"""Shared pipeline status, exit-code, and commit/rollback policy contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sapi.contracts.run_envelopes import (
    FlowSpecificFields,
    IngestRunFields,
    RunEnvelopeBase,
    RunStatus,
    write_run_record,
)
from sapi.core.transactions import (
    ArtifactTransaction,
    TerminalFailureDisposition,
    apply_terminal_failure_policy,
)
from sapi.core.run_truth import advance_reconciliation_state
from sapi.lint.lint_engine import (
    LintSummary,
    default_lint_summary,
    evaluate_lint_gate,
    render_lint_summary_markdown,
    write_lint_artifact,
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


def apply_lint_gate_to_run_base(
    *,
    base: RunEnvelopeBase,
    warning_budget: int,
    summary: LintSummary | None = None,
) -> str:
    """Stamp lint totals on the run envelope and merge gate status into the terminal state."""
    if base.status == "pending":
        raise ValueError("apply_lint_gate_to_run_base requires a terminal run status.")

    lint_summary = default_lint_summary() if summary is None else summary
    workflow = _workflow_key_for_pipeline(base.flow_key)
    gate = evaluate_lint_gate(workflow, lint_summary, warning_threshold=warning_budget)

    base.lint_error_count = lint_summary.error_count
    base.lint_warning_count = lint_summary.warning_count
    base.lint_info_count = lint_summary.info_count

    if base.status == "success":
        base.status = gate.status
    elif base.status == "success_with_warnings":
        if gate.status == "failed":
            base.status = "failed"
    elif base.status not in FAILURE_STATUSES:
        raise ValueError(f"Unsupported terminal run status for lint finalization: {base.status}")

    return render_lint_summary_markdown(lint_summary)


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
        write_lint_artifact(
            space_root=space_root,
            run_id=base.run_id,
            workflow=_workflow_key_for_pipeline(base.flow_key),
            summary=_lint_summary_from_base(base),
        )
        advance_reconciliation_state(
            space_root=space_root,
            base=base,
            transaction=transaction,
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
        _validate_force_mode_ingest_failure_fields(base=base, flow_fields=flow_fields)
        run_path = write_run_record(
            space_root=space_root,
            base=base,
            flow_fields=flow_fields,
            summary=summary,
            changes=changes,
            lint_summary=lint_summary,
            errors=errors,
        )
        write_lint_artifact(
            space_root=space_root,
            run_id=base.run_id,
            workflow=_workflow_key_for_pipeline(base.flow_key),
            summary=_lint_summary_from_base(base),
        )
        transaction.commit()

    return PipelineFinalizeResult(
        status=base.status,
        exit_code=exit_code,
        run_record_path=run_path,
        rollback_disposition=rollback_disposition,
    )


def _validate_force_mode_ingest_failure_fields(
    *,
    base: RunEnvelopeBase,
    flow_fields: FlowSpecificFields,
) -> None:
    if base.flow_key != "ingest_pipeline":
        raise ValueError("rollback_skipped run retention is only valid for ingest_pipeline.")
    if not isinstance(flow_fields, IngestRunFields):
        raise TypeError("ingest_pipeline requires IngestRunFields for force-mode failure retention.")
    if not flow_fields.force_mode or not flow_fields.rollback_skipped:
        raise ValueError(
            "Ingest force-mode retained failures must record force_mode=true and rollback_skipped=true."
        )


def _lint_summary_from_base(base: RunEnvelopeBase) -> LintSummary:
    return LintSummary(
        error_count=base.lint_error_count,
        warning_count=base.lint_warning_count,
        info_count=base.lint_info_count,
        issues=(),
    )


def _workflow_key_for_pipeline(pipeline_flow_key: str) -> str:
    flow_map = {
        "ingest_pipeline": "ingest_source",
        "query_pipeline": "query",
        "comment_section_pipeline": "create_comments",
        "persona_profile_pipeline": "generate_profiles",
        "overview_pipeline": "generate_overview",
        "question_pipeline": "refresh_questions",
    }
    try:
        return flow_map[pipeline_flow_key]
    except KeyError as exc:
        raise ValueError(f"Unsupported pipeline flow key: {pipeline_flow_key}") from exc
