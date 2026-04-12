#!/usr/bin/env python3
"""Testing-plan exit-criteria verifier (TODO-0263)."""

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
from sapi.core.registry import load_registry, resolve_space_root
from sapi.core.slice_a_gates import deferred_build_backlog_run_ids


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
    parser.add_argument(
        "--space-name",
        action="append",
        default=[],
        help="Space name to audit for deferred-build backlog (repeatable). Defaults to all spaces.",
    )
    parser.add_argument("--out")
    parser.add_argument(
        "--evidence-path",
        default=str(_REPO_ROOT / "docs" / "verification" / "testing_exit_criteria.latest.json"),
    )
    return parser


def run_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))

    try:
        site_path = Path(args.site_path).expanduser().resolve()
        registry_path = site_path / "spaces.toml"
        if not registry_path.is_file():
            raise FileNotFoundError(f"Registry file not found: {registry_path}")

        registry = load_registry(registry_path)
        known_space_names = [entry.space_name for entry in registry["spaces"]]
        target_space_names = args.space_name if args.space_name else known_space_names
        if not target_space_names:
            raise ValueError("No spaces found in registry for deferred-build backlog checks.")

        steps = [
            _run_step("pr_required_tiers", ["npm", "run", "test:pr"]),
            _run_step("determinism_tiers", ["npm", "run", "test:tier4-5"]),
            _run_step(
                "failure_rollback_suite",
                ["pytest", "-q", "tests/integration/failure", "-m", "not live_llm"],
            ),
        ]
        step_index = {step.name: step for step in steps}

        deferred_backlog: dict[str, list[str]] = {}
        for space_name in target_space_names:
            space_root = resolve_space_root(registry_path, space_name)
            deferred_backlog[space_name] = deferred_build_backlog_run_ids(space_root=space_root)

        checks = {
            "pr_required_tiers_green": step_index["pr_required_tiers"].returncode == 0,
            "determinism_checks_green": step_index["determinism_tiers"].returncode == 0,
            "rollback_leakage_regressions_absent": (
                step_index["failure_rollback_suite"].returncode == 0
            ),
            "deferred_build_backlog_clear": all(not run_ids for run_ids in deferred_backlog.values()),
        }
        errors = _gate_errors(checks=checks, deferred_backlog=deferred_backlog)

        verification_id = _verification_id()
        output_dir = (
            Path(args.out).expanduser().resolve()
            if args.out is not None
            else site_path / "outputs" / "verification" / "testing_exit_criteria" / verification_id
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"

        completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
        manifest = {
            "verification_id": verification_id,
            "scope": "testing_plan_exit_criteria",
            "started_at": started_at,
            "completed_at": completed_at,
            "site_path": str(site_path),
            "registry_path": str(registry_path),
            "space_names": target_space_names,
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
            "deferred_build_backlog_run_ids": deferred_backlog,
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
                    "scope": "testing_plan_exit_criteria",
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
                "Testing-plan exit criteria verification failed. "
                f"See manifest: {manifest_path}. Errors: {errors!r}"
            )

        print(
            "scripts/verify_testing_exit_criteria.py verification complete "
            f"(verification_id={verification_id}, manifest_path={manifest_path}, "
            f"evidence_path={evidence_path}, status=success)"
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def main() -> int:
    return run_main()


def _gate_errors(
    *,
    checks: dict[str, bool],
    deferred_backlog: dict[str, list[str]],
) -> list[str]:
    errors: list[str] = []
    if not checks["pr_required_tiers_green"]:
        errors.append("PR-required test tiers must pass (`npm run test:pr`).")
    if not checks["determinism_checks_green"]:
        errors.append("Determinism/golden checks must pass (`npm run test:tier4-5`).")
    if not checks["rollback_leakage_regressions_absent"]:
        errors.append(
            "Failure-semantics rollback/leakage regression suite must pass "
            "(`pytest -q tests/integration/failure -m \"not live_llm\"`)."
        )
    if not checks["deferred_build_backlog_clear"]:
        errors.append(
            "Deferred-build backlog must be zero before DoD closure "
            f"(found={deferred_backlog!r})."
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
    return datetime.now(UTC).strftime("testing-exit-%Y%m%dT%H%M%SZ")


def _excerpt(text: str, *, limit: int = 1200) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "...<truncated>"


if __name__ == "__main__":
    raise SystemExit(main())
