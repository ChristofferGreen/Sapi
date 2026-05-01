"""Cumulative synthesis refresh for prepared questions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from sapi.contracts.ids import format_timestamp_rfc3339_utc
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
    load_prepared_questions,
    write_prepared_question_record,
)


@dataclass(frozen=True)
class QuestionSynthesisContext:
    """Canonical context used to synthesize one prepared question."""

    question: dict[str, Any]
    sources: tuple[dict[str, Any], ...]
    claims: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    previous_synthesis: dict[str, Any]
    freshness: dict[str, Any]
    input_signature: str


@dataclass(frozen=True)
class QuestionSynthesisResult:
    """Outcome of one prepared-question synthesis refresh."""

    status: str
    question_id: str
    question_path: Path
    semantic_output_path: Path | None
    attempt_count: int
    refreshed: bool
    input_signature: str


def refresh_question_syntheses(
    *,
    space_root: Path,
    run_id: str,
    llm_client_factory: Callable[[QuestionSynthesisContext], LlmClient],
    transaction: ArtifactTransaction,
    question_ids: list[str] | None = None,
    stale_only: bool = True,
    force: bool = False,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> list[QuestionSynthesisResult]:
    """Refresh selected prepared questions, or all questions when no IDs are supplied."""
    questions = _select_questions(space_root=space_root, question_ids=question_ids)
    results: list[QuestionSynthesisResult] = []
    for question in questions:
        context = build_question_synthesis_context(space_root=space_root, question=question)
        current_signature = _existing_question_synthesis_signature(question)
        if stale_only and not force and current_signature == context.input_signature:
            results.append(
                record_question_synthesis_check(
                    space_root=space_root,
                    question=question,
                    run_id=run_id,
                    input_signature=context.input_signature,
                    transaction=transaction,
                    status="unchanged",
                )
            )
            continue
        results.append(
            run_question_synthesis_and_update(
                space_root=space_root,
                question_id=question.question_id,
                run_id=run_id,
                llm_client=llm_client_factory(context),
                transaction=transaction,
                force=force or not stale_only,
                max_repair_loops=max_repair_loops,
                trace_ctx=trace_ctx,
            )
        )
    return results


def run_question_synthesis_and_update(
    *,
    space_root: Path,
    question_id: str,
    run_id: str,
    llm_client: LlmClient,
    transaction: ArtifactTransaction,
    force: bool = False,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> QuestionSynthesisResult:
    """Regenerate and persist synthesis for one prepared question when its context is stale."""
    question = _load_question(space_root=space_root, question_id=question_id)
    context = build_question_synthesis_context(space_root=space_root, question=question)
    current_signature = _existing_question_synthesis_signature(question)
    if not force and current_signature == context.input_signature:
        return record_question_synthesis_check(
            space_root=space_root,
            question=question,
            run_id=run_id,
            input_signature=context.input_signature,
            transaction=transaction,
            status="unchanged",
        )

    repo_root = Path(__file__).resolve().parents[2]
    resolved = resolve_semantic_invocation_spec(
        "question_synthesis",
        repo_root=repo_root,
        path_tokens={
            "space_root": space_root,
            "run_id": run_id,
            "question_id": question.question_id,
        },
    )
    semantic_output, attempt_count = run_semantic_flow(
        spec=_to_runtime_spec(resolved),
        llm_client=llm_client,
        max_repair_loops=max_repair_loops,
        trace_ctx=trace_ctx,
    )
    transaction.mark_create(resolved.output_json_path)
    _validate_question_synthesis_output(
        payload=semantic_output,
        question=question,
    )
    _write_synthesis_payload(
        space_root=space_root,
        question=question,
        run_id=run_id,
        semantic_output_path=resolved.output_json_path,
        input_signature=context.input_signature,
        synthesis=semantic_output,
        transaction=transaction,
        status="refreshed",
    )
    return QuestionSynthesisResult(
        status="refreshed",
        question_id=question.question_id,
        question_path=question.path,
        semantic_output_path=resolved.output_json_path,
        attempt_count=attempt_count,
        refreshed=True,
        input_signature=context.input_signature,
    )


def record_question_synthesis_check(
    *,
    space_root: Path,
    question: PreparedQuestion,
    run_id: str,
    input_signature: str,
    transaction: ArtifactTransaction,
    status: str,
) -> QuestionSynthesisResult:
    """Record a non-generating synthesis pipeline check on the question artifact."""
    _write_synthesis_payload(
        space_root=space_root,
        question=question,
        run_id=run_id,
        semantic_output_path=None,
        input_signature=input_signature,
        synthesis=dict(question.synthesis),
        transaction=transaction,
        status=status,
    )
    return QuestionSynthesisResult(
        status=status,
        question_id=question.question_id,
        question_path=question.path,
        semantic_output_path=None,
        attempt_count=0,
        refreshed=False,
        input_signature=input_signature,
    )


def build_question_synthesis_context(
    *,
    space_root: Path,
    question: PreparedQuestion,
) -> QuestionSynthesisContext:
    """Build canonical linked context and its stable input signature."""
    sources = tuple(
        _read_json_object(space_root / "sources" / "records" / f"{source_id}.json")
        for source_id in sorted(question.linked_source_ids)
    )
    claims = tuple(
        _read_json_object(space_root / "claims" / f"{claim_id}.json")
        for claim_id in sorted(question.claim_ids)
    )
    evidence = tuple(
        _read_json_object(space_root / "evidence" / f"{evidence_id}.json")
        for evidence_id in sorted(question.evidence_ids)
    )
    question_context = {
        "question_id": question.question_id,
        "question": question.question,
        "status": question.status,
        "display_order": question.display_order,
        "scope": {"space_name": question.scope_space_name},
        "linked_source_ids": list(question.linked_source_ids),
        "claim_ids": list(question.claim_ids),
        "evidence_ids": list(question.evidence_ids),
        "measurement_ids": list(question.measurement_ids),
    }
    signature_payload = {
        "schema_version": "question_synthesis_input_v1",
        "question": question_context,
        "sources": sources,
        "claims": claims,
        "evidence": evidence,
    }
    return QuestionSynthesisContext(
        question=question_context,
        sources=sources,
        claims=claims,
        evidence=evidence,
        previous_synthesis=dict(question.synthesis),
        freshness=dict(question.freshness),
        input_signature=_stable_signature(signature_payload),
    )


def _write_synthesis_payload(
    *,
    space_root: Path,
    question: PreparedQuestion,
    run_id: str,
    semantic_output_path: Path | None,
    input_signature: str,
    synthesis: dict[str, Any],
    transaction: ArtifactTransaction,
    status: str,
) -> Path:
    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    freshness = dict(question.freshness)
    previous_synthesis_freshness = freshness.get("question_synthesis")
    previous_semantic_output_path_raw = (
        previous_synthesis_freshness.get("semantic_output_path")
        if isinstance(previous_synthesis_freshness, dict)
        else None
    )
    previous_semantic_output_path = (
        previous_semantic_output_path_raw
        if isinstance(previous_semantic_output_path_raw, str)
        else None
    )
    semantic_output_path_value = (
        _space_relative_path(semantic_output_path, space_root=space_root)
        if semantic_output_path is not None
        else previous_semantic_output_path
    )
    freshness["question_synthesis"] = {
        "status": status,
        "run_id": run_id,
        "input_signature": input_signature,
        "semantic_output_path": semantic_output_path_value,
        "refreshed_at": completed_at,
    }
    checks = freshness.get("question_synthesis_checks")
    if not isinstance(checks, list):
        checks = []
    checks.append(
        {
            "status": status,
            "run_id": run_id,
            "input_signature": input_signature,
            "semantic_output_path": semantic_output_path_value,
            "checked_at": completed_at,
        }
    )
    freshness["question_synthesis_checks"] = checks[-25:]

    payload: dict[str, Any] = {
        "schema_version": "prepared_question_v1",
        "question_id": question.question_id,
        "question": question.question,
        "status": question.status,
        "display_order": question.display_order,
        "scope": {"space_name": question.scope_space_name},
        "linked_source_ids": list(question.linked_source_ids),
        "claim_ids": list(question.claim_ids),
        "evidence_ids": list(question.evidence_ids),
        "measurement_ids": list(question.measurement_ids),
        "synthesis": synthesis,
        "freshness": freshness,
        "warnings": list(question.warnings),
    }
    track_path_for_write(question.path, transaction=transaction)
    return write_prepared_question_record(
        space_root=space_root,
        space_name=question.scope_space_name,
        payload=payload,
    )


def _validate_question_synthesis_output(
    *,
    payload: dict[str, Any],
    question: PreparedQuestion,
) -> None:
    if payload.get("question_id") != question.question_id:
        raise ValueError(
            "question_synthesis payload question_id must match prepared question "
            f"{question.question_id!r}."
        )
    linked_source_ids = set(question.linked_source_ids)
    linked_claim_ids = set(question.claim_ids)
    linked_evidence_ids = set(question.evidence_ids)
    for collection_name in ("conclusions", "disagreements"):
        values = payload.get(collection_name)
        if not isinstance(values, list):
            raise ValueError(f"question_synthesis.{collection_name} must be an array.")
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                raise ValueError(f"question_synthesis.{collection_name}[{index}] must be an object.")
            _require_allowed_ids(
                item.get("source_ids"),
                allowed=linked_source_ids,
                field=f"question_synthesis.{collection_name}[{index}].source_ids",
            )
            _require_allowed_ids(
                item.get("claim_ids"),
                allowed=linked_claim_ids,
                field=f"question_synthesis.{collection_name}[{index}].claim_ids",
            )
            _require_allowed_ids(
                item.get("evidence_ids"),
                allowed=linked_evidence_ids,
                field=f"question_synthesis.{collection_name}[{index}].evidence_ids",
            )

    anchors = payload.get("citation_anchors")
    if not isinstance(anchors, list):
        raise ValueError("question_synthesis.citation_anchors must be an array.")
    for index, anchor in enumerate(anchors):
        if not isinstance(anchor, dict):
            raise ValueError(f"question_synthesis.citation_anchors[{index}] must be an object.")
        source_id = anchor.get("source_id")
        if source_id not in linked_source_ids:
            raise ValueError(
                f"question_synthesis.citation_anchors[{index}].source_id references "
                f"unlinked source: {source_id}."
            )
        _require_allowed_ids(
            anchor.get("claim_ids"),
            allowed=linked_claim_ids,
            field=f"question_synthesis.citation_anchors[{index}].claim_ids",
        )
        _require_allowed_ids(
            anchor.get("evidence_ids"),
            allowed=linked_evidence_ids,
            field=f"question_synthesis.citation_anchors[{index}].evidence_ids",
        )


def _require_allowed_ids(value: Any, *, allowed: set[str], field: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array.")
    for item in value:
        if item not in allowed:
            raise ValueError(f"{field} references unlinked canonical ID: {item}.")


def _load_question(*, space_root: Path, question_id: str) -> PreparedQuestion:
    for question in load_prepared_questions(space_root):
        if question.question_id == question_id:
            return question
    raise ValueError(f"Prepared question not found: {question_id}.")


def _select_questions(*, space_root: Path, question_ids: list[str] | None) -> list[PreparedQuestion]:
    questions = load_prepared_questions(space_root)
    if question_ids is None:
        return questions
    by_id = {question.question_id: question for question in questions}
    selected: list[PreparedQuestion] = []
    for question_id in question_ids:
        if question_id not in by_id:
            raise ValueError(f"Prepared question not found: {question_id}.")
        selected.append(by_id[question_id])
    return selected


def _to_runtime_spec(resolved: Any) -> SemanticSpec:
    return SemanticSpec(
        flow_key=resolved.flow_key,
        version=resolved.version,
        schema_path=resolved.schema_path,
        output_json_path=resolved.output_json_path,
        context_paths=resolved.context_paths,
        spec_path=resolved.spec_path,
    )


def _existing_question_synthesis_signature(question: PreparedQuestion) -> str | None:
    metadata = question.freshness.get("question_synthesis")
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("input_signature")
    return value if isinstance(value, str) and value else None


def _stable_signature(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object.")
    return payload


def _space_relative_path(path: Path, *, space_root: Path) -> str:
    return str(path.resolve().relative_to(space_root.resolve()))
