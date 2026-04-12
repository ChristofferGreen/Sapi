#!/usr/bin/env python3
"""MVP Slice A gate verifier (TODO-0260)."""

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
    validate_ingest_run_frontmatter,
    validate_query_run_frontmatter,
)

_RUN_ID_RE = re.compile(r"run_id=(run-[^,\s)]+)")


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
    parser.add_argument("--site-name", default="Slice A Verification Site")
    parser.add_argument("--out")
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    site_path = Path(args.site_path).expanduser().resolve()
    source_path_or_url = str(Path(args.source_path_or_url).expanduser().resolve())
    space_root = site_path / "spaces" / args.space_name
    registry_path = site_path / "spaces.toml"

    try:
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

        ingest_command = [
            "bash",
            str(_REPO_ROOT / "ingest.sh"),
            str(site_path),
            args.space_name,
            source_path_or_url,
        ]
        if args.mock_llm:
            ingest_command.append("--mock-llm")
        if args.verbose:
            ingest_command.append("--verbose")
        ingest_step = _run_checked("ingest", ingest_command)
        steps.append(ingest_step)

        steps.append(
            _run_checked(
                "build",
                [
                    "bash",
                    str(_REPO_ROOT / "regenerate_web.sh"),
                    str(site_path),
                    args.space_name,
                    *(["--verbose"] if args.verbose else []),
                ],
            )
        )

        query_command = [
            "bash",
            str(_REPO_ROOT / "query.sh"),
            str(site_path),
            args.space_name,
            args.question,
        ]
        if args.mock_llm:
            query_command.append("--mock-llm")
        if args.verbose:
            query_command.append("--verbose")
        query_step = _run_checked("query", query_command)
        steps.append(query_step)

        ingest_run_id = _extract_run_id(ingest_step.stdout)
        query_run_id = _extract_run_id(query_step.stdout)
        if ingest_run_id is None:
            raise ValueError("Unable to determine ingest run_id from ingest output.")
        if query_run_id is None:
            raise ValueError("Unable to determine query run_id from query output.")

        ingest_frontmatter = load_run_frontmatter(space_root=space_root, run_id=ingest_run_id)
        query_frontmatter = load_run_frontmatter(space_root=space_root, run_id=query_run_id)
        ingest_errors = validate_ingest_run_frontmatter(ingest_frontmatter)
        query_errors = validate_query_run_frontmatter(query_frontmatter)
        deferred_runs = deferred_build_backlog_run_ids(space_root=space_root)

        gate_errors = [*ingest_errors, *query_errors]
        if deferred_runs:
            gate_errors.append(
                "Deferred-build backlog must be zero for Slice A verification "
                f"(found={deferred_runs!r})."
            )
        steps.append(
            _synthetic_step(
                name="validate",
                command=[
                    "internal",
                    "slice_a_gate_validation",
                    "--check",
                    "run_envelopes",
                    "--check",
                    "deferred_build_backlog",
                ],
            )
        )

        verification_id = _verification_id()
        output_dir = (
            Path(args.out).expanduser().resolve()
            if args.out is not None
            else site_path / "outputs" / "verification" / "slice_a" / verification_id
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"
        manifest = {
            "verification_id": verification_id,
            "scope": "mvp_slice_a_exit_gates",
            "started_at": started_at,
            "completed_at": format_timestamp_rfc3339_utc(datetime.now(UTC)),
            "site_path": str(site_path),
            "space_name": args.space_name,
            "registry_path": str(registry_path),
            "source_path_or_url": source_path_or_url,
            "question": args.question,
            "run_ids": {
                "ingest": ingest_run_id,
                "query": query_run_id,
            },
            "steps": [
                {
                    "name": step.name,
                    "command": step.command,
                    "returncode": step.returncode,
                }
                for step in steps
            ],
            "checks": {
                "end_to_end_path_executed": [step.name for step in steps],
                "ingest_run_envelope_errors": ingest_errors,
                "query_run_envelope_errors": query_errors,
                "deferred_build_backlog_run_ids": deferred_runs,
            },
            "status": "success" if not gate_errors else "failed",
            "errors": gate_errors,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        if gate_errors:
            raise RuntimeError(
                "Slice A verification gate checks failed. "
                f"See manifest: {manifest_path}. Errors: {gate_errors!r}"
            )

        print(
            "scripts/verify_slice_a.py verification complete "
            f"(verification_id={verification_id}, manifest_path={manifest_path}, "
            f"ingest_run_id={ingest_run_id}, query_run_id={query_run_id})"
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


def _synthetic_step(*, name: str, command: list[str]) -> StepResult:
    return StepResult(
        name=name,
        command=command,
        returncode=0,
        stdout="",
        stderr="",
    )


def _extract_run_id(stdout: str) -> str | None:
    match = _RUN_ID_RE.search(stdout)
    if match is None:
        return None
    return match.group(1)


def _verification_id() -> str:
    return datetime.now(UTC).strftime("slice-a-%Y%m%dT%H%M%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
