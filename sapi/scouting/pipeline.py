"""Source-scouting semantic flow orchestration."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any

from sapi.contracts.ids import format_timestamp_rfc3339_utc
from sapi.contracts.semantic_specs import resolve_semantic_invocation_spec
from sapi.core.pipeline_runtime import add_llm_attempts, build_run_envelope_base, record_semantic_invocation
from sapi.core.runtime_flags import RuntimeFlagSnapshot
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import SemanticBackendConfig, generate_semantic_json_live
from sapi.llm.semantic_executor import DEFAULT_MAX_REPAIR_LOOPS, SemanticSpec, TraceContext, run_semantic_flow
from sapi.questions.prepared_questions import PreparedQuestion
from sapi.scouting.store import CandidateQueue, append_scouted_candidates


@dataclass(frozen=True)
class SourceScoutingResult:
    run_id: str
    semantic_output_path: Path
    run_record_path: Path
    candidate_count: int
    candidate_ids: list[str]
    attempt_count: int
    status: str


def run_source_scouting_and_store(
    *,
    repo_root: Path,
    site_path: Path,
    space_root: Path,
    queue: CandidateQueue,
    question: PreparedQuestion,
    run_id: str,
    count: int,
    runtime_flags: RuntimeFlagSnapshot,
    llm_client: Any,
    trace_ctx: TraceContext | None = None,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
) -> SourceScoutingResult:
    if count <= 0:
        raise ValueError("count must be positive.")
    semantic_flows: list[str] = []
    invocation_counts: dict[str, int] = {}
    record_semantic_invocation(
        flow_key="source_scouting",
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=invocation_counts,
    )
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    resolved = resolve_semantic_invocation_spec(
        "source_scouting",
        repo_root=repo_root,
        path_tokens={
            "site_path": site_path,
            "space_root": space_root,
            "space_name": queue.space_name,
            "question_id": queue.question_id,
            "run_id": run_id,
        },
    )
    semantic_payload, attempt_count = run_semantic_flow(
        spec=SemanticSpec(
            flow_key=resolved.flow_key,
            version=resolved.version,
            schema_path=resolved.schema_path,
            output_json_path=resolved.output_json_path,
            context_paths=resolved.context_paths,
            spec_path=resolved.spec_path,
        ),
        llm_client=llm_client,
        max_repair_loops=max_repair_loops,
        trace_ctx=trace_ctx,
    )
    candidates = append_scouted_candidates(
        queue=queue,
        semantic_payload=semantic_payload,
        run_id=run_id,
        semantic_output_path=resolved.output_json_path,
        scouted_at=started_at,
    )
    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    base = build_run_envelope_base(
        run_id=run_id,
        flow_key="source_scouting_pipeline",
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=invocation_counts,
        status="success",
        started_at=started_at,
        completed_at=completed_at,
        execution_mode="mock_llm_test" if runtime_flags.mock_llm else "live_llm",
        llm_backend=runtime_flags.llm_backend,
        llm_model=runtime_flags.llm_model,
        reasoning_effort=runtime_flags.llm_reasoning_effort,
        llm_attempt_count=add_llm_attempts(llm_attempt_count=0, attempt_count=attempt_count),
        toolchain_versions={
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        },
    )
    run_record_path = queue.runs_root / run_id / "run.json"
    run_record_path.parent.mkdir(parents=True, exist_ok=True)
    run_payload = {
        **asdict(base),
        "space_name": queue.space_name,
        "question_id": queue.question_id,
        "question_text": question.question,
        "requested_count": count,
        "candidate_count": len(candidates),
        "candidate_ids": [candidate["candidate_id"] for candidate in candidates],
        "semantic_output_path": str(resolved.output_json_path),
        "warnings": list(semantic_payload.get("warnings") or []),
    }
    run_record_path.write_text(json.dumps(run_payload, indent=2, sort_keys=True) + "\n")
    return SourceScoutingResult(
        run_id=run_id,
        semantic_output_path=resolved.output_json_path,
        run_record_path=run_record_path,
        candidate_count=len(candidates),
        candidate_ids=[candidate["candidate_id"] for candidate in candidates],
        attempt_count=attempt_count,
        status="success",
    )


class MockSourceScoutingClient:
    """Deterministic source-scouting client for explicit --mock-llm test mode."""

    def __init__(
        self,
        *,
        space_name: str,
        question_id: str,
        question_text: str,
        count: int,
        candidate_plan: list[dict[str, Any]] | None = None,
    ) -> None:
        self._space_name = space_name
        self._question_id = question_id
        self._question_text = question_text
        self._count = count
        self._candidate_plan = candidate_plan or []

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        candidates = self._candidate_plan[: self._count] if self._candidate_plan else [
            _mock_candidate(index=index, question_text=self._question_text)
            for index in range(1, self._count + 1)
        ]
        return json.dumps(
            {
                "schema_version": "source_scouting_v1",
                "space_name": self._space_name,
                "question_id": self._question_id,
                "question_text": self._question_text,
                "candidates": candidates,
                "warnings": [],
            }
        )


class LiveSourceScoutingClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        task_context: dict[str, Any],
    ) -> None:
        self._backend_config = backend_config
        self._task_context = task_context

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context=self._task_context,
        )


def backend_config_from_runtime_flags(runtime_flags: RuntimeFlagSnapshot) -> SemanticBackendConfig:
    return SemanticBackendConfig(
        backend=runtime_flags.llm_backend,
        model=runtime_flags.llm_model,
        reasoning_effort=runtime_flags.llm_reasoning_effort,
        timeout_secs=runtime_flags.llm_timeout_secs,
    )


def _mock_candidate(*, index: int, question_text: str) -> dict[str, Any]:
    return {
        "title": f"Mock scouted paper {index}",
        "authors": [f"Mock Author {index}"],
        "venue": {
            "name": "Journal of Mock Research",
            "type": "journal",
            "publisher": "Sapi Test Fixtures",
            "reputation_rationale": "Deterministic mock venue for explicit test mode.",
        },
        "publication_year": 2024,
        "doi": f"10.0000/mock-scouted-paper-{index}",
        "landing_url": f"https://example.test/mock-scouted-paper-{index}",
        "pdf_url": None,
        "public_access": {
            "has_public_pdf": False,
            "access_status": "unknown",
            "evidence": "Mock candidate has no fixture PDF unless a mock candidate plan is supplied.",
        },
        "citation_signal": {
            "count": index * 10,
            "provider": "mock",
            "as_of": "2026-05-05",
            "confidence": "medium",
        },
        "ranking": {
            "rank": index,
            "answer_fit_score": 4,
            "venue_reputation_score": 3,
            "citation_score": 2,
            "interestingness_score": 4,
            "overall_score": 13,
            "answer_fit_rationale": f"Mock rationale tied to question: {question_text}",
            "interestingness_rationale": "Exercises the scouting ranking contract in test mode.",
            "overall_rationale": "Suitable deterministic mock candidate.",
        },
    }
