"""Shared pipeline status, exit-code, and commit/rollback policy contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sapi.contracts.run_envelopes import (
    FlowSpecificFields,
    RunEnvelopeBase,
    RunStatus,
    write_run_record,
)
from sapi.core.transactions import (
    ArtifactTransaction,
    TerminalFailureDisposition,
    apply_terminal_failure_policy,
)


SUCCESS_STATUSES: frozenset[RunStatus] = frozenset({"success", "success_with_warnings"})
FAILURE_STATUSES: frozenset[RunStatus] = frozenset({"failed", "aborted"})


@dataclass(frozen=True)
class PipelineFinalizeResult:
    status: RunStatus
    exit_code: int
    run_record_path: Path | None
    rollback_disposition: TerminalFailureDisposition | None


def initialize_run_status() -> RunStatus:
    """Return the shared initial run status."""
    return "pending"


def finalize_run_status(
    *,
    lint_error_count: int,
    lint_warning_count: int,
    warning_budget: int = 200,
    terminal_error: bool = False,
    aborted: bool = False,
) -> RunStatus:
    """Apply the shared state-machine contract for final pipeline statuses."""
    if lint_error_count < 0 or lint_warning_count < 0:
        raise ValueError("Lint counts must be non-negative.")
    if warning_budget <= 0:
        raise ValueError("warning_budget must be a positive integer.")

    if aborted:
        return "aborted"
    if terminal_error or lint_error_count > 0:
        return "failed"
    if lint_warning_count > warning_budget:
        return "success_with_warnings"
    return "success"


def exit_code_for_status(status: RunStatus) -> int:
    """Map terminal run status to process exit code."""
    if status in SUCCESS_STATUSES:
        return 0
    if status in FAILURE_STATUSES:
        return 1
    raise ValueError(f"Exit code is undefined for non-terminal status: {status}")


def finalize_pipeline_run(
    *,
    space_root: Path,
    base: RunEnvelopeBase,
    flow_fields: FlowSpecificFields,
    transaction: ArtifactTransaction,
    force_mode: bool = False,
    summary: str = "",
    changes: str = "",
    lint_summary: str = "",
    errors: str = "",
) -> PipelineFinalizeResult:
    """Apply shared commit/rollback policy and emit run records when allowed."""
    if base.status == "pending":
        raise ValueError("finalize_pipeline_run requires a terminal run status.")

    exit_code = exit_code_for_status(base.status)
    if base.status in SUCCESS_STATUSES:
        run_path = write_run_record(
            space_root=space_root,
            base=base,
            flow_fields=flow_fields,
            summary=summary,
            changes=changes,
            lint_summary=lint_summary,
            errors=errors,
        )
        transaction.commit()
        return PipelineFinalizeResult(
            status=base.status,
            exit_code=exit_code,
            run_record_path=run_path,
            rollback_disposition=None,
        )

    rollback_disposition = apply_terminal_failure_policy(
        transaction=transaction,
        pipeline_flow_key=base.flow_key,
        force_mode=force_mode,
        run_container_path=space_root / "runs" / base.run_id,
    )
    run_path: Path | None = None
    if rollback_disposition.rollback_skipped:
        run_path = write_run_record(
            space_root=space_root,
            base=base,
            flow_fields=flow_fields,
            summary=summary,
            changes=changes,
            lint_summary=lint_summary,
            errors=errors,
        )
        transaction.commit()

    return PipelineFinalizeResult(
        status=base.status,
        exit_code=exit_code,
        run_record_path=run_path,
        rollback_disposition=rollback_disposition,
    )
