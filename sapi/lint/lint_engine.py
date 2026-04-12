"""Lint summary, warning-budget, gate-evaluation, and artifact helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from sapi.contracts.run_envelopes import RunStatus
from sapi.lint.severity import LintSeverity, normalize_lint_severity, severity_for_check


WORKFLOW_KEYS: frozenset[str] = frozenset(
    {
        "ingest_source",
        "create_comments",
        "generate_profiles",
        "build_site",
        "query",
        "rebuild_topic_collection",
    }
)
_LINT_GATED_BY_ERROR_AND_WARNING_THRESHOLD: frozenset[str] = frozenset(
    {
        "ingest_source",
        "create_comments",
        "generate_profiles",
        "rebuild_topic_collection",
    }
)
_LINT_GATED_BY_ERROR_ONLY: frozenset[str] = frozenset({"build_site"})
_NON_BLOCKING_WORKFLOWS: frozenset[str] = frozenset({"query"})


@dataclass(frozen=True)
class LintIssue:
    check_id: str
    message: str
    severity: LintSeverity | None = None
    path: str | None = None
    line: int | None = None

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise ValueError("check_id must be non-empty.")
        if not self.message.strip():
            raise ValueError("message must be non-empty.")
        if self.severity is None:
            object.__setattr__(self, "severity", severity_for_check(self.check_id))
            return
        object.__setattr__(self, "severity", normalize_lint_severity(self.severity))


@dataclass(frozen=True)
class LintSummary:
    error_count: int
    warning_count: int
    info_count: int
    issues: tuple[LintIssue, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "issues": [
                {
                    "check_id": issue.check_id,
                    "severity": issue.severity,
                    "message": issue.message,
                    "path": issue.path,
                    "line": issue.line,
                }
                for issue in self.issues
            ],
        }


@dataclass(frozen=True)
class GateResult:
    workflow: str
    blocked: bool
    status: RunStatus
    warning_threshold: int
    lint: LintSummary


def parse_warning_budget(raw_value: str | None, *, default: int = 200) -> int:
    if default <= 0:
        raise ValueError("default warning budget must be a positive integer.")
    if raw_value is None:
        return default
    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise ValueError("--warning-budget must be a positive integer.") from exc
    if parsed <= 0:
        raise ValueError("--warning-budget must be a positive integer.")
    return parsed


def summarize_lint_issues(issues: list[LintIssue]) -> LintSummary:
    error_count = 0
    warning_count = 0
    info_count = 0
    for issue in issues:
        severity = issue.severity
        assert severity is not None
        if severity == "error":
            error_count += 1
        elif severity == "warning":
            warning_count += 1
        else:
            info_count += 1
    return LintSummary(
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        issues=tuple(issues),
    )


def evaluate_lint_gate(
    workflow: str,
    summary: LintSummary,
    warning_threshold: int,
) -> GateResult:
    if workflow not in WORKFLOW_KEYS:
        raise ValueError(f"Unsupported workflow key: {workflow}")
    if warning_threshold <= 0:
        raise ValueError("warning_threshold must be a positive integer.")
    if summary.error_count < 0 or summary.warning_count < 0 or summary.info_count < 0:
        raise ValueError("Lint counts must be non-negative.")

    if workflow in _LINT_GATED_BY_ERROR_AND_WARNING_THRESHOLD:
        if summary.error_count > 0:
            return GateResult(
                workflow=workflow,
                blocked=True,
                status="failed",
                warning_threshold=warning_threshold,
                lint=summary,
            )
        status: RunStatus = (
            "success_with_warnings"
            if summary.warning_count > warning_threshold
            else "success"
        )
        return GateResult(
            workflow=workflow,
            blocked=False,
            status=status,
            warning_threshold=warning_threshold,
            lint=summary,
        )

    if workflow in _LINT_GATED_BY_ERROR_ONLY:
        return GateResult(
            workflow=workflow,
            blocked=summary.error_count > 0,
            status="failed" if summary.error_count > 0 else "success",
            warning_threshold=warning_threshold,
            lint=summary,
        )

    assert workflow in _NON_BLOCKING_WORKFLOWS
    return GateResult(
        workflow=workflow,
        blocked=False,
        status="success",
        warning_threshold=warning_threshold,
        lint=summary,
    )


def default_lint_summary(*, issues: list[LintIssue] | None = None) -> LintSummary:
    if not issues:
        return LintSummary(error_count=0, warning_count=0, info_count=0, issues=())
    return summarize_lint_issues(issues)


def write_lint_artifact(
    *,
    space_root: Path,
    run_id: str,
    workflow: str,
    summary: LintSummary,
) -> Path:
    if workflow not in WORKFLOW_KEYS:
        raise ValueError(f"Unsupported workflow key: {workflow}")
    lint_path = space_root / "runs" / run_id / "lint.json"
    lint_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "lint_summary_v1",
        "workflow": workflow,
        **summary.to_dict(),
    }
    lint_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return lint_path


def render_lint_summary_markdown(summary: LintSummary) -> str:
    return (
        f"error_count={summary.error_count} "
        f"warning_count={summary.warning_count} "
        f"info_count={summary.info_count}"
    )
