"""Query result-shape and artifact-manifest contract helpers."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Mapping


_OUTPUT_MODES_WITH_MANIFEST: set[str] = {"mermaid", "images", "slides", "pdf"}
_OUTPUT_MODE_MARKDOWN = "markdown"
_RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_OPTIONAL_LIST_FIELDS: tuple[str, ...] = (
    "ancestor_pages_used",
    "inherited_conflicts",
    "synthesis_claim_ids",
)
_REQUIRED_RETRIEVAL_COUNT_KEYS: tuple[str, ...] = ("claims_retrieved", "sources_retrieved")
_REQUIRED_OMITTED_BUDGET_KEYS: tuple[str, ...] = ("claims", "sources")
_REQUIRED_LINT_SUMMARY_KEYS: tuple[str, ...] = ("error_count", "warning_count", "info_count")
_REQUIRED_EXECUTION_KEYS: tuple[str, ...] = (
    "execution_mode",
    "llm_attempt_count",
    "reasoning_effort",
    "model_fingerprint",
    "provider_fingerprint",
)
_REQUIRED_HIGH_SIGNAL_KEYS: tuple[str, ...] = (
    "query_id",
    "answer",
    "claims_used",
    "sources_used",
    "retrieval_counts",
    "contradictions_considered",
    "falsification_signals",
    "omitted_due_to_budget",
    "mode",
    "scope",
    "run_id",
    "query_timestamp_utc",
    "citation_coverage",
    "lint_summary",
    "execution",
    "warnings",
    "manifest_path",
)


def canonical_query_manifest_path(*, space_root: Path, query_id: str) -> Path:
    if not isinstance(query_id, str) or not query_id.strip():
        raise ValueError("query_id must be a non-empty string.")
    return (space_root / "outputs" / "query" / query_id / "manifest.json").resolve()


def build_query_result_record(
    *,
    query_id: str,
    answer: str,
    claims_used: list[str],
    sources_used: list[str],
    retrieval_counts: dict[str, int],
    contradictions_considered: int,
    falsification_signals: list[dict[str, Any]],
    omitted_due_to_budget: dict[str, int],
    mode: str,
    scope: str,
    run_id: str,
    query_timestamp_utc: str,
    citation_coverage: dict[str, Any],
    lint_summary: dict[str, Any],
    execution: dict[str, Any],
    warnings: list[dict[str, Any] | str],
    output_mode: str,
    space_root: Path,
    ancestor_pages_used: list[str] | None = None,
    inherited_conflicts: list[str] | None = None,
    synthesis_claim_ids: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "query_id": _require_non_empty_string(query_id, field_name="query_id"),
        "answer": _require_non_empty_string(answer, field_name="answer"),
        "claims_used": _require_string_list(claims_used, field_name="claims_used"),
        "sources_used": _require_string_list(sources_used, field_name="sources_used"),
        "retrieval_counts": _require_int_dict(retrieval_counts, field_name="retrieval_counts"),
        "contradictions_considered": _require_non_negative_int(
            contradictions_considered,
            field_name="contradictions_considered",
        ),
        "falsification_signals": _require_object_list(
            falsification_signals,
            field_name="falsification_signals",
        ),
        "omitted_due_to_budget": _require_int_dict(
            omitted_due_to_budget,
            field_name="omitted_due_to_budget",
        ),
        "mode": _require_non_empty_string(mode, field_name="mode"),
        "scope": _require_non_empty_string(scope, field_name="scope"),
        "run_id": _require_non_empty_string(run_id, field_name="run_id"),
        "query_timestamp_utc": _require_non_empty_string(
            query_timestamp_utc,
            field_name="query_timestamp_utc",
        ),
        "citation_coverage": _require_object(citation_coverage, field_name="citation_coverage"),
        "lint_summary": _require_object(lint_summary, field_name="lint_summary"),
        "execution": _require_object(execution, field_name="execution"),
        "warnings": _require_array(warnings, field_name="warnings"),
    }

    _set_manifest_path_for_output_mode(
        payload=payload,
        output_mode=output_mode,
        space_root=space_root,
    )

    optional_values = {
        "ancestor_pages_used": ancestor_pages_used,
        "inherited_conflicts": inherited_conflicts,
        "synthesis_claim_ids": synthesis_claim_ids,
    }
    for field_name, value in optional_values.items():
        normalized = _normalize_optional_string_list(value, field_name=field_name)
        if normalized is not None:
            payload[field_name] = normalized

    validate_query_result_shape(
        payload,
        output_mode=output_mode,
        space_root=space_root,
    )
    return payload


def validate_query_result_shape(
    payload: Mapping[str, Any],
    *,
    output_mode: str,
    space_root: Path,
) -> None:
    missing = [key for key in _REQUIRED_HIGH_SIGNAL_KEYS if key not in payload]
    if missing:
        raise ValueError("Query result missing required high-signal keys: " + ", ".join(missing))

    for key in (
        "query_id",
        "answer",
        "mode",
        "scope",
        "run_id",
        "query_timestamp_utc",
    ):
        _require_non_empty_string(payload.get(key), field_name=key)
    query_timestamp_utc = _require_non_empty_string(
        payload.get("query_timestamp_utc"),
        field_name="query_timestamp_utc",
    )
    if not _RFC3339_UTC_RE.fullmatch(query_timestamp_utc):
        raise ValueError("query_timestamp_utc must be RFC 3339 UTC with trailing Z.")

    retrieval_counts = _require_int_dict(payload.get("retrieval_counts"), field_name="retrieval_counts")
    _require_object_int_keys(
        retrieval_counts,
        field_name="retrieval_counts",
        required_keys=_REQUIRED_RETRIEVAL_COUNT_KEYS,
    )
    omitted_due_to_budget = _require_int_dict(
        payload.get("omitted_due_to_budget"),
        field_name="omitted_due_to_budget",
    )
    _require_object_int_keys(
        omitted_due_to_budget,
        field_name="omitted_due_to_budget",
        required_keys=_REQUIRED_OMITTED_BUDGET_KEYS,
    )

    _require_object(payload.get("citation_coverage"), field_name="citation_coverage")
    lint_summary = _require_object(payload.get("lint_summary"), field_name="lint_summary")
    _require_object_int_keys(
        lint_summary,
        field_name="lint_summary",
        required_keys=_REQUIRED_LINT_SUMMARY_KEYS,
    )
    execution = _require_object(payload.get("execution"), field_name="execution")
    for key in _REQUIRED_EXECUTION_KEYS:
        if key not in execution:
            raise ValueError(f"execution is missing required key: {key}")
    _require_non_empty_string(execution.get("execution_mode"), field_name="execution.execution_mode")
    _require_non_negative_int(execution.get("llm_attempt_count"), field_name="execution.llm_attempt_count")
    _require_non_empty_string(
        execution.get("reasoning_effort"),
        field_name="execution.reasoning_effort",
    )
    _require_non_empty_string(
        execution.get("model_fingerprint"),
        field_name="execution.model_fingerprint",
    )
    _require_non_empty_string(
        execution.get("provider_fingerprint"),
        field_name="execution.provider_fingerprint",
    )

    for key in ("claims_used", "sources_used"):
        _require_string_list(payload.get(key), field_name=key)
    _require_object_list(payload.get("falsification_signals"), field_name="falsification_signals")
    _require_array(payload.get("warnings"), field_name="warnings")
    _require_non_negative_int(
        payload.get("contradictions_considered"),
        field_name="contradictions_considered",
    )

    for field_name in _OPTIONAL_LIST_FIELDS:
        if field_name not in payload:
            continue
        normalized = _normalize_optional_string_list(payload[field_name], field_name=field_name)
        if normalized is None:
            raise ValueError(f"{field_name} must be omitted when empty.")
        if list(payload[field_name]) != normalized:
            raise ValueError(f"{field_name} must be sorted and de-duplicated when present.")

    _validate_manifest_path_contract(
        payload=payload,
        output_mode=output_mode,
        space_root=space_root,
    )


def _set_manifest_path_for_output_mode(
    *,
    payload: dict[str, Any],
    output_mode: str,
    space_root: Path,
) -> None:
    if output_mode == _OUTPUT_MODE_MARKDOWN:
        payload["manifest_path"] = None
        return
    if output_mode in _OUTPUT_MODES_WITH_MANIFEST:
        payload["manifest_path"] = str(
            canonical_query_manifest_path(
                space_root=space_root,
                query_id=payload["query_id"],
            )
        )
        return
    raise ValueError(f"Unsupported query output mode: {output_mode}")


def _validate_manifest_path_contract(
    *,
    payload: Mapping[str, Any],
    output_mode: str,
    space_root: Path,
) -> None:
    manifest_path = payload.get("manifest_path")
    if output_mode == _OUTPUT_MODE_MARKDOWN:
        if manifest_path is not None:
            raise ValueError("markdown output mode must not emit a manifest path.")
        return
    if output_mode not in _OUTPUT_MODES_WITH_MANIFEST:
        raise ValueError(f"Unsupported query output mode: {output_mode}")
    if not isinstance(manifest_path, str) or not manifest_path.strip():
        raise ValueError(f"{output_mode} output mode requires a manifest_path string.")
    expected = canonical_query_manifest_path(
        space_root=space_root,
        query_id=_require_non_empty_string(payload.get("query_id"), field_name="query_id"),
    )
    if Path(manifest_path).resolve() != expected:
        raise ValueError(
            "manifest_path must match canonical output contract for the query_id and space_root."
        )


def _require_non_empty_string(raw: Any, *, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return raw.strip()


def _require_non_negative_int(raw: Any, *, field_name: str) -> int:
    if not isinstance(raw, int):
        raise TypeError(f"{field_name} must be an integer.")
    if raw < 0:
        raise ValueError(f"{field_name} must be >= 0.")
    return raw


def _require_object(raw: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise TypeError(f"{field_name} must be an object.")
    return raw


def _require_array(raw: Any, *, field_name: str) -> list[Any]:
    if not isinstance(raw, list):
        raise TypeError(f"{field_name} must be an array.")
    return raw


def _require_string_list(raw: Any, *, field_name: str) -> list[str]:
    items = _require_array(raw, field_name=field_name)
    normalized: list[str] = []
    for item in items:
        normalized.append(_require_non_empty_string(item, field_name=field_name))
    return normalized


def _require_object_list(raw: Any, *, field_name: str) -> list[dict[str, Any]]:
    items = _require_array(raw, field_name=field_name)
    normalized: list[dict[str, Any]] = []
    for item in items:
        normalized.append(_require_object(item, field_name=field_name))
    return normalized


def _require_int_dict(raw: Any, *, field_name: str) -> dict[str, int]:
    obj = _require_object(raw, field_name=field_name)
    normalized: dict[str, int] = {}
    for key, value in obj.items():
        normalized_key = _require_non_empty_string(key, field_name=field_name)
        normalized_value = _require_non_negative_int(value, field_name=field_name)
        normalized[normalized_key] = normalized_value
    return normalized


def _require_object_int_keys(
    raw: Mapping[str, Any],
    *,
    field_name: str,
    required_keys: tuple[str, ...],
) -> None:
    for key in required_keys:
        if key not in raw:
            raise ValueError(f"{field_name} is missing required key: {key}")
        _require_non_negative_int(raw[key], field_name=f"{field_name}.{key}")


def _normalize_optional_string_list(raw: Any, *, field_name: str) -> list[str] | None:
    if raw is None:
        return None
    items = _require_string_list(raw, field_name=field_name)
    if not items:
        return None
    return sorted(dict.fromkeys(items))
