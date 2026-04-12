#!/usr/bin/env python3
"""MVP Slice B gate verifier (TODO-0261)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc


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
    parser.add_argument("--out")
    parser.add_argument(
        "--evidence-path",
        default=str(_REPO_ROOT / "docs" / "verification" / "slice_b_exit_criteria.latest.json"),
    )
    return parser


def run_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))

    try:
        site_path = Path(args.site_path).expanduser().resolve()
        if not site_path.exists():
            raise FileNotFoundError(f"Site path not found: {site_path}")

        steps = [
            _run_step(
                "reliability_determinism",
                [
                    "pytest",
                    "-q",
                    "tests/integration/build/test_build_determinism.py",
                    "tests/integration/build/test_incremental_vs_full_equivalence.py",
                    "-m",
                    "not live_llm",
                ],
            ),
            _run_step(
                "ingest_build_query_contracts",
                [
                    "pytest",
                    "-q",
                    "tests/integration/pipelines/test_ingest_pipeline.py",
                    "tests/integration/pipelines/test_query_pipeline_outputs.py",
                    "tests/unit/contracts/test_run_envelope_semantic_flows.py",
                    "tests/golden/test_query_snapshot.py",
                    "tests/golden/test_run_envelope_snapshot.py",
                    "-m",
                    "not live_llm",
                ],
            ),
            _run_step(
                "operator_wrapper_usability",
                [
                    "pytest",
                    "-q",
                    "tests/integration/wrappers/test_bootstrap_registry_exception.py",
                    "tests/integration/wrappers/test_wrapper_alias_normalization.py",
                    "tests/integration/wrappers/test_wrapper_alias_conflicts.py",
                    "tests/integration/wrappers/test_regenerate_web_wrapper_contract.py",
                    "tests/integration/wrappers/test_wrapper_runtime_flags.py",
                    "-m",
                    "not live_llm",
                ],
            ),
        ]
        step_index = {step.name: step for step in steps}

        checks = {
            "reliability_determinism_green": step_index["reliability_determinism"].returncode == 0,
            "ingest_build_query_contracts_green": (
                step_index["ingest_build_query_contracts"].returncode == 0
            ),
            "operator_wrapper_usability_green": (
                step_index["operator_wrapper_usability"].returncode == 0
            ),
        }
        errors = _gate_errors(checks=checks)

        verification_id = _verification_id()
        output_dir = (
            Path(args.out).expanduser().resolve()
            if args.out is not None
            else site_path / "outputs" / "verification" / "slice_b" / verification_id
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"

        completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
        manifest = {
            "verification_id": verification_id,
            "scope": "mvp_slice_b_exit_gates",
            "started_at": started_at,
            "completed_at": completed_at,
            "site_path": str(site_path),
            "steps": [
                {
                    "name": step.name,
                    "command": step.command,
                    "returncode": step.returncode,
                    "stdout_excerpt": _excerpt(step.stdout),
                    "stderr_excerpt": _excerpt(step.stderr),
                }
                for step in steps
            ],
            "checks": checks,
            "status": "success" if not errors else "failed",
            "errors": errors,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

        evidence_path = Path(args.evidence_path).expanduser().resolve()
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(
                {
                    "verification_id": verification_id,
                    "scope": "mvp_slice_b_exit_gates",
                    "completed_at": completed_at,
                    "manifest_path": str(manifest_path),
                    "status": manifest["status"],
                    "checks": checks,
                    "errors": errors,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

        if errors:
            raise RuntimeError(
                "Slice B verification gate checks failed. "
                f"See manifest: {manifest_path}. Errors: {errors!r}"
            )

        print(
            "scripts/verify_slice_b.py verification complete "
            f"(verification_id={verification_id}, manifest_path={manifest_path}, "
            f"evidence_path={evidence_path}, status=success)"
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def main() -> int:
    return run_main()


def _gate_errors(*, checks: dict[str, bool]) -> list[str]:
    errors: list[str] = []
    if not checks["reliability_determinism_green"]:
        errors.append(
            "Reliability/determinism checks must pass for repeated rebuild behavior "
            "(tests/integration/build)."
        )
    if not checks["ingest_build_query_contracts_green"]:
        errors.append(
            "Ingest/build/query contract verification suite must pass with strong signal."
        )
    if not checks["operator_wrapper_usability_green"]:
        errors.append(
            "Wrapper/operator usability verification suite must pass without manual workarounds."
        )
    return errors


def _run_step(name: str, command: list[str]) -> StepResult:
    result = subprocess.run(
        command,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return StepResult(
        name=name,
        command=command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _verification_id() -> str:
    return datetime.now(UTC).strftime("slice-b-%Y%m%dT%H%M%SZ")


def _excerpt(text: str, *, limit: int = 1200) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "...<truncated>"


if __name__ == "__main__":
    raise SystemExit(main())
