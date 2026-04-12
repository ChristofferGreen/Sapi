#!/usr/bin/env python3
"""Lint/validate entrypoint with workflow-key gate dispatch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.lint.lint_engine import (
    LintSummary,
    WORKFLOW_KEYS,
    default_lint_summary,
    evaluate_lint_gate,
    parse_warning_budget,
)
from sapi.lint.guardrails import GuardrailIssue, evaluate_pipeline_pr_evidence, run_guardrail_checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--workflow", action="append", default=[])
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--warning-budget")
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


def _select_single_value(values: list[str], *, flag_name: str) -> str | None:
    if not values:
        return None
    if len(values) > 1:
        raise ValueError(f"{flag_name} may be provided at most once.")
    value = values[0].strip()
    if not value:
        raise ValueError(f"{flag_name} cannot be empty.")
    return value


def _lint_summary_from_run(space_root: Path, *, run_id: str | None) -> LintSummary:
    if run_id is None:
        return default_lint_summary()

    lint_path = space_root / "runs" / run_id / "lint.json"
    if not lint_path.is_file():
        raise FileNotFoundError(f"Lint artifact not found for run_id={run_id}: {lint_path}")

    payload = json.loads(lint_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Lint artifact must be a JSON object: {lint_path}")

    return LintSummary(
        error_count=_read_non_negative_int(payload, "error_count", lint_path=lint_path),
        warning_count=_read_non_negative_int(payload, "warning_count", lint_path=lint_path),
        info_count=_read_non_negative_int(payload, "info_count", lint_path=lint_path),
        issues=(),
    )


def _read_non_negative_int(payload: dict[str, object], key: str, *, lint_path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{lint_path} contains invalid {key!r}; expected non-negative integer.")
    return value


def _render_lint_envelope(
    *,
    workflow: str,
    run_id: str | None,
    warning_threshold: int,
    summary: LintSummary,
    blocked: bool,
    status: str,
) -> str:
    envelope = {
        "status": status,
        "reason": "lint_gate" if blocked else None,
        "workflow": workflow,
        "run_id": run_id,
        "warning_threshold": warning_threshold,
        "lint": {
            "error_count": summary.error_count,
            "warning_count": summary.warning_count,
            "info_count": summary.info_count,
        },
    }
    return json.dumps(envelope, sort_keys=True)


def run_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        registry_path = resolve_registry_path(args.registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        selected_workflow = _select_single_value(args.workflow, flag_name="--workflow") or "ingest_source"
        if selected_workflow not in WORKFLOW_KEYS:
            raise ValueError(
                f"Unsupported workflow key: {selected_workflow!r}. "
                f"Allowed values: {', '.join(sorted(WORKFLOW_KEYS))}"
            )
        selected_run_id = _select_single_value(args.run_id, flag_name="--run-id")
        warning_threshold = parse_warning_budget(args.warning_budget)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

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

    try:
        lint_summary = _lint_summary_from_run(space_root, run_id=selected_run_id)
        gate = evaluate_lint_gate(
            selected_workflow,
            lint_summary,
            warning_threshold,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        _render_lint_envelope(
            workflow=selected_workflow,
            run_id=selected_run_id,
            warning_threshold=warning_threshold,
            summary=lint_summary,
            blocked=gate.blocked,
            status=gate.status,
        )
    )
    return 1 if gate.blocked else 0


def main() -> int:
    return run_main()


if __name__ == "__main__":
    raise SystemExit(main())
