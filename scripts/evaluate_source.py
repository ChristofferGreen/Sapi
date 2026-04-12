#!/usr/bin/env python3
"""User-facing source evaluation harness (TODO-0273)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc
from sapi.core.registry import (
    resolve_registry_path,
    resolve_site_path_from_registry,
    resolve_space_root,
)

_RUN_ID_RE = re.compile(r"run_id=(run-[^,\s)]+)")
_FIELD_RE_CACHE: dict[str, re.Pattern[str]] = {}


@dataclass(frozen=True)
class StepResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("source_path_or_url")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--out")
    parser.add_argument("--comments", type=int)
    parser.add_argument("--comment-user", action="append", default=[])
    parser.add_argument("--comment-page", action="append", default=[])
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--mock-llm", action="store_true", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        _validate_comments_arg(args.comments)
        registry_path = resolve_registry_path(args.registry_path)
        site_path = resolve_site_path_from_registry(registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))

        existing_run_ids = _list_run_ids(space_root)
        ingest_result = _run_checked(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "ingest_source.py"),
                args.space_name,
                args.source_path_or_url,
                "--registry-path",
                str(registry_path),
                *(["--mock-llm"] if args.mock_llm else []),
                *(["--verbose"] if args.verbose else []),
            ],
            step_name="ingest_source",
        )

        ingest_run_id = _extract_run_id(ingest_result.stdout)
        if ingest_run_id is None:
            new_run_ids = sorted(_list_run_ids(space_root) - existing_run_ids)
            if len(new_run_ids) != 1:
                raise RuntimeError("Unable to resolve ingest run_id from output or run directory diff.")
            ingest_run_id = new_run_ids[0]

        lint_result = _run_checked(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "lint.py"),
                args.space_name,
                "--registry-path",
                str(registry_path),
                "--workflow",
                "ingest_source",
                "--run-id",
                ingest_run_id,
                *(["--verbose"] if args.verbose else []),
            ],
            step_name="validate_lint",
        )
        lint_envelope = _parse_lint_envelope(lint_result.stdout)

        strict_question = (
            f"Provide a strict summary for source `{args.source_path_or_url}` using only canonical evidence."
        )
        query_result = _run_checked(
            [
                sys.executable,
                str(_REPO_ROOT / "scripts" / "query.py"),
                args.space_name,
                strict_question,
                "--registry-path",
                str(registry_path),
                *(["--mock-llm"] if args.mock_llm else []),
                *(["--verbose"] if args.verbose else []),
            ],
            step_name="query_strict",
        )

        comments_result: StepResult | None = None
        if args.comments is not None and args.comments > 0:
            comments_result = _run_checked(
                [
                    sys.executable,
                    str(_REPO_ROOT / "scripts" / "create_comments.py"),
                    args.space_name,
                    "--registry-path",
                    str(registry_path),
                    "--count",
                    str(args.comments),
                    *[item for value in args.comment_user for item in ("--comment-user", value)],
                    *[item for value in args.comment_page for item in ("--comment-page", value)],
                    *(["--mock-llm"] if args.mock_llm else []),
                    *(["--verbose"] if args.verbose else []),
                ],
                step_name="create_comments",
            )

        evaluation_id = _make_evaluation_id(ingest_run_id)
        output_dir = (
            Path(args.out).expanduser().resolve()
            if args.out is not None
            else space_root / "outputs" / "evaluations" / evaluation_id
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "query_answers").mkdir(parents=True, exist_ok=True)

        run_dir = space_root / "runs" / ingest_run_id
        run_record_path = run_dir / "run.md"
        lint_json_path = run_dir / "lint.json"
        build_manifest_path = _resolve_build_manifest_path(site_path, ingest_result.stdout)
        build_manifest = _read_json_if_exists(build_manifest_path)

        readme_path = output_dir / "README.md"
        summary_path = output_dir / "summary.md"
        ingest_run_path = output_dir / "ingest_run.md"
        lint_summary_path = output_dir / "lint_summary.md"
        site_links_path = output_dir / "site_links.md"
        strict_query_path = output_dir / "query_answers" / "strict.md"

        readme_path.write_text(
            _render_readme(
                started_at=started_at,
                completed_at=format_timestamp_rfc3339_utc(datetime.now(UTC)),
                space_name=args.space_name,
                source_path_or_url=args.source_path_or_url,
                registry_path=registry_path,
                ingest_result=ingest_result,
                lint_result=lint_result,
                query_result=query_result,
                comments_result=comments_result,
                comments_requested=args.comments,
            )
        )
        summary_path.write_text(
            _render_summary(
                ingest_result=ingest_result,
                lint_envelope=lint_envelope,
                query_result=query_result,
                comments_result=comments_result,
                comments_requested=args.comments,
            )
        )
        ingest_run_path.write_text(
            _render_ingest_run(
                ingest_run_id=ingest_run_id,
                run_record_path=run_record_path,
                ingest_stdout=ingest_result.stdout,
            )
        )
        lint_summary_path.write_text(
            _render_lint_summary(
                lint_envelope=lint_envelope,
                lint_json_path=lint_json_path,
            )
        )
        strict_query_path.write_text(
            _render_strict_query_answer(
                question=strict_question,
                query_result=query_result,
            )
        )
        site_links_path.write_text(
            _render_site_links(
                site_path=site_path,
                build_manifest=build_manifest,
            )
        )

        comments_review_path: Path | None = None
        if comments_result is not None and args.comments is not None:
            comments_review_path = output_dir / "comments_review.md"
            comments_review_path.write_text(
                _render_comments_review(
                    requested_count=args.comments,
                    comment_users=args.comment_user,
                    comment_pages=args.comment_page,
                    comments_result=comments_result,
                )
            )

        copied_supporting_paths: list[Path] = []
        if lint_json_path.is_file():
            copied_lint_path = output_dir / "lint.json"
            shutil.copy2(lint_json_path, copied_lint_path)
            copied_supporting_paths.append(copied_lint_path)

        manifest_path = output_dir / "manifest.json"
        artifact_paths = [
            readme_path,
            summary_path,
            ingest_run_path,
            lint_summary_path,
            site_links_path,
            strict_query_path,
        ]
        if comments_review_path is not None:
            artifact_paths.append(comments_review_path)
        manifest = _build_manifest(
            evaluation_id=evaluation_id,
            registry_path=registry_path,
            site_path=site_path,
            space_root=space_root,
            output_dir=output_dir,
            source_path_or_url=args.source_path_or_url,
            space_name=args.space_name,
            ingest_run_id=ingest_run_id,
            lint_envelope=lint_envelope,
            artifact_paths=artifact_paths,
            supporting_paths=copied_supporting_paths,
            build_manifest_path=build_manifest_path if build_manifest_path.is_file() else None,
            comments_requested=args.comments,
            comments_result=comments_result,
        )
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

        print(
            "scripts/evaluate_source.py evaluation artifact pack ready "
            f"(evaluation_id={evaluation_id}, output_dir={output_dir}, ingest_run_id={ingest_run_id}, "
            f"manifest_path={manifest_path})"
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _validate_comments_arg(comments: int | None) -> None:
    if comments is None:
        return
    if comments <= 0:
        raise ValueError("--comments must be a positive integer when provided.")


def _run_checked(command: list[str], *, step_name: str) -> StepResult:
    result = subprocess.run(
        command,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    step_result = StepResult(
        command=command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    if step_result.returncode != 0:
        raise RuntimeError(
            f"{step_name} failed (exit_code={step_result.returncode}): "
            f"stdout={step_result.stdout.strip()} stderr={step_result.stderr.strip()}"
        )
    return step_result


def _list_run_ids(space_root: Path) -> set[str]:
    runs_root = space_root / "runs"
    if not runs_root.is_dir():
        return set()
    return {path.name for path in runs_root.iterdir() if path.is_dir() and path.name.startswith("run-")}


def _extract_run_id(stdout: str) -> str | None:
    match = _RUN_ID_RE.search(stdout)
    if match is None:
        return None
    return match.group(1)


def _extract_field(stdout: str, key: str) -> str | None:
    pattern = _FIELD_RE_CACHE.get(key)
    if pattern is None:
        pattern = re.compile(rf"{re.escape(key)}=([^,\n)]+)")
        _FIELD_RE_CACHE[key] = pattern
    match = pattern.search(stdout)
    if match is None:
        return None
    return match.group(1).strip()


def _parse_lint_envelope(stdout: str) -> dict[str, object]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("validate_lint produced no output.")
    envelope_raw = lines[-1]
    envelope = json.loads(envelope_raw)
    if not isinstance(envelope, dict):
        raise ValueError("validate_lint output must decode to a JSON object.")
    return envelope


def _resolve_build_manifest_path(site_path: Path, ingest_stdout: str) -> Path:
    manifest_field = _extract_field(ingest_stdout, "build_manifest_path")
    if manifest_field is not None:
        return Path(manifest_field)
    return site_path / "outputs" / "build_site" / "manifest.json"


def _read_json_if_exists(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        return None
    return payload


def _make_evaluation_id(ingest_run_id: str) -> str:
    if ingest_run_id.startswith("run-"):
        return f"evaluation-{ingest_run_id[4:]}"
    return f"evaluation-{ingest_run_id}"


def _render_readme(
    *,
    started_at: str,
    completed_at: str,
    space_name: str,
    source_path_or_url: str,
    registry_path: Path,
    ingest_result: StepResult,
    lint_result: StepResult,
    query_result: StepResult,
    comments_result: StepResult | None,
    comments_requested: int | None,
) -> str:
    lines = [
        "# Source Evaluation Artifact Pack",
        "",
        "## Execution Summary",
        f"- started_at: `{started_at}`",
        f"- completed_at: `{completed_at}`",
        f"- space_name: `{space_name}`",
        f"- source_path_or_url: `{source_path_or_url}`",
        f"- registry_path: `{registry_path}`",
        "",
        "## Executed Steps",
        f"- ingest_source: `{' '.join(ingest_result.command)}`",
        f"- validate_lint: `{' '.join(lint_result.command)}`",
        f"- query_strict: `{' '.join(query_result.command)}`",
    ]
    if comments_result is not None:
        lines.append(f"- create_comments: `{' '.join(comments_result.command)}`")
    elif comments_requested is not None:
        lines.append("- create_comments: not executed (requested count <= 0)")
    else:
        lines.append("- create_comments: not requested")
    lines.extend(
        [
            "",
            "## Command Outputs",
            "### ingest_source stdout",
            "```text",
            ingest_result.stdout.strip(),
            "```",
        ]
    )
    if ingest_result.stderr.strip():
        lines.extend(["### ingest_source stderr", "```text", ingest_result.stderr.strip(), "```"])
    return "\n".join(lines) + "\n"


def _render_summary(
    *,
    ingest_result: StepResult,
    lint_envelope: dict[str, object],
    query_result: StepResult,
    comments_result: StepResult | None,
    comments_requested: int | None,
) -> str:
    lint_block = lint_envelope.get("lint")
    lint_error_count = "unknown"
    lint_warning_count = "unknown"
    lint_info_count = "unknown"
    if isinstance(lint_block, dict):
        lint_error_count = lint_block.get("error_count", "unknown")
        lint_warning_count = lint_block.get("warning_count", "unknown")
        lint_info_count = lint_block.get("info_count", "unknown")

    comments_status = "skipped"
    if comments_requested is not None and comments_result is not None:
        comments_status = "success"
    elif comments_requested is not None:
        comments_status = "invalid_request"

    lines = [
        "# Evaluation Summary",
        "",
        "## Checklist",
        f"- ingest_source completed: {'yes' if ingest_result.returncode == 0 else 'no'}",
        f"- validate_lint status: `{lint_envelope.get('status', 'unknown')}`",
        f"- lint totals: errors={lint_error_count}, warnings={lint_warning_count}, info={lint_info_count}",
        f"- strict query step completed: {'yes' if query_result.returncode == 0 else 'no'}",
        f"- comments step status: `{comments_status}`",
        "",
        "## Next Actions",
        "- Review `ingest_run.md` for canonical run references.",
        "- Review `query_answers/strict.md` for strict-mode answer output.",
        "- Review `site_links.md` for deterministic page outputs to inspect manually.",
    ]
    return "\n".join(lines) + "\n"


def _render_ingest_run(*, ingest_run_id: str, run_record_path: Path, ingest_stdout: str) -> str:
    ingest_status = _extract_field(ingest_stdout, "status") or "unknown"
    source_id = _extract_field(ingest_stdout, "source_id") or "unknown"
    topic_id = _extract_field(ingest_stdout, "topic_id") or "unknown"
    run_record_excerpt = ""
    if run_record_path.is_file():
        run_record_excerpt = "\n".join(run_record_path.read_text().splitlines()[:25]).strip()
    lines = [
        "# Ingest Run",
        "",
        f"- ingest_run_id: `{ingest_run_id}`",
        f"- status: `{ingest_status}`",
        f"- source_id: `{source_id}`",
        f"- topic_id: `{topic_id}`",
        f"- run_record_path: `{run_record_path}`",
    ]
    if run_record_excerpt:
        lines.extend(
            [
                "",
                "## Run Record Excerpt",
                "```markdown",
                run_record_excerpt,
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def _render_lint_summary(*, lint_envelope: dict[str, object], lint_json_path: Path) -> str:
    lint_block = lint_envelope.get("lint")
    lint_error_count = "unknown"
    lint_warning_count = "unknown"
    lint_info_count = "unknown"
    if isinstance(lint_block, dict):
        lint_error_count = lint_block.get("error_count", "unknown")
        lint_warning_count = lint_block.get("warning_count", "unknown")
        lint_info_count = lint_block.get("info_count", "unknown")
    lines = [
        "# Lint Summary",
        "",
        f"- workflow: `{lint_envelope.get('workflow', 'unknown')}`",
        f"- status: `{lint_envelope.get('status', 'unknown')}`",
        f"- run_id: `{lint_envelope.get('run_id', 'unknown')}`",
        f"- warning_threshold: `{lint_envelope.get('warning_threshold', 'unknown')}`",
        f"- error_count: `{lint_error_count}`",
        f"- warning_count: `{lint_warning_count}`",
        f"- info_count: `{lint_info_count}`",
        f"- lint_json_path: `{lint_json_path}`",
    ]
    return "\n".join(lines) + "\n"


def _render_strict_query_answer(*, question: str, query_result: StepResult) -> str:
    lines = [
        "# Strict Query Answer",
        "",
        "- mode: `strict`",
        f"- question: `{question}`",
        "",
        "## Query Command Output",
        "```text",
        query_result.stdout.strip(),
        "```",
    ]
    if query_result.stderr.strip():
        lines.extend(["## Query stderr", "```text", query_result.stderr.strip(), "```"])
    return "\n".join(lines) + "\n"


def _render_site_links(*, site_path: Path, build_manifest: dict[str, object] | None) -> str:
    lines = [
        "# Site Links",
        "",
        f"- site_path: `{site_path}`",
    ]
    if build_manifest is None:
        lines.extend(["", "Build manifest unavailable."])
        return "\n".join(lines) + "\n"

    site_new_index_path = build_manifest.get("site_new_index_path")
    if isinstance(site_new_index_path, str):
        lines.append(f"- site_new_index_path: `{site_new_index_path}`")

    lines.extend(["", "## Generated Pages"])
    generated: list[str] = []
    space_builds = build_manifest.get("space_builds")
    if isinstance(space_builds, list):
        for row in space_builds:
            if not isinstance(row, dict):
                continue
            generated_files = row.get("generated_files")
            if isinstance(generated_files, list):
                for path in generated_files:
                    if isinstance(path, str):
                        generated.append(path)

    if not generated:
        lines.append("- (none)")
    else:
        for path in sorted(generated)[:40]:
            lines.append(f"- `{path}`")
    return "\n".join(lines) + "\n"


def _render_comments_review(
    *,
    requested_count: int,
    comment_users: list[str],
    comment_pages: list[str],
    comments_result: StepResult,
) -> str:
    page_targets = sorted(set(comment_pages)) if comment_pages else ["(default topic targets)"]
    user_targets = sorted(set(comment_users)) if comment_users else ["(default persona mix)"]
    page_counts = _distribute_requested_count(requested_count, page_targets)
    user_counts = _distribute_requested_count(requested_count, user_targets)

    lines = [
        "# Comments Review",
        "",
        f"- requested_comment_count: `{requested_count}`",
        "",
        "## Per-Page Requested Counts",
        "| page_ref | requested_count |",
        "| --- | --- |",
    ]
    for key, count in page_counts:
        lines.append(f"| `{key}` | {count} |")

    lines.extend(
        [
            "",
            "## Per-User Requested Counts",
            "| persona_id | requested_count |",
            "| --- | --- |",
        ]
    )
    for key, count in user_counts:
        lines.append(f"| `{key}` | {count} |")

    representative_excerpt = comments_result.stdout.strip() or "(no stdout emitted)"
    lines.extend(
        [
            "",
            "## Representative Thread Excerpt",
            "```text",
            representative_excerpt,
            "```",
        ]
    )
    if comments_result.stderr.strip():
        lines.extend(["## comments stderr", "```text", comments_result.stderr.strip(), "```"])
    return "\n".join(lines) + "\n"


def _distribute_requested_count(total: int, keys: list[str]) -> list[tuple[str, int]]:
    if not keys:
        return []
    base, remainder = divmod(total, len(keys))
    distribution: list[tuple[str, int]] = []
    for idx, key in enumerate(keys):
        distribution.append((key, base + (1 if idx < remainder else 0)))
    return distribution


def _build_manifest(
    *,
    evaluation_id: str,
    registry_path: Path,
    site_path: Path,
    space_root: Path,
    output_dir: Path,
    source_path_or_url: str,
    space_name: str,
    ingest_run_id: str,
    lint_envelope: dict[str, object],
    artifact_paths: list[Path],
    supporting_paths: list[Path],
    build_manifest_path: Path | None,
    comments_requested: int | None,
    comments_result: StepResult | None,
) -> dict[str, object]:
    markdown_artifacts = sorted(str(path.relative_to(output_dir)) for path in artifact_paths)
    supporting_artifacts = sorted(str(path.relative_to(output_dir)) for path in supporting_paths)
    statuses: dict[str, str] = {
        "ingest_source": "success",
        "validate_lint": "success",
        "query_strict": "success",
        "comments": "success" if comments_result is not None else "skipped",
    }
    if comments_requested is not None and comments_result is None:
        statuses["comments"] = "skipped"

    manifest: dict[str, object] = {
        "schema_version": "evaluate_source_manifest_v1",
        "evaluation_id": evaluation_id,
        "created_at": format_timestamp_rfc3339_utc(datetime.now(UTC)),
        "workflow_key": "evaluate_source_quality",
        "source_path_or_url": source_path_or_url,
        "space_name": space_name,
        "registry_path": str(registry_path),
        "site_path": str(site_path),
        "space_root": str(space_root),
        "output_dir": str(output_dir),
        "run_ids": {
            "ingest": ingest_run_id,
            "query": None,
            "comments": None,
        },
        "workflow_statuses": statuses,
        "lint": lint_envelope,
        "markdown_artifacts": markdown_artifacts,
        "supporting_artifacts": supporting_artifacts,
    }
    if build_manifest_path is not None:
        manifest["build_manifest_path"] = str(build_manifest_path)
    if comments_requested is not None:
        manifest["comments_requested"] = comments_requested
    return manifest


if __name__ == "__main__":
    raise SystemExit(main())
