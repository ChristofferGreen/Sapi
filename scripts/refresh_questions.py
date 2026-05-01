#!/usr/bin/env python3
"""Refresh cumulative prepared-question synthesis artifacts."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc, make_run_id
from sapi.contracts.run_envelopes import QuestionRunFields, RunEnvelopeBase, RunStatus
from sapi.core.pipeline_policy import apply_lint_gate_to_run_base, finalize_pipeline_run
from sapi.core.pipeline_runtime import (
    add_llm_attempts,
    build_run_envelope_base,
    record_semantic_invocation,
)
from sapi.core.postprocess import run_space_build_postprocess
from sapi.core.registry import resolve_registry_path, resolve_site_path_from_registry, resolve_space_root
from sapi.core.runtime_flags import (
    RuntimeFlagSnapshot,
    add_runtime_flag_arguments,
    runtime_flags_summary_dict,
    snapshot_runtime_flags,
    validate_runtime_flag_arguments,
)
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.core.transactions import ArtifactTransaction
from sapi.lint.lint_engine import summarize_lint_issues
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import SemanticBackendConfig, generate_semantic_json_live
from sapi.llm.trace import SiteLlmTraceContext
from sapi.questions.linting import collect_question_lint_issues
from sapi.questions.measurements import (
    QuestionMeasurementContext,
    QuestionMeasurementResult,
    refresh_question_measurements,
)
from sapi.questions.prepared_questions import active_prepared_questions, load_prepared_questions
from sapi.questions.synthesis import (
    QuestionSynthesisContext,
    QuestionSynthesisResult,
    refresh_question_syntheses,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument(
        "--question-id",
        action="append",
        default=[],
        help="Prepared question ID to refresh; repeat for multiple IDs.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Refresh all active prepared questions. This is the default when no --question-id is supplied.",
    )
    parser.add_argument(
        "--stale-only",
        action="store_true",
        help="Skip questions whose synthesis input signature is already current. This is the default.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate selected question syntheses even when input signatures are unchanged.",
    )
    parser.add_argument("--build-deferred", action="store_true")
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--verbose", action="store_true")
    add_runtime_flag_arguments(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    run_id = make_run_id()
    transaction = ArtifactTransaction()
    toolchain_versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    semantic_flows: list[str] = []
    semantic_flow_invocation_counts: dict[str, int] = {}
    llm_attempt_count = 0

    try:
        if args.all and args.question_id:
            raise ValueError("--all cannot be combined with --question-id.")
        validate_runtime_flag_arguments(args)
        runtime_flags = snapshot_runtime_flags(args)
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=runtime_flags.mock_llm,
            env=os.environ,
        )
        registry_path = resolve_registry_path(args.registry_path)
        site_path = resolve_site_path_from_registry(registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        selected_question_ids = _select_question_ids(
            space_root=space_root,
            explicit_question_ids=args.question_id,
        )
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Question refresh failed: {exc}", file=sys.stderr)
        return 2

    trace_ctx = (
        SiteLlmTraceContext(site_path=site_path, verbose=True)
        if args.verbose
        else None
    )
    measurement_results: list[QuestionMeasurementResult] = []
    synthesis_results: list[QuestionSynthesisResult] = []
    build_manifest_path: Path | None = None

    try:
        measurement_results = refresh_question_measurements(
            space_root=space_root,
            run_id=run_id,
            llm_client_factory=lambda context: _build_question_measurement_client(
                runtime_flags=runtime_flags,
                context=context,
            ),
            transaction=transaction,
            question_ids=selected_question_ids,
            stale_only=True,
            force=bool(args.force),
            trace_ctx=trace_ctx,
        )
        for result in measurement_results:
            if result.attempt_count:
                record_semantic_invocation(
                    flow_key="question_measurement_extraction",
                    semantic_flows=semantic_flows,
                    semantic_flow_invocation_counts=semantic_flow_invocation_counts,
                )
                llm_attempt_count = add_llm_attempts(
                    llm_attempt_count=llm_attempt_count,
                    attempt_count=result.attempt_count,
                )
        synthesis_results = refresh_question_syntheses(
            space_root=space_root,
            run_id=run_id,
            llm_client_factory=lambda context: _build_question_synthesis_client(
                runtime_flags=runtime_flags,
                context=context,
            ),
            transaction=transaction,
            question_ids=selected_question_ids,
            stale_only=True,
            force=bool(args.force),
            trace_ctx=trace_ctx,
        )
        for result in synthesis_results:
            if result.attempt_count:
                record_semantic_invocation(
                    flow_key="question_synthesis",
                    semantic_flows=semantic_flows,
                    semantic_flow_invocation_counts=semantic_flow_invocation_counts,
                )
                llm_attempt_count = add_llm_attempts(
                    llm_attempt_count=llm_attempt_count,
                    attempt_count=result.attempt_count,
                )
        if args.simulate_terminal_failure:
            raise RuntimeError("Simulated terminal question refresh failure.")
        if not args.build_deferred:
            build_manifest_path = run_space_build_postprocess(
                repo_root=_REPO_ROOT,
                registry_path=registry_path,
                site_path=site_path,
                space_name=args.space_name,
            )
    except Exception as exc:
        completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
        base = _make_run_base(
            run_id=run_id,
            status="failed",
            started_at=started_at,
            completed_at=completed_at,
            execution_mode=runtime_policy.execution_mode,
            llm_backend=runtime_flags.llm_backend,
            llm_model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            semantic_flows=semantic_flows,
            semantic_flow_invocation_counts=semantic_flow_invocation_counts,
            llm_attempt_count=llm_attempt_count,
            toolchain_versions=toolchain_versions,
        )
        lint_summary = apply_lint_gate_to_run_base(
            base=base,
            warning_budget=runtime_flags.warning_budget,
        )
        finalized = finalize_pipeline_run(
            space_root=space_root,
            base=base,
            flow_fields=_make_flow_fields(
                space_name=args.space_name,
                selected_question_ids=selected_question_ids,
                measurement_results=measurement_results,
                synthesis_results=synthesis_results,
                force_mode=bool(args.force),
                build_deferred=bool(args.build_deferred),
                build_manifest_path=build_manifest_path,
            ),
            transaction=transaction,
            force_mode=False,
            summary="Prepared-question refresh failed; invocation-scoped outputs rolled back.",
            changes=_render_changes(
                measurement_results=measurement_results,
                synthesis_results=synthesis_results,
                selected_question_ids=selected_question_ids,
            ),
            lint_summary=lint_summary,
            errors=str(exc),
        )
        print(
            "scripts/refresh_questions.py refresh failed "
            f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
            f"status={finalized.status}, question_ids={selected_question_ids}, "
            f"runtime_flags={runtime_flags_summary_dict(runtime_flags)}, error={exc})",
            file=sys.stderr,
        )
        return finalized.exit_code

    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    base_status: RunStatus = "success_with_warnings" if args.build_deferred else "success"
    base = _make_run_base(
        run_id=run_id,
        status=base_status,
        started_at=started_at,
        completed_at=completed_at,
        execution_mode=runtime_policy.execution_mode,
        llm_backend=runtime_flags.llm_backend,
        llm_model=runtime_flags.llm_model,
        reasoning_effort=runtime_flags.llm_reasoning_effort,
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )
    question_lint_summary = summarize_lint_issues(
        collect_question_lint_issues(
            space_root,
            include_site_output=not args.build_deferred,
        )
    )
    lint_summary = apply_lint_gate_to_run_base(
        base=base,
        warning_budget=runtime_flags.warning_budget,
        summary=question_lint_summary,
    )
    finalized = finalize_pipeline_run(
        space_root=space_root,
        base=base,
        flow_fields=_make_flow_fields(
            space_name=args.space_name,
            selected_question_ids=selected_question_ids,
            measurement_results=measurement_results,
            synthesis_results=synthesis_results,
            force_mode=bool(args.force),
            build_deferred=bool(args.build_deferred),
            build_manifest_path=build_manifest_path,
        ),
        transaction=transaction,
        force_mode=False,
        summary="Prepared-question refresh completed successfully.",
        changes=_render_changes(
            measurement_results=measurement_results,
            synthesis_results=synthesis_results,
            selected_question_ids=selected_question_ids,
        ),
        lint_summary=lint_summary,
        errors="",
    )
    if finalized.exit_code != 0:
        print(
            "scripts/refresh_questions.py refresh failed "
            f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
            f"status={finalized.status}, question_ids={selected_question_ids}, "
            f"lint_error_count={base.lint_error_count}, lint_warning_count={base.lint_warning_count}, "
            f"runtime_flags={runtime_flags_summary_dict(runtime_flags)})",
            file=sys.stderr,
        )
        return finalized.exit_code
    print(
        "scripts/refresh_questions.py refresh complete "
        f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
        f"status={finalized.status}, question_ids={selected_question_ids}, "
        f"question_measurements_changed={sum(1 for result in measurement_results if result.refreshed)}, "
        f"question_measurements_unchanged={sum(1 for result in measurement_results if result.status == 'unchanged')}, "
        f"question_syntheses_changed={sum(1 for result in synthesis_results if result.refreshed)}, "
        f"question_syntheses_unchanged={sum(1 for result in synthesis_results if result.status == 'unchanged')}, "
        f"semantic_flows={semantic_flows}, "
        f"semantic_flow_invocation_counts={semantic_flow_invocation_counts}, "
        f"build_deferred={bool(args.build_deferred)}, "
        f"build_manifest_path={build_manifest_path}, "
        f"run_record_path={finalized.run_record_path}, "
        f"runtime_flags={runtime_flags_summary_dict(runtime_flags)})"
    )
    return finalized.exit_code


def _select_question_ids(*, space_root: Path, explicit_question_ids: list[str]) -> list[str]:
    if explicit_question_ids:
        available = {question.question_id for question in load_prepared_questions(space_root)}
        selected: list[str] = []
        for question_id in explicit_question_ids:
            if question_id not in available:
                raise ValueError(f"Prepared question not found: {question_id}.")
            if question_id not in selected:
                selected.append(question_id)
        return selected
    return [question.question_id for question in active_prepared_questions(space_root)]


def _make_run_base(
    *,
    run_id: str,
    status: RunStatus,
    started_at: str,
    completed_at: str,
    execution_mode: str,
    llm_backend: str,
    llm_model: str,
    reasoning_effort: str,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
    llm_attempt_count: int,
    toolchain_versions: dict[str, str],
) -> RunEnvelopeBase:
    return build_run_envelope_base(
        run_id=run_id,
        flow_key="question_pipeline",
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        execution_mode=execution_mode,
        llm_backend=llm_backend,
        llm_model=llm_model,
        reasoning_effort=reasoning_effort,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )


def _make_flow_fields(
    *,
    space_name: str,
    selected_question_ids: list[str],
    measurement_results: list[QuestionMeasurementResult],
    synthesis_results: list[QuestionSynthesisResult],
    force_mode: bool,
    build_deferred: bool,
    build_manifest_path: Path | None,
) -> QuestionRunFields:
    return QuestionRunFields(
        question_scope=space_name,
        question_ids=list(selected_question_ids),
        refresh_mode="force" if force_mode else "stale_only",
        stale_only=not force_mode,
        force_mode=force_mode,
        questions_checked=len(selected_question_ids),
        question_measurements_changed=sum(1 for result in measurement_results if result.refreshed),
        question_measurements_unchanged=sum(
            1 for result in measurement_results if result.status == "unchanged"
        ),
        question_syntheses_changed=sum(1 for result in synthesis_results if result.refreshed),
        question_syntheses_unchanged=sum(1 for result in synthesis_results if result.status == "unchanged"),
        build_deferred=build_deferred,
        build_manifest_path=str(build_manifest_path.resolve()) if build_manifest_path is not None else None,
    )


def _render_changes(
    *,
    measurement_results: list[QuestionMeasurementResult],
    synthesis_results: list[QuestionSynthesisResult],
    selected_question_ids: list[str],
) -> str:
    return (
        f"question_ids={selected_question_ids}, "
        f"questions_checked={len(selected_question_ids)}, "
        f"question_measurements_changed={sum(1 for result in measurement_results if result.refreshed)}, "
        f"question_measurements_unchanged={sum(1 for result in measurement_results if result.status == 'unchanged')}, "
        f"question_syntheses_changed={sum(1 for result in synthesis_results if result.refreshed)}, "
        f"question_syntheses_unchanged={sum(1 for result in synthesis_results if result.status == 'unchanged')}, "
        f"measurement_statuses={_summarize_statuses(measurement_results)}, "
        f"synthesis_statuses={_summarize_statuses(synthesis_results)}"
    )


def _summarize_statuses(results: list[QuestionMeasurementResult] | list[QuestionSynthesisResult]) -> str:
    if not results:
        return "no_active_questions"
    statuses = sorted({result.status for result in results})
    if len(statuses) == 1:
        return statuses[0]
    return "mixed:" + ",".join(statuses)


def _build_question_synthesis_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    context: QuestionSynthesisContext,
):
    if runtime_flags.mock_llm:
        return _MockQuestionSynthesisClient(context=context)
    return _LiveQuestionSynthesisClient(
        backend_config=SemanticBackendConfig(
            backend=runtime_flags.llm_backend,
            model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            timeout_secs=runtime_flags.llm_timeout_secs,
        ),
        context=context,
    )


def _build_question_measurement_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    context: QuestionMeasurementContext,
):
    if runtime_flags.mock_llm:
        return _MockQuestionMeasurementClient(context=context)
    return _LiveQuestionMeasurementClient(
        backend_config=SemanticBackendConfig(
            backend=runtime_flags.llm_backend,
            model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            timeout_secs=runtime_flags.llm_timeout_secs,
        ),
        context=context,
    )


class _MockQuestionMeasurementClient:
    """Deterministic measurement client for explicit --mock-llm test mode."""

    def __init__(self, *, context: QuestionMeasurementContext) -> None:
        self._context = context

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        question_id = str(self._context.question["question_id"])
        source_ids = [str(source.get("source_id")) for source in self._context.sources]
        claim_ids = [str(claim.get("claim_id")) for claim in self._context.claims]
        evidence_ids = [str(evidence.get("evidence_id")) for evidence in self._context.evidence]
        measurements: list[dict[str, object]] = []
        chart_groups: list[dict[str, object]] = []
        if source_ids and (claim_ids or evidence_ids):
            question_slug = question_id.removeprefix("question-").split("--", 1)[0]
            measurement_id = f"measurement-{question_slug}--123456789abc"
            measurements.append(
                {
                    "measurement_id": measurement_id,
                    "source_id": source_ids[0],
                    "claim_id": claim_ids[0] if claim_ids else None,
                    "evidence_id": evidence_ids[0] if evidence_ids else None,
                    "measure_name": "mock extracted value",
                    "value": 1.6,
                    "value_max": 2.2,
                    "unit": "fixture-units",
                    "population": "mock linked context",
                    "outcome": "question-relevant outcome",
                    "comparator": "fixture comparator",
                    "uncertainty": "Mock mode does not estimate real uncertainty.",
                }
            )
            chart_groups.append(
                {
                    "chart_group_id": "chart-mock-extracted-value",
                    "measure_name": "mock extracted value",
                    "unit": "fixture-units",
                    "outcome": "question-relevant outcome",
                    "population": "mock linked context",
                    "measurement_ids": [measurement_id],
                }
            )
        return json.dumps(
            {
                "schema_version": "question_measurement_extraction_v1",
                "question_id": question_id,
                "measurements": measurements,
                "chart_groups": chart_groups,
                "warnings": [] if measurements else ["No extractable mock measurements were available."],
            }
        )


class _LiveQuestionMeasurementClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        context: QuestionMeasurementContext,
    ) -> None:
        self._backend_config = backend_config
        self._context = context

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "must_include_question_id": self._context.question["question_id"],
                    "allowed_source_ids": [source.get("source_id") for source in self._context.sources],
                    "allowed_claim_ids": [claim.get("claim_id") for claim in self._context.claims],
                    "allowed_evidence_ids": [
                        evidence.get("evidence_id") for evidence in self._context.evidence
                    ],
                    "grounding_policy": (
                        "Extract numeric measurements only when they are explicitly present in linked "
                        "source, claim, or evidence context. Return an empty measurements array when "
                        "values are absent or incompatible; do not estimate or normalize values."
                    ),
                },
                "question_context": self._context.question,
                "sources": list(self._context.sources),
                "claims": list(self._context.claims),
                "evidence": list(self._context.evidence),
                "previous_measurements": list(self._context.previous_measurements),
                "freshness": self._context.freshness,
            },
        )


class _MockQuestionSynthesisClient:
    """Deterministic question-synthesis client for explicit --mock-llm test mode."""

    def __init__(self, *, context: QuestionSynthesisContext) -> None:
        self._context = context

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        question_id = str(self._context.question["question_id"])
        source_ids = [str(source.get("source_id")) for source in self._context.sources]
        claim_ids = [str(claim.get("claim_id")) for claim in self._context.claims]
        evidence_ids = [str(evidence.get("evidence_id")) for evidence in self._context.evidence]
        citation_anchors: list[dict[str, object]] = []
        if source_ids:
            citation_anchors.append(
                {
                    "anchor_id": "anchor-mock-refresh",
                    "label": "[S1]",
                    "source_id": source_ids[0],
                    "claim_ids": claim_ids[:1],
                    "evidence_ids": evidence_ids[:1],
                }
            )
        conclusions: list[dict[str, object]] = []
        if source_ids:
            conclusions.append(
                {
                    "text": "Mock refresh finds that the linked source remains relevant to this question.",
                    "support": "moderate",
                    "source_ids": source_ids,
                    "claim_ids": claim_ids,
                    "evidence_ids": evidence_ids,
                }
            )
        return json.dumps(
            {
                "schema_version": "question_synthesis_v1",
                "question_id": question_id,
                "short_answer": (
                    "The linked mock evidence supports a cautious answer; live LLM refresh is required "
                    "for production use."
                ),
                "conclusions": conclusions,
                "uncertainty": "Mock mode cannot estimate real-world uncertainty.",
                "disagreements": [],
                "citation_anchors": citation_anchors,
                "warnings": [] if source_ids else ["No linked source context is available."],
            }
        )


class _LiveQuestionSynthesisClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        context: QuestionSynthesisContext,
    ) -> None:
        self._backend_config = backend_config
        self._context = context

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "must_include_question_id": self._context.question["question_id"],
                    "allowed_source_ids": [source.get("source_id") for source in self._context.sources],
                    "allowed_claim_ids": [claim.get("claim_id") for claim in self._context.claims],
                    "allowed_evidence_ids": [
                        evidence.get("evidence_id") for evidence in self._context.evidence
                    ],
                    "grounding_policy": (
                        "Use only linked source, claim, and evidence context. Do not introduce new "
                        "canonical IDs or conclusions without direct support in that context."
                    ),
                },
                "question_context": self._context.question,
                "sources": list(self._context.sources),
                "claims": list(self._context.claims),
                "evidence": list(self._context.evidence),
                "previous_synthesis": self._context.previous_synthesis,
                "freshness": self._context.freshness,
            },
        )


if __name__ == "__main__":
    raise SystemExit(main())
