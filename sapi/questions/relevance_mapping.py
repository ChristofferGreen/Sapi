"""Prepared-question relevance mapping for newly ingested sources."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from sapi.contracts.semantic_specs import resolve_semantic_invocation_spec
from sapi.core.pipeline_runtime import track_path_for_write
from sapi.core.transactions import ArtifactTransaction
from sapi.llm.client import LlmClient
from sapi.llm.semantic_executor import (
    DEFAULT_MAX_REPAIR_LOOPS,
    SemanticSpec,
    TraceContext,
    run_semantic_flow,
)
from sapi.questions.prepared_questions import (
    PreparedQuestion,
    active_prepared_questions,
    write_prepared_question_record,
)


@dataclass(frozen=True)
class QuestionRelevanceMappingResult:
    """Outcome of one source-to-prepared-question relevance mapping step."""

    status: str
    active_question_count: int
    matched_question_ids: tuple[str, ...]
    updated_question_paths: tuple[Path, ...]
    semantic_output_path: Path | None
    attempt_count: int


def run_question_relevance_mapping_and_update(
    *,
    space_root: Path,
    source_id: str,
    run_id: str,
    llm_client: LlmClient,
    transaction: ArtifactTransaction,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> QuestionRelevanceMappingResult:
    """Map a new source to active prepared questions and update matched records."""
    questions = active_prepared_questions(space_root)
    if not questions:
        return QuestionRelevanceMappingResult(
            status="no_active_questions",
            active_question_count=0,
            matched_question_ids=(),
            updated_question_paths=(),
            semantic_output_path=None,
            attempt_count=0,
        )

    repo_root = Path(__file__).resolve().parents[2]
    resolved = resolve_semantic_invocation_spec(
        "question_relevance_mapping",
        repo_root=repo_root,
        path_tokens={
            "space_root": space_root,
            "run_id": run_id,
        },
    )
    semantic_output, attempt_count = run_semantic_flow(
        spec=_to_runtime_spec(resolved),
        llm_client=llm_client,
        max_repair_loops=max_repair_loops,
        trace_ctx=trace_ctx,
    )
    matches = _normalize_question_matches(
        payload=semantic_output,
        source_id=source_id,
        questions=questions,
        space_root=space_root,
    )
    if not matches:
        return QuestionRelevanceMappingResult(
            status="no_matches",
            active_question_count=len(questions),
            matched_question_ids=(),
            updated_question_paths=(),
            semantic_output_path=resolved.output_json_path,
            attempt_count=attempt_count,
        )

    questions_by_id = {question.question_id: question for question in questions}
    updated_paths: list[Path] = []
    matched_question_ids: list[str] = []
    for match in matches:
        question = questions_by_id[match["question_id"]]
        updated_paths.append(
            _append_mapping_to_question(
                space_root=space_root,
                question=question,
                source_id=source_id,
                run_id=run_id,
                semantic_output_path=resolved.output_json_path,
                match=match,
                transaction=transaction,
            )
        )
        matched_question_ids.append(str(match["question_id"]))

    return QuestionRelevanceMappingResult(
        status="mapped",
        active_question_count=len(questions),
        matched_question_ids=tuple(matched_question_ids),
        updated_question_paths=tuple(updated_paths),
        semantic_output_path=resolved.output_json_path,
        attempt_count=attempt_count,
    )


def _to_runtime_spec(resolved: Any) -> SemanticSpec:
    return SemanticSpec(
        flow_key=resolved.flow_key,
        version=resolved.version,
        schema_path=resolved.schema_path,
        output_json_path=resolved.output_json_path,
        context_paths=resolved.context_paths,
        spec_path=resolved.spec_path,
    )


def _normalize_question_matches(
    *,
    payload: dict[str, Any],
    source_id: str,
    questions: list[PreparedQuestion],
    space_root: Path,
) -> list[dict[str, Any]]:
    if payload.get("source_id") != source_id:
        raise ValueError(
            "question_relevance_mapping source_id must match newly ingested source_id "
            f"{source_id!r}."
        )
    raw_matches = payload.get("question_matches")
    if not isinstance(raw_matches, list):
        raise ValueError("question_relevance_mapping output requires question_matches as an array.")

    active_question_ids = {question.question_id for question in questions}
    normalized_matches: list[dict[str, Any]] = []
    seen_question_ids: set[str] = set()
    for index, raw_match in enumerate(raw_matches):
        if not isinstance(raw_match, dict):
            raise ValueError(f"question_matches[{index}] must be an object.")
        question_id = _required_string(raw_match, "question_id", index=index)
        if question_id not in active_question_ids:
            raise ValueError(
                f"question_matches[{index}].question_id must reference an active prepared question: "
                f"{question_id}."
            )
        if question_id in seen_question_ids:
            raise ValueError(f"Duplicate question_id in question_matches: {question_id}.")
        seen_question_ids.add(question_id)

        claim_ids = _required_string_list(raw_match, "claim_ids", index=index)
        evidence_ids = _required_string_list(raw_match, "evidence_ids", index=index)
        for claim_id in claim_ids:
            _require_record_source_id(
                path=space_root / "claims" / f"{claim_id}.json",
                id_field="claim_id",
                expected_id=claim_id,
                source_id=source_id,
            )
        for evidence_id in evidence_ids:
            _require_record_source_id(
                path=space_root / "evidence" / f"{evidence_id}.json",
                id_field="evidence_id",
                expected_id=evidence_id,
                source_id=source_id,
            )

        normalized_matches.append(
            {
                "question_id": question_id,
                "relevance": _required_string(raw_match, "relevance", index=index),
                "rationale": _required_string(raw_match, "rationale", index=index),
                "claim_ids": claim_ids,
                "evidence_ids": evidence_ids,
            }
        )
    return normalized_matches


def _append_mapping_to_question(
    *,
    space_root: Path,
    question: PreparedQuestion,
    source_id: str,
    run_id: str,
    semantic_output_path: Path,
    match: dict[str, Any],
    transaction: ArtifactTransaction,
) -> Path:
    freshness = dict(question.freshness)
    mapping_history = freshness.get("question_relevance_mappings")
    if not isinstance(mapping_history, list):
        mapping_history = []
    mapping_history = [
        item
        for item in mapping_history
        if not (isinstance(item, dict) and item.get("source_id") == source_id)
    ]
    mapping_history.append(
        {
            "source_id": source_id,
            "run_id": run_id,
            "semantic_output_path": _space_relative_path(semantic_output_path, space_root=space_root),
            "relevance": match["relevance"],
            "rationale": match["rationale"],
        }
    )
    freshness["question_relevance_mappings"] = mapping_history

    payload: dict[str, Any] = {
        "schema_version": "prepared_question_v1",
        "question_id": question.question_id,
        "question": question.question,
        "status": question.status,
        "display_order": question.display_order,
        "scope": {"space_name": question.scope_space_name},
        "linked_source_ids": _append_unique(list(question.linked_source_ids), [source_id]),
        "claim_ids": _append_unique(list(question.claim_ids), match["claim_ids"]),
        "evidence_ids": _append_unique(list(question.evidence_ids), match["evidence_ids"]),
        "measurement_ids": list(question.measurement_ids),
        "synthesis": dict(question.synthesis),
        "freshness": freshness,
        "warnings": list(question.warnings),
    }
    track_path_for_write(question.path, transaction=transaction)
    return write_prepared_question_record(
        space_root=space_root,
        space_name=question.scope_space_name,
        payload=payload,
    )


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = set(existing)
    result = list(existing)
    for value in additions:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _space_relative_path(path: Path, *, space_root: Path) -> str:
    return str(path.resolve().relative_to(space_root.resolve()))


def _required_string(payload: dict[str, Any], field: str, *, index: int) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"question_matches[{index}].{field} must be a non-empty string.")
    return value.strip()


def _required_string_list(payload: dict[str, Any], field: str, *, index: int) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        raise ValueError(f"question_matches[{index}].{field} must be an array.")
    normalized: list[str] = []
    seen: set[str] = set()
    for item_index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"question_matches[{index}].{field}[{item_index}] must be a non-empty string."
            )
        item = item.strip()
        if item in seen:
            raise ValueError(f"question_matches[{index}].{field} contains duplicate value {item}.")
        seen.add(item)
        normalized.append(item)
    return normalized


def _require_record_source_id(
    *,
    path: Path,
    id_field: str,
    expected_id: str,
    source_id: str,
) -> None:
    if not path.is_file():
        raise ValueError(f"question_relevance_mapping referenced missing {id_field}: {expected_id}.")
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object.")
    if payload.get(id_field) != expected_id:
        raise ValueError(f"{path}: {id_field} must equal {expected_id}.")
    if payload.get("source_id") != source_id:
        raise ValueError(
            f"{path}: {id_field} must belong to newly ingested source_id {source_id}."
        )
