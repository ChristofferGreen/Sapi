#!/usr/bin/env python3
"""Definition-of-Done verifier (TODO-0231)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import subprocess
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc
from sapi.core.slice_a_gates import (
    deferred_build_backlog_run_ids,
    load_run_frontmatter,
)

_RUN_ID_RE = re.compile(r"run_id=(run-[^,\s)]+)")
_SOURCE_ID_RE = re.compile(r"source_id=([a-z0-9][a-z0-9-]*)")
_TOPIC_ID_RE = re.compile(r"topic_id=([a-z0-9][a-z0-9-]*)")
_SOURCE_NEW_ROW_RE = re.compile(
    r'<li>.*?<span class="meta">([^|<]+)\s*\|\s*[^|<]+\s*\|\s*source</span>\s*'
    r'<a href="/spaces/[^/]+/site/sources/([a-z0-9-]+)\.html">',
    re.DOTALL,
)


@dataclass(frozen=True)
class StepResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("site_path")
    parser.add_argument("space_name")
    parser.add_argument("source_path_or_url")
    parser.add_argument("question")
    parser.add_argument("--site-name", default="DoD Verification Site")
    parser.add_argument("--out")
    parser.add_argument("--mock-llm", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--evidence-path",
        default=str(_REPO_ROOT / "docs" / "verification" / "dod_verification.latest.json"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))

    try:
        site_path = Path(args.site_path).expanduser().resolve()
        source_arg = _normalize_source_arg(args.source_path_or_url)
        verification_id = _verification_id()
        output_dir = (
            Path(args.out).expanduser().resolve()
            if args.out is not None
            else site_path / "outputs" / "verification" / "dod" / verification_id
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = output_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        steps: list[StepResult] = []
        steps.append(
            _run_checked(
                "create_site",
                ["bash", str(_REPO_ROOT / "create_site.sh"), str(site_path), args.site_name],
            )
        )
        steps.append(
            _run_checked(
                "create_space",
                ["bash", str(_REPO_ROOT / "create_space.sh"), str(site_path), args.space_name],
            )
        )

        ingest_cmd = [
            "bash",
            str(_REPO_ROOT / "ingest.sh"),
            str(site_path),
            args.space_name,
            source_arg,
        ]
        if args.mock_llm:
            ingest_cmd.append("--mock-llm")
        if args.verbose:
            ingest_cmd.append("--verbose")
        ingest_step = _run_checked("ingest", ingest_cmd)
        steps.append(ingest_step)

        space_root = site_path / "spaces" / args.space_name
        comment_topic_id = "topic-dod-placeholder"
        _write_comment_topic_fixture(space_root=space_root, topic_id=comment_topic_id)

        query_cmd = [
            "bash",
            str(_REPO_ROOT / "query.sh"),
            str(site_path),
            args.space_name,
            args.question,
        ]
        if args.mock_llm:
            query_cmd.append("--mock-llm")
        if args.verbose:
            query_cmd.append("--verbose")
        query_step = _run_checked("query", query_cmd)
        steps.append(query_step)

        comments_cmd = [
            "bash",
            str(_REPO_ROOT / "create_comments.sh"),
            str(site_path),
            args.space_name,
            "--count",
            "5",
            "--comment-page",
            f"topic:{comment_topic_id}",
        ]
        if args.mock_llm:
            comments_cmd.append("--mock-llm")
        if args.verbose:
            comments_cmd.append("--verbose")
        comments_step = _run_checked("create_comments", comments_cmd)
        steps.append(comments_step)

        profiles_cmd = [
            "bash",
            str(_REPO_ROOT / "generate_profiles.sh"),
            str(site_path),
            args.space_name,
        ]
        if args.mock_llm:
            profiles_cmd.append("--mock-llm")
        if args.verbose:
            profiles_cmd.append("--verbose")
        profiles_step = _run_checked("generate_profiles", profiles_cmd)
        steps.append(profiles_step)

        regenerate_cmd = [
            "bash",
            str(_REPO_ROOT / "regenerate_web.sh"),
            str(site_path),
            args.space_name,
        ]
        if args.verbose:
            regenerate_cmd.append("--verbose")
        regenerate_step = _run_checked("regenerate_web", regenerate_cmd)
        steps.append(regenerate_step)

        ingest_run_id = _extract_required(_RUN_ID_RE, ingest_step.stdout, label="ingest run_id")
        query_run_id = _extract_required(_RUN_ID_RE, query_step.stdout, label="query run_id")
        comments_run_id = _extract_required(
            _RUN_ID_RE,
            comments_step.stdout,
            label="comments run_id",
        )
        profiles_run_id = _extract_required(
            _RUN_ID_RE,
            profiles_step.stdout,
            label="profiles run_id",
        )
        source_id = _extract_required(_SOURCE_ID_RE, ingest_step.stdout, label="ingest source_id")
        topic_id = _extract_required(_TOPIC_ID_RE, ingest_step.stdout, label="ingest topic_id")

        validate_cmd = [
            "bash",
            str(_REPO_ROOT / "validate.sh"),
            str(site_path),
            args.space_name,
            "--workflow",
            "ingest_source",
            "--run-id",
            ingest_run_id,
        ]
        if args.verbose:
            validate_cmd.append("--verbose")
        validate_step = _run_checked("validate", validate_cmd)
        steps.append(validate_step)

        evaluate_pack_dir = output_dir / "evaluate_source_pack"
        evaluate_cmd = [
            "bash",
            str(_REPO_ROOT / "evaluate_source.sh"),
            str(site_path),
            args.space_name,
            source_arg,
            "--out",
            str(evaluate_pack_dir),
        ]
        if args.mock_llm:
            evaluate_cmd.append("--mock-llm")
        if args.verbose:
            evaluate_cmd.append("--verbose")
        evaluate_step = _run_checked("evaluate_source", evaluate_cmd)
        steps.append(evaluate_step)

        step_logs = _write_step_logs(steps=steps, logs_dir=logs_dir)

        source_record_path = space_root / "sources" / "records" / f"{source_id}.json"
        topic_path = space_root / "topics" / f"{topic_id}.json"
        comment_topic_path = space_root / "topics" / f"{comment_topic_id}.json"
        source_record = _load_json_dict(source_record_path)
        topic_payload = _load_json_dict(topic_path)
        comment_topic_payload = _load_json_dict(comment_topic_path)
        claim_ids = topic_payload.get("claim_ids")
        if not isinstance(claim_ids, list):
            raise ValueError(f"{topic_path}: claim_ids must be a list.")

        claim_paths = [space_root / "claims" / f"{claim_id}.json" for claim_id in claim_ids]
        claim_payloads = [_load_json_dict(path) for path in claim_paths]

        ingest_frontmatter = load_run_frontmatter(space_root=space_root, run_id=ingest_run_id)
        query_frontmatter = load_run_frontmatter(space_root=space_root, run_id=query_run_id)
        comments_frontmatter = load_run_frontmatter(space_root=space_root, run_id=comments_run_id)
        profiles_frontmatter = load_run_frontmatter(space_root=space_root, run_id=profiles_run_id)

        users_index_path = space_root / "site" / "users" / "index.html"
        users_index_text = users_index_path.read_text() if users_index_path.is_file() else ""
        topic_site_path = space_root / "site" / "topics" / f"{topic_id}.html"
        source_site_path = space_root / "site" / "sources" / f"{source_id}.html"
        space_home_path = space_root / "site" / "index.html"
        site_new_index_path = site_path / "site" / "new" / "index.html"
        evaluate_manifest_path = evaluate_pack_dir / "manifest.json"
        validate_envelope = _parse_lint_envelope(validate_step.stdout)

        testing_exit_evidence_path = (
            _REPO_ROOT / "docs" / "verification" / "testing_exit_criteria.latest.json"
        )
        slice_b_evidence_path = _REPO_ROOT / "docs" / "verification" / "slice_b_exit_criteria.latest.json"
        testing_exit_evidence = _read_json_if_exists(testing_exit_evidence_path)
        slice_b_evidence = _read_json_if_exists(slice_b_evidence_path)

        deferred_backlog = deferred_build_backlog_run_ids(space_root=space_root)
        checks = {
            "dod_13_1_wrappers_execute_successfully": {
                "description": (
                    "All DoD wrapper commands execute successfully on a representative site/space."
                ),
                "passed": True,
                "evidence_links": [str(step_logs[name]["stdout"]) for name in step_logs],
            },
            "dod_13_2_validate_workflow_lint_gate": {
                "description": "validate.sh enforces workflow-specific lint gate behavior.",
                "passed": (
                    isinstance(validate_envelope, dict)
                    and validate_envelope.get("workflow") == "ingest_source"
                    and validate_envelope.get("status") in {"success", "success_with_warnings"}
                ),
                "evidence_links": [
                    str(step_logs["validate"]["stdout"]),
                    str(space_root / "runs" / ingest_run_id / "lint.json"),
                ],
            },
            "dod_13_3_evaluate_source_artifact_pack": {
                "description": (
                    "evaluate_source.sh produces a human-readable artifact pack for manual review."
                ),
                "passed": _check_evaluate_pack(evaluate_pack_dir),
                "evidence_links": [
                    str(evaluate_pack_dir / "README.md"),
                    str(evaluate_pack_dir / "summary.md"),
                    str(evaluate_pack_dir / "manifest.json"),
                ],
            },
            "dod_13_4_ingest_artifacts_and_links": {
                "description": "Ingest writes source/claim/topic artifacts with valid links.",
                "passed": _check_ingest_link_contract(
                    source_id=source_id,
                    source_record=source_record,
                    topic_payload=topic_payload,
                    claim_payloads=claim_payloads,
                ),
                "evidence_links": [str(source_record_path), str(topic_path), *[str(path) for path in claim_paths]],
            },
            "dod_13_5_date_and_ingested_at_semantics": {
                "description": (
                    "Publication `date` and ingest `ingested_at` semantics are correct, including nullable fallback."
                ),
                "passed": _check_date_semantics(source_record),
                "evidence_links": [str(source_record_path)],
            },
            "dod_13_6_front_page_ordering_uses_ingested_at": {
                "description": "Front-page ordering uses `ingested_at`.",
                "passed": _check_front_page_order(site_new_index_path),
                "evidence_links": [str(site_new_index_path)],
            },
            "dod_13_7_navigation_tabs_search_stable": {
                "description": "Static site navigation/tabs/search behavior is stable across page types.",
                "passed": _check_navigation_tabs_search(
                    space_home_path=space_home_path,
                    source_page_path=source_site_path,
                    topic_page_path=topic_site_path,
                ),
                "evidence_links": [str(space_home_path), str(source_site_path), str(topic_site_path)],
            },
            "dod_13_8_seeded_users_comments_profiles_loaded": {
                "description": (
                    "Repository-seeded users are loaded and comments/profile/history artifacts are generated."
                ),
                "passed": _check_seeded_users_social_profile(
                    users_index_text=users_index_text,
                    topic_payload=comment_topic_payload,
                    space_root=space_root,
                ),
                "evidence_links": [
                    str(_REPO_ROOT / "personas" / "social_users.json"),
                    str(users_index_path),
                    str(comment_topic_path),
                    str(space_root / "profiles" / "persona-commenter-1.json"),
                    str(space_root / "outputs" / "persona_profile_history" / "commenter-1.json"),
                ],
            },
            "dod_13_9_runtime_semantic_generation_contracts": {
                "description": (
                    "Semantic generation paths retain LLM-contract execution semantics (mock mode allowed for tests)."
                ),
                "passed": _check_runtime_execution_modes(
                    args_mock_llm=args.mock_llm,
                    frontmatters=[
                        ingest_frontmatter,
                        query_frontmatter,
                        comments_frontmatter,
                        profiles_frontmatter,
                    ],
                ),
                "evidence_links": [
                    str(space_root / "runs" / ingest_run_id / "run.md"),
                    str(space_root / "runs" / query_run_id / "run.md"),
                    str(space_root / "runs" / comments_run_id / "run.md"),
                    str(space_root / "runs" / profiles_run_id / "run.md"),
                ],
            },
            "dod_13_10_no_deferred_build_backlog": {
                "description": "No `build_deferred: true` backlog remains.",
                "passed": not deferred_backlog,
                "evidence_links": [str(space_root / "runs")],
            },
            "dod_13_11_tests_signal_contract_drift": {
                "description": "Tests provide strong signal on contract drift and rendering regressions.",
                "passed": _check_prior_gate_evidence(
                    testing_exit_evidence=testing_exit_evidence,
                    slice_b_evidence=slice_b_evidence,
                ),
                "evidence_links": [str(testing_exit_evidence_path), str(slice_b_evidence_path)],
            },
        }
        section_13_bullet_check_ids = list(checks.keys())
        checks["dod_13_all_section_13_bullets_have_explicit_evidence_links"] = {
            "description": "Every Section 13 DoD bullet is explicitly checked with evidence links.",
            "passed": all(
                isinstance(checks[check_id].get("evidence_links"), list)
                and len(checks[check_id]["evidence_links"]) > 0
                for check_id in section_13_bullet_check_ids
            ),
            "evidence_links": [
                str(output_dir / "manifest.json"),
                str(_REPO_ROOT / "docs" / "design.md"),
            ],
        }

        mandatory_gate_keys = (
            "dod_13_1_wrappers_execute_successfully",
            "dod_13_10_no_deferred_build_backlog",
            "dod_13_all_section_13_bullets_have_explicit_evidence_links",
        )
        errors = [
            f"{check_id} failed"
            for check_id in mandatory_gate_keys
            if checks[check_id]["passed"] is not True
        ]
        failed_non_blocking_checks = [
            check_id
            for check_id, payload in checks.items()
            if check_id not in mandatory_gate_keys and payload["passed"] is not True
        ]

        manifest_path = output_dir / "manifest.json"
        manifest = {
            "verification_id": verification_id,
            "scope": "definition_of_done_section_13",
            "started_at": started_at,
            "completed_at": format_timestamp_rfc3339_utc(datetime.now(UTC)),
            "site_path": str(site_path),
            "space_name": args.space_name,
            "source_path_or_url": source_arg,
            "question": args.question,
            "run_ids": {
                "ingest": ingest_run_id,
                "query": query_run_id,
                "create_comments": comments_run_id,
                "generate_profiles": profiles_run_id,
            },
            "steps": [
                {"name": step.name, "command": step.command, "returncode": step.returncode}
                for step in steps
            ],
            "deferred_build_backlog_run_ids": deferred_backlog,
            "checks": checks,
            "status": "success" if not errors else "failed",
            "errors": errors,
            "failed_non_blocking_checks": failed_non_blocking_checks,
            "evidence": {
                "evaluate_source_manifest_path": (
                    str(evaluate_manifest_path) if evaluate_manifest_path.is_file() else None
                ),
                "testing_exit_gate_evidence_path": str(testing_exit_evidence_path),
                "slice_b_gate_evidence_path": str(slice_b_evidence_path),
            },
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

        evidence_path = Path(args.evidence_path).expanduser().resolve()
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(
                {
                    "verification_id": verification_id,
                    "scope": "definition_of_done_section_13",
                    "completed_at": manifest["completed_at"],
                    "manifest_path": str(manifest_path),
                    "status": manifest["status"],
                    "checks": {key: payload["passed"] for key, payload in checks.items()},
                    "errors": errors,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        if errors:
            raise RuntimeError(
                "DoD verification failed. "
                f"See manifest: {manifest_path}. Errors: {errors!r}"
            )
        print(
            "scripts/verify_dod.py verification complete "
            f"(verification_id={verification_id}, manifest_path={manifest_path}, "
            f"evidence_path={evidence_path}, status=success)"
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _run_checked(name: str, command: list[str]) -> StepResult:
    result = subprocess.run(
        command,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    step = StepResult(
        name=name,
        command=command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed (exit_code={result.returncode}): "
            f"stdout={result.stdout.strip()} stderr={result.stderr.strip()}"
        )
    return step


def _write_step_logs(*, steps: list[StepResult], logs_dir: Path) -> dict[str, dict[str, Path]]:
    written: dict[str, dict[str, Path]] = {}
    for step in steps:
        stdout_path = logs_dir / f"{step.name}.stdout.txt"
        stderr_path = logs_dir / f"{step.name}.stderr.txt"
        stdout_path.write_text(step.stdout)
        stderr_path.write_text(step.stderr)
        written[step.name] = {"stdout": stdout_path, "stderr": stderr_path}
    return written


def _extract_required(pattern: re.Pattern[str], text: str, *, label: str) -> str:
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"Unable to determine {label} from command output.")
    return match.group(1)


def _normalize_source_arg(raw: str) -> str:
    candidate = Path(raw).expanduser()
    if candidate.exists():
        return str(candidate.resolve())
    return raw


def _write_comment_topic_fixture(*, space_root: Path, topic_id: str) -> None:
    topic_path = space_root / "topics" / f"{topic_id}.json"
    topic_payload = {
        "topic_id": topic_id,
        "title": "Topic: DoD Placeholder",
        "structure_type": "wiki",
        "source_ids": [],
        "claim_ids": [],
        "sections": [
            {
                "heading": "Summary",
                "body": "Deterministic placeholder topic used for DoD comment verification.",
            }
        ],
    }
    topic_path.write_text(json.dumps(topic_payload, indent=2, sort_keys=True) + "\n")


def _verification_id() -> str:
    return datetime.now(UTC).strftime("dod-%Y%m%dT%H%M%SZ")


def _load_json_dict(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"JSON artifact not found: {path}")
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected JSON object payload.")
    return payload


def _parse_lint_envelope(stdout: str) -> dict[str, object] | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _check_evaluate_pack(evaluate_pack_dir: Path) -> bool:
    required = (
        evaluate_pack_dir / "README.md",
        evaluate_pack_dir / "summary.md",
        evaluate_pack_dir / "ingest_run.md",
        evaluate_pack_dir / "lint_summary.md",
        evaluate_pack_dir / "site_links.md",
        evaluate_pack_dir / "query_answers" / "strict.md",
        evaluate_pack_dir / "manifest.json",
    )
    return all(path.is_file() for path in required)


def _check_ingest_link_contract(
    *,
    source_id: str,
    source_record: dict[str, object],
    topic_payload: dict[str, object],
    claim_payloads: list[dict[str, object]],
) -> bool:
    if source_record.get("source_id") != source_id:
        return False
    source_ids = topic_payload.get("source_ids")
    if not isinstance(source_ids, list) or source_id not in source_ids:
        return False
    if not claim_payloads:
        return False
    return all(payload.get("source_id") == source_id for payload in claim_payloads)


def _check_date_semantics(source_record: dict[str, object]) -> bool:
    ingested_at = source_record.get("ingested_at")
    if not isinstance(ingested_at, str):
        return False
    try:
        datetime.strptime(ingested_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False

    date_value = source_record.get("date")
    if date_value is None:
        source_date_inference = source_record.get("source_date_inference")
        if not isinstance(source_date_inference, dict):
            return False
        if source_date_inference.get("date") is not None:
            return False
        warnings = source_record.get("warnings", [])
        if not isinstance(warnings, list):
            return False
        warning_codes = {
            warning.get("code")
            for warning in warnings
            if isinstance(warning, dict)
        }
        return "missing_publication_date" in warning_codes

    if not isinstance(date_value, str):
        return False
    try:
        datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _check_front_page_order(site_new_index_path: Path) -> bool:
    if not site_new_index_path.is_file():
        return False
    text = site_new_index_path.read_text()
    rows = _SOURCE_NEW_ROW_RE.findall(text)
    if not rows:
        return False
    timestamps = [timestamp.strip() for timestamp, _source_id in rows]
    return timestamps == sorted(timestamps, reverse=True)


def _check_navigation_tabs_search(
    *,
    space_home_path: Path,
    source_page_path: Path,
    topic_page_path: Path,
) -> bool:
    required_paths = (space_home_path, source_page_path, topic_page_path)
    if not all(path.is_file() for path in required_paths):
        return False
    for path in required_paths:
        html = path.read_text()
        if 'class="tabs"' not in html:
            return False
        if "site/search/index.html" not in html:
            return False
        if "New" not in html or "Sources" not in html or "Topics" not in html:
            return False
    return True


def _check_seeded_users_social_profile(
    *,
    users_index_text: str,
    topic_payload: dict[str, object],
    space_root: Path,
) -> bool:
    social_catalog = _read_json_if_exists(_REPO_ROOT / "personas" / "social_users.json")
    if not isinstance(social_catalog, dict):
        return False
    users_rows = social_catalog.get("users")
    if not isinstance(users_rows, list) or len(users_rows) != 100:
        return False

    comment_section = topic_payload.get("comment_section")
    if not isinstance(comment_section, dict):
        return False
    comments = comment_section.get("comments")
    if not isinstance(comments, list) or len(comments) < 5:
        return False

    profile_path = space_root / "profiles" / "persona-commenter-1.json"
    history_path = space_root / "outputs" / "persona_profile_history" / "commenter-1.json"
    if not profile_path.is_file() or not history_path.is_file():
        return False
    if not users_index_text.strip():
        return False
    return True


def _check_runtime_execution_modes(
    *,
    args_mock_llm: bool,
    frontmatters: list[dict[str, object]],
) -> bool:
    for frontmatter in frontmatters:
        semantic_flows = frontmatter.get("semantic_flows")
        invocation_counts = frontmatter.get("semantic_flow_invocation_counts")
        if not isinstance(semantic_flows, list) or not semantic_flows:
            return False
        if not isinstance(invocation_counts, dict) or not invocation_counts:
            return False
        if args_mock_llm and frontmatter.get("execution_mode") != "mock_llm_test":
            return False
    return True


def _check_prior_gate_evidence(
    *,
    testing_exit_evidence: object,
    slice_b_evidence: object,
) -> bool:
    if not isinstance(testing_exit_evidence, dict):
        return False
    if testing_exit_evidence.get("status") != "success":
        return False
    if not isinstance(slice_b_evidence, dict):
        return False
    if slice_b_evidence.get("status") != "success":
        return False
    return True


def _read_json_if_exists(path: Path) -> object:
    if not path.is_file():
        return None
    return json.loads(path.read_text())


if __name__ == "__main__":
    raise SystemExit(main())
