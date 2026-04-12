#!/usr/bin/env python3
"""Bootstrap stub for lint/validate entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.lint.guardrails import GuardrailIssue, evaluate_pipeline_pr_evidence, run_guardrail_checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--workflow", action="append", default=[])
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Repo-relative changed file path (repeatable) for pipeline checklist quality gates.",
    )
    parser.add_argument(
        "--pipeline-pr-checklist",
        default=None,
        help="Path to completed pipeline PR checklist evidence markdown.",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def _format_guardrail_issue(issue: GuardrailIssue, *, repo_root: Path) -> str:
    try:
        display_path = issue.path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        display_path = issue.path.resolve()
    return f"- [{issue.check_id}] {display_path}:{issue.line}: {issue.message}"


def run_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry_path = resolve_registry_path(args.registry_path)
    resolve_space_root(registry_path, args.space_name)
    issues = run_guardrail_checks(_REPO_ROOT)
    issues.extend(
        evaluate_pipeline_pr_evidence(
            repo_root=_REPO_ROOT,
            changed_files=args.changed_file,
            checklist_path=args.pipeline_pr_checklist,
        )
    )
    if issues:
        print("Guardrail checks failed:", file=sys.stderr)
        for issue in issues:
            print(_format_guardrail_issue(issue, repo_root=_REPO_ROOT), file=sys.stderr)
        return 1
    print("scripts/lint.py scaffold ready")
    return 0


def main() -> int:
    return run_main()


if __name__ == "__main__":
    raise SystemExit(main())
