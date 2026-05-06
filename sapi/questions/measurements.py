"""Structured measurement extraction for prepared questions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from sapi.contracts.ids import format_timestamp_rfc3339_utc
from sapi.contracts.semantic_specs import resolve_semantic_invocation_spec
from sapi.core.pipeline_runtime import track_path_for_delete, track_path_for_write
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


MAX_QUESTION_MEASUREMENT_ROWS = 6


@dataclass(frozen=True)
class QuestionMeasurementContext:
    """Canonical context used to extract measurements for one prepared question."""

    question: dict[str, Any]
    sources: tuple[dict[str, Any], ...]
    claims: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    previous_measurements: tuple[dict[str, Any], ...]
    freshness: dict[str, Any]
    input_signature: str


@dataclass(frozen=True)
class QuestionMeasurementResult:
    """Outcome of one prepared-question measurement extraction refresh."""

    status: str
    question_id: str
    question_path: Path
    semantic_output_path: Path | None
    attempt_count: int
    refreshed: bool
    input_signature: str
    measurement_ids: tuple[str, ...]
    chart_group_count: int


def refresh_question_measurements(
    *,
    space_root: Path,
    run_id: str,
    llm_client_factory: Callable[[QuestionMeasurementContext], LlmClient],
    transaction: ArtifactTransaction,
    question_ids: list[str] | None = None,
    stale_only: bool = True,
    force: bool = False,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> list[QuestionMeasurementResult]:
    """Refresh measurement extraction for selected prepared questions."""
    questions = _select_questions(space_root=space_root, question_ids=question_ids)
    results: list[QuestionMeasurementResult] = []
    for question in questions:
        context = build_question_measurement_context(space_root=space_root, question=question)
        if not _has_extractable_context(context):
            results.append(
                record_question_measurement_check(
                    space_root=space_root,
                    question=question,
                    run_id=run_id,
                    input_signature=context.input_signature,
                    transaction=transaction,
                    status="no_linked_context",
                )
            )
            continue
        current_signature = _existing_question_measurement_signature(question)
        if stale_only and not force and current_signature == context.input_signature:
            results.append(
                record_question_measurement_check(
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
            run_question_measurement_extraction_and_update(
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


def run_question_measurement_extraction_and_update(
    *,
    space_root: Path,
    question_id: str,
    run_id: str,
    llm_client: LlmClient,
    transaction: ArtifactTransaction,
    force: bool = False,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> QuestionMeasurementResult:
    """Regenerate and persist measurement rows for one prepared question."""
    question = _load_question(space_root=space_root, question_id=question_id)
    context = build_question_measurement_context(space_root=space_root, question=question)
    if not _has_extractable_context(context):
        return record_question_measurement_check(
            space_root=space_root,
            question=question,
            run_id=run_id,
            input_signature=context.input_signature,
            transaction=transaction,
            status="no_linked_context",
        )

    current_signature = _existing_question_measurement_signature(question)
    if not force and current_signature == context.input_signature:
        return record_question_measurement_check(
            space_root=space_root,
            question=question,
            run_id=run_id,
            input_signature=context.input_signature,
            transaction=transaction,
            status="unchanged",
        )

    repo_root = Path(__file__).resolve().parents[2]
    resolved = resolve_semantic_invocation_spec(
        "question_measurement_extraction",
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
    semantic_output = _sanitize_question_measurement_output(semantic_output)
    semantic_output = _remap_foreign_measurement_id_collisions(
        payload=semantic_output,
        space_root=space_root,
        question=question,
    )
    resolved.output_json_path.write_text(json.dumps(semantic_output, indent=2, sort_keys=True) + "\n")
    transaction.mark_create(resolved.output_json_path)
    _validate_question_measurement_output(payload=semantic_output, question=question)
    measurement_ids, chart_group_count = _write_measurement_payload(
        space_root=space_root,
        question=question,
        run_id=run_id,
        semantic_output_path=resolved.output_json_path,
        input_signature=context.input_signature,
        extraction=semantic_output,
        transaction=transaction,
        status="refreshed",
    )
    return QuestionMeasurementResult(
        status="refreshed",
        question_id=question.question_id,
        question_path=question.path,
        semantic_output_path=resolved.output_json_path,
        attempt_count=attempt_count,
        refreshed=True,
        input_signature=context.input_signature,
        measurement_ids=tuple(measurement_ids),
        chart_group_count=chart_group_count,
    )


def record_question_measurement_check(
    *,
    space_root: Path,
    question: PreparedQuestion,
    run_id: str,
    input_signature: str,
    transaction: ArtifactTransaction,
    status: str,
) -> QuestionMeasurementResult:
    """Record a non-generating measurement extraction check on the question artifact."""
    metadata = question.freshness.get("question_measurement_extraction")
    chart_groups = metadata.get("chart_groups") if isinstance(metadata, dict) else []
    if not isinstance(chart_groups, list):
        chart_groups = []
    semantic_output_path = (
        metadata.get("semantic_output_path")
        if isinstance(metadata, dict) and isinstance(metadata.get("semantic_output_path"), str)
        else None
    )
    _write_measurement_metadata(
        space_root=space_root,
        question=question,
        run_id=run_id,
        semantic_output_path=semantic_output_path,
        input_signature=input_signature,
        measurement_ids=list(question.measurement_ids),
        chart_groups=chart_groups,
        warnings=_existing_measurement_warnings(question),
        transaction=transaction,
        status=status,
    )
    return QuestionMeasurementResult(
        status=status,
        question_id=question.question_id,
        question_path=question.path,
        semantic_output_path=None,
        attempt_count=0,
        refreshed=False,
        input_signature=input_signature,
        measurement_ids=tuple(question.measurement_ids),
        chart_group_count=len(chart_groups),
    )


def build_question_measurement_context(
    *,
    space_root: Path,
    question: PreparedQuestion,
) -> QuestionMeasurementContext:
    """Build canonical linked measurement context and a stable input signature."""
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
    previous_measurements = tuple(
        _read_json_object(space_root / "measurements" / f"{measurement_id}.json")
        for measurement_id in sorted(question.measurement_ids)
        if (space_root / "measurements" / f"{measurement_id}.json").is_file()
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
        "schema_version": "question_measurement_input_v1",
        "question": {
            key: value
            for key, value in question_context.items()
            if key != "measurement_ids"
        },
        "sources": sources,
        "claims": claims,
        "evidence": evidence,
    }
    return QuestionMeasurementContext(
        question=question_context,
        sources=sources,
        claims=claims,
        evidence=evidence,
        previous_measurements=previous_measurements,
        freshness=dict(question.freshness),
        input_signature=_stable_signature(signature_payload),
    )


def _write_measurement_payload(
    *,
    space_root: Path,
    question: PreparedQuestion,
    run_id: str,
    semantic_output_path: Path,
    input_signature: str,
    extraction: dict[str, Any],
    transaction: ArtifactTransaction,
    status: str,
) -> tuple[list[str], int]:
    measurements = extraction.get("measurements")
    chart_groups = extraction.get("chart_groups")
    warnings = extraction.get("warnings")
    if not isinstance(measurements, list):
        raise ValueError("question_measurement_extraction.measurements must be an array.")
    if not isinstance(chart_groups, list):
        raise ValueError("question_measurement_extraction.chart_groups must be an array.")
    if not isinstance(warnings, list):
        raise ValueError("question_measurement_extraction.warnings must be an array.")

    measurement_ids: list[str] = []
    for item in measurements:
        if not isinstance(item, dict):
            raise ValueError("question_measurement_extraction.measurements entries must be objects.")
        measurement_id = str(item["measurement_id"])
        measurement_ids.append(measurement_id)
        canonical_payload = {
            "schema_version": "question_measurement_v1",
            "question_id": question.question_id,
            **item,
        }
        measurement_path = space_root / "measurements" / f"{measurement_id}.json"
        _require_measurement_file_owned_by_question(
            measurement_path=measurement_path,
            question_id=question.question_id,
        )
        track_path_for_write(measurement_path, transaction=transaction)
        measurement_path.write_text(json.dumps(canonical_payload, indent=2, sort_keys=True) + "\n")

    _delete_stale_question_measurements(
        space_root=space_root,
        question=question,
        refreshed_measurement_ids=measurement_ids,
        transaction=transaction,
    )
    _write_measurement_metadata(
        space_root=space_root,
        question=question,
        run_id=run_id,
        semantic_output_path=_space_relative_path(semantic_output_path, space_root=space_root),
        input_signature=input_signature,
        measurement_ids=measurement_ids,
        chart_groups=chart_groups,
        warnings=[str(warning) for warning in warnings],
        transaction=transaction,
        status=status,
    )
    return measurement_ids, len(chart_groups)


def _delete_stale_question_measurements(
    *,
    space_root: Path,
    question: PreparedQuestion,
    refreshed_measurement_ids: list[str],
    transaction: ArtifactTransaction,
) -> None:
    refreshed = set(refreshed_measurement_ids)
    for measurement_id in question.measurement_ids:
        if measurement_id in refreshed:
            continue
        measurement_path = space_root / "measurements" / f"{measurement_id}.json"
        _require_measurement_file_owned_by_question(
            measurement_path=measurement_path,
            question_id=question.question_id,
        )
        track_path_for_delete(measurement_path, transaction=transaction)


def _require_measurement_file_owned_by_question(
    *,
    measurement_path: Path,
    question_id: str,
) -> None:
    if not measurement_path.exists():
        return
    try:
        payload = _read_json_object(measurement_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{measurement_path}: existing measurement file is not valid JSON.") from exc
    observed_question_id = payload.get("question_id")
    if observed_question_id != question_id:
        raise ValueError(
            f"{measurement_path}: existing measurement belongs to question_id "
            f"{observed_question_id!r}, not {question_id!r}."
        )


def _remap_foreign_measurement_id_collisions(
    *,
    payload: dict[str, Any],
    space_root: Path,
    question: PreparedQuestion,
) -> dict[str, Any]:
    measurements = payload.get("measurements")
    if not isinstance(measurements, list):
        return payload

    remapped_ids: dict[str, str] = {}
    used_ids = {
        item.get("measurement_id")
        for item in measurements
        if isinstance(item, dict) and isinstance(item.get("measurement_id"), str)
    }
    rewritten_measurements: list[Any] = []
    for item in measurements:
        if not isinstance(item, dict):
            rewritten_measurements.append(item)
            continue
        measurement_id = item.get("measurement_id")
        if not isinstance(measurement_id, str):
            rewritten_measurements.append(item)
            continue
        replacement_id = _replacement_measurement_id_for_question(
            measurement_id=measurement_id,
            space_root=space_root,
            question_id=question.question_id,
            used_ids=used_ids,
        )
        if replacement_id != measurement_id:
            remapped_ids[measurement_id] = replacement_id
            used_ids.add(replacement_id)
            rewritten = dict(item)
            rewritten["measurement_id"] = replacement_id
            rewritten_measurements.append(rewritten)
        else:
            rewritten_measurements.append(item)

    if not remapped_ids:
        return payload

    rewritten_payload = dict(payload)
    rewritten_payload["measurements"] = rewritten_measurements
    rewritten_payload["chart_groups"] = _rewrite_chart_group_measurement_ids(
        chart_groups=payload.get("chart_groups"),
        remapped_ids=remapped_ids,
    )
    warnings = payload.get("warnings")
    warning_values = [str(warning) for warning in warnings] if isinstance(warnings, list) else []
    warning_values.append(
        "Remapped measurement IDs that collided with existing measurements owned by other questions."
    )
    rewritten_payload["warnings"] = warning_values
    return rewritten_payload


def _replacement_measurement_id_for_question(
    *,
    measurement_id: str,
    space_root: Path,
    question_id: str,
    used_ids: set[object],
) -> str:
    measurement_path = space_root / "measurements" / f"{measurement_id}.json"
    if not measurement_path.exists():
        return measurement_id
    try:
        payload = _read_json_object(measurement_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{measurement_path}: existing measurement file is not valid JSON.") from exc
    if payload.get("question_id") == question_id:
        return measurement_id

    if "--" not in measurement_id:
        return measurement_id
    stem = measurement_id.rsplit("--", 1)[0]
    attempt = 0
    while True:
        salt = f"{measurement_id}\n{question_id}\n{attempt}".encode("utf-8")
        replacement_id = f"{stem}--{hashlib.sha256(salt).hexdigest()[:12]}"
        replacement_path = space_root / "measurements" / f"{replacement_id}.json"
        if replacement_id not in used_ids and not replacement_path.exists():
            return replacement_id
        if replacement_path.exists():
            try:
                replacement_payload = _read_json_object(replacement_path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{replacement_path}: existing measurement file is not valid JSON.") from exc
            if replacement_payload.get("question_id") == question_id:
                return replacement_id
        attempt += 1


def _rewrite_chart_group_measurement_ids(
    *,
    chart_groups: Any,
    remapped_ids: dict[str, str],
) -> Any:
    if not isinstance(chart_groups, list):
        return chart_groups
    rewritten_groups: list[Any] = []
    for group in chart_groups:
        if not isinstance(group, dict):
            rewritten_groups.append(group)
            continue
        measurement_ids = group.get("measurement_ids")
        if not isinstance(measurement_ids, list):
            rewritten_groups.append(group)
            continue
        rewritten = dict(group)
        rewritten["measurement_ids"] = [
            remapped_ids.get(measurement_id, measurement_id) for measurement_id in measurement_ids
        ]
        rewritten_groups.append(rewritten)
    return rewritten_groups


def _write_measurement_metadata(
    *,
    space_root: Path,
    question: PreparedQuestion,
    run_id: str,
    semantic_output_path: str | None,
    input_signature: str,
    measurement_ids: list[str],
    chart_groups: list[Any],
    warnings: list[str],
    transaction: ArtifactTransaction,
    status: str,
) -> Path:
    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    freshness = dict(question.freshness)
    freshness["question_measurement_extraction"] = {
        "status": status,
        "run_id": run_id,
        "input_signature": input_signature,
        "semantic_output_path": semantic_output_path,
        "refreshed_at": completed_at,
        "measurement_ids": list(measurement_ids),
        "chart_groups": list(chart_groups),
        "warnings": list(warnings),
    }
    checks = freshness.get("question_measurement_extraction_checks")
    if not isinstance(checks, list):
        checks = []
    checks.append(
        {
            "status": status,
            "run_id": run_id,
            "input_signature": input_signature,
            "semantic_output_path": semantic_output_path,
            "checked_at": completed_at,
            "measurement_ids": list(measurement_ids),
        }
    )
    freshness["question_measurement_extraction_checks"] = checks[-25:]

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
        "measurement_ids": list(measurement_ids),
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


def _validate_question_measurement_output(
    *,
    payload: dict[str, Any],
    question: PreparedQuestion,
) -> None:
    if payload.get("question_id") != question.question_id:
        raise ValueError(
            "question_measurement_extraction payload question_id must match prepared question "
            f"{question.question_id!r}."
        )
    linked_source_ids = set(question.linked_source_ids)
    linked_claim_ids = set(question.claim_ids)
    linked_evidence_ids = set(question.evidence_ids)

    measurements = payload.get("measurements")
    if not isinstance(measurements, list):
        raise ValueError("question_measurement_extraction.measurements must be an array.")
    if len(measurements) > MAX_QUESTION_MEASUREMENT_ROWS:
        raise ValueError(
            "question_measurement_extraction.measurements must contain at most "
            f"{MAX_QUESTION_MEASUREMENT_ROWS} question-relevant rows."
        )
    by_measurement_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(measurements):
        if not isinstance(item, dict):
            raise ValueError(f"question_measurement_extraction.measurements[{index}] must be an object.")
        measurement_id = item.get("measurement_id")
        if not isinstance(measurement_id, str) or not measurement_id:
            raise ValueError(f"question_measurement_extraction.measurements[{index}].measurement_id is required.")
        if measurement_id in by_measurement_id:
            raise ValueError(f"Duplicate measurement_id in question measurement output: {measurement_id}.")
        by_measurement_id[measurement_id] = item
        question_relevance = item.get("question_relevance")
        if not isinstance(question_relevance, str) or not question_relevance.strip():
            raise ValueError(
                f"question_measurement_extraction.measurements[{index}].question_relevance is required."
            )
        source_id = item.get("source_id")
        if source_id not in linked_source_ids:
            raise ValueError(
                f"question_measurement_extraction.measurements[{index}].source_id references "
                f"unlinked source: {source_id}."
            )
        claim_id = item.get("claim_id")
        evidence_id = item.get("evidence_id")
        if claim_id is None and evidence_id is None:
            raise ValueError(
                f"question_measurement_extraction.measurements[{index}] must reference a claim or evidence item."
            )
        if claim_id is not None and claim_id not in linked_claim_ids:
            raise ValueError(
                f"question_measurement_extraction.measurements[{index}].claim_id references "
                f"unlinked claim: {claim_id}."
            )
        if evidence_id is not None and evidence_id not in linked_evidence_ids:
            raise ValueError(
                f"question_measurement_extraction.measurements[{index}].evidence_id references "
                f"unlinked evidence: {evidence_id}."
            )
        value = item.get("value")
        value_max = item.get("value_max")
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"question_measurement_extraction.measurements[{index}].value must be numeric.")
        if value_max is not None:
            if isinstance(value_max, bool) or not isinstance(value_max, int | float):
                raise ValueError(
                    f"question_measurement_extraction.measurements[{index}].value_max must be numeric or null."
                )
            if value_max < value:
                raise ValueError(
                    f"question_measurement_extraction.measurements[{index}].value_max must be >= value."
                )

    chart_groups = payload.get("chart_groups")
    if not isinstance(chart_groups, list):
        raise ValueError("question_measurement_extraction.chart_groups must be an array.")
    seen_chart_group_ids: set[str] = set()
    for index, group in enumerate(chart_groups):
        if not isinstance(group, dict):
            raise ValueError(f"question_measurement_extraction.chart_groups[{index}] must be an object.")
        chart_group_id = group.get("chart_group_id")
        if not isinstance(chart_group_id, str) or not chart_group_id:
            raise ValueError(f"question_measurement_extraction.chart_groups[{index}].chart_group_id is required.")
        if chart_group_id in seen_chart_group_ids:
            raise ValueError(f"Duplicate chart_group_id in question measurement output: {chart_group_id}.")
        seen_chart_group_ids.add(chart_group_id)
        group_measurement_ids = group.get("measurement_ids")
        if not isinstance(group_measurement_ids, list) or not group_measurement_ids:
            raise ValueError(
                f"question_measurement_extraction.chart_groups[{index}].measurement_ids must be non-empty."
            )
        for measurement_id in group_measurement_ids:
            measurement = by_measurement_id.get(measurement_id)
            if measurement is None:
                raise ValueError(
                    f"question_measurement_extraction.chart_groups[{index}] references missing "
                    f"measurement_id {measurement_id!r}."
                )
            for field in ("measure_name", "unit", "outcome", "population"):
                if measurement.get(field) != group.get(field):
                    raise ValueError(
                        f"question_measurement_extraction.chart_groups[{index}] has incompatible "
                        f"{field} for measurement {measurement_id!r}."
                    )


def _sanitize_question_measurement_output(payload: dict[str, Any]) -> dict[str, Any]:
    measurements = payload.get("measurements")
    chart_groups = payload.get("chart_groups")
    warnings = payload.get("warnings")
    if not isinstance(measurements, list) or not isinstance(chart_groups, list):
        return payload

    by_measurement_id = {
        item.get("measurement_id"): item
        for item in measurements
        if isinstance(item, dict) and isinstance(item.get("measurement_id"), str)
    }
    compatible_groups: list[Any] = []
    dropped_count = 0
    for group in chart_groups:
        if not isinstance(group, dict) or not _question_measurement_chart_group_compatible(
            group=group,
            by_measurement_id=by_measurement_id,
        ):
            dropped_count += 1
            continue
        compatible_groups.append(group)
    if dropped_count == 0:
        return payload

    normalized_warnings = list(warnings) if isinstance(warnings, list) else []
    normalized_warnings.append(
        "Dropped incompatible question measurement chart group"
        + ("." if dropped_count == 1 else f"s ({dropped_count}).")
    )
    sanitized = dict(payload)
    sanitized["chart_groups"] = compatible_groups
    sanitized["warnings"] = normalized_warnings
    return sanitized


def _question_measurement_chart_group_compatible(
    *,
    group: dict[str, Any],
    by_measurement_id: dict[str, dict[str, Any]],
) -> bool:
    group_measurement_ids = group.get("measurement_ids")
    if not isinstance(group_measurement_ids, list) or not group_measurement_ids:
        return False
    for measurement_id in group_measurement_ids:
        measurement = by_measurement_id.get(measurement_id)
        if measurement is None:
            return False
        for field in ("measure_name", "unit", "outcome", "population"):
            if measurement.get(field) != group.get(field):
                return False
    return True


def _has_extractable_context(context: QuestionMeasurementContext) -> bool:
    return bool(context.sources and (context.claims or context.evidence))


def _existing_measurement_warnings(question: PreparedQuestion) -> list[str]:
    metadata = question.freshness.get("question_measurement_extraction")
    warnings = metadata.get("warnings") if isinstance(metadata, dict) else []
    if not isinstance(warnings, list):
        return []
    return [str(warning) for warning in warnings]


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


def _existing_question_measurement_signature(question: PreparedQuestion) -> str | None:
    metadata = question.freshness.get("question_measurement_extraction")
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
