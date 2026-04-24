"""Run-envelope models and canonical run-record writer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Literal

from sapi.contracts.ids import RFC3339_UTC_RE


SemanticFlowKey = Literal[
    "ingest_extraction",
    "topic_generation",
    "query_synthesis",
    "comment_section_generation",
    "persona_profile_generation",
    "space_overview_generation",
]

PipelineFlowKey = Literal[
    "ingest_pipeline",
    "query_pipeline",
    "comment_section_pipeline",
    "persona_profile_pipeline",
    "overview_pipeline",
]

RunStatus = Literal["pending", "success", "success_with_warnings", "failed", "aborted"]

_SEMANTIC_FLOW_KEYS: set[str] = {
    "ingest_extraction",
    "topic_generation",
    "query_synthesis",
    "comment_section_generation",
    "persona_profile_generation",
    "space_overview_generation",
}

_REQUIRED_BASE_FRONTMATTER_KEYS: tuple[str, ...] = (
    "run_id",
    "flow_key",
    "semantic_flows",
    "semantic_flow_invocation_counts",
    "status",
    "started_at",
    "completed_at",
    "model_fingerprint",
    "provider_fingerprint",
    "reasoning_effort",
    "execution_mode",
    "llm_attempt_count",
    "lint_error_count",
    "lint_warning_count",
    "lint_info_count",
    "toolchain_versions",
)

_REQUIRED_RUN_MD_SECTIONS: tuple[str, ...] = (
    "Summary",
    "Changes",
    "Lint Summary",
    "Errors",
)


@dataclass
class RunEnvelopeBase:
    run_id: str
    flow_key: PipelineFlowKey
    semantic_flows: list[SemanticFlowKey]
    semantic_flow_invocation_counts: dict[SemanticFlowKey, int]
    status: RunStatus
    started_at: str
    completed_at: str | None
    model_fingerprint: str
    provider_fingerprint: str
    reasoning_effort: str
    execution_mode: str
    llm_attempt_count: int
    lint_error_count: int
    lint_warning_count: int
    lint_info_count: int
    toolchain_versions: dict[str, str]


@dataclass
class IngestRunFields:
    ingest_scope: str
    source_ids: list[str]
    parent_run_id: str | None
    claims_changed: int
    relations_changed: int
    topic_pages_changed: int
    build_deferred: bool
    deferred_build_reason: str | None
    force_mode: bool
    rollback_skipped: bool


@dataclass
class QueryRunFields:
    query_id: str
    mode: str
    scope: str
    claims_used: int
    sources_used: int
    contradictions_considered: int
    manifest_path: str | None


@dataclass
class CommentRunFields:
    target_page_refs: list[str]
    comment_user_filters: list[str]
    requested_count: int
    comments_added: int
    adjudication: dict[str, object]
    generation_isolation: dict[str, object]
    evidence_mode: str
    evidence_snapshot_path: str | None


@dataclass
class PersonaProfileRunFields:
    persona_ids: list[str]
    history_generated: int
    history_updated: int
    history_reused: int
    pages_changed: int


@dataclass
class OverviewRunFields:
    overview_id: str
    scope_kind: str
    scope_name: str
    source_records_used: int
    claims_used: int
    relations_used: int
    topics_used: int
    article_path: str | None


FlowSpecificFields = (
    IngestRunFields | QueryRunFields | CommentRunFields | PersonaProfileRunFields | OverviewRunFields
)


def write_run_record(
    *,
    space_root: Path,
    base: RunEnvelopeBase,
    flow_fields: FlowSpecificFields,
    summary: str = "",
    changes: str = "",
    lint_summary: str = "",
    errors: str = "",
) -> Path:
    """Write canonical run markdown under `<space_root>/runs/<run_id>/run.md`."""
    _validate_base_fields(base)
    _validate_semantic_flow_fields(base)
    _validate_flow_fields_type(base.flow_key, flow_fields)

    run_md_path = run_record_path(space_root=space_root, run_id=base.run_id)
    run_md_path.parent.mkdir(parents=True, exist_ok=True)

    frontmatter = {
        **asdict(base),
        **asdict(flow_fields),
    }
    markdown = _render_frontmatter(frontmatter) + _render_required_sections(
        summary=summary,
        changes=changes,
        lint_summary=lint_summary,
        errors=errors,
    )
    run_md_path.write_text(markdown)
    return run_md_path


def run_record_path(*, space_root: Path, run_id: str) -> Path:
    """Return canonical run metadata path."""
    return space_root / "runs" / run_id / "run.md"


def _validate_semantic_flow_fields(base: RunEnvelopeBase) -> None:
    if len(base.semantic_flows) != len(dict.fromkeys(base.semantic_flows)):
        raise ValueError("semantic_flows must be ordered-unique.")

    for flow_key in base.semantic_flows:
        if flow_key not in _SEMANTIC_FLOW_KEYS:
            raise ValueError(f"Unknown semantic flow key in semantic_flows: {flow_key}")

    for flow_key, count in base.semantic_flow_invocation_counts.items():
        if flow_key not in _SEMANTIC_FLOW_KEYS:
            raise ValueError(f"Unknown semantic flow key in invocation counts: {flow_key}")
        if count <= 0:
            raise ValueError(f"Invocation count must be positive for {flow_key}.")

    missing = [flow for flow in base.semantic_flows if flow not in base.semantic_flow_invocation_counts]
    if missing:
        raise ValueError(
            "semantic_flow_invocation_counts must include every semantic flow in semantic_flows: "
            + ", ".join(missing)
        )

    extras = [flow for flow in base.semantic_flow_invocation_counts if flow not in base.semantic_flows]
    if extras:
        raise ValueError(
            "semantic_flow_invocation_counts keys must be represented in semantic_flows: "
            + ", ".join(extras)
        )


def _validate_flow_fields_type(flow_key: PipelineFlowKey, flow_fields: FlowSpecificFields) -> None:
    expected_types: dict[PipelineFlowKey, type[FlowSpecificFields]] = {
        "ingest_pipeline": IngestRunFields,
        "query_pipeline": QueryRunFields,
        "comment_section_pipeline": CommentRunFields,
        "persona_profile_pipeline": PersonaProfileRunFields,
        "overview_pipeline": OverviewRunFields,
    }
    expected = expected_types[flow_key]
    if not isinstance(flow_fields, expected):
        raise TypeError(f"flow_key={flow_key} requires {expected.__name__} extension fields.")


def _render_frontmatter(frontmatter: dict[str, object]) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value, ensure_ascii=True)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _render_required_sections(
    *,
    summary: str,
    changes: str,
    lint_summary: str,
    errors: str,
) -> str:
    section_bodies: dict[str, str] = {
        "Summary": summary,
        "Changes": changes,
        "Lint Summary": lint_summary,
        "Errors": errors,
    }
    chunks: list[str] = []
    for title in _REQUIRED_RUN_MD_SECTIONS:
        body = section_bodies[title]
        body_text = body.strip() or "(none)"
        chunks.append(f"## {title}\n{body_text}\n")
    return "\n".join(chunks)


def _validate_base_fields(base: RunEnvelopeBase) -> None:
    frontmatter = asdict(base)
    missing = [key for key in _REQUIRED_BASE_FRONTMATTER_KEYS if key not in frontmatter]
    if missing:
        raise ValueError(
            "Base run frontmatter missing required fields: " + ", ".join(missing)
        )

    _require_non_empty_string(base.run_id, "run_id")
    _require_non_empty_string(base.flow_key, "flow_key")
    _require_non_empty_string(base.status, "status")
    _require_rfc3339_utc(base.started_at, "started_at")
    _require_non_empty_string(base.model_fingerprint, "model_fingerprint")
    _require_non_empty_string(base.provider_fingerprint, "provider_fingerprint")
    _require_non_empty_string(base.reasoning_effort, "reasoning_effort")
    _require_non_empty_string(base.execution_mode, "execution_mode")
    if base.completed_at is not None:
        _require_rfc3339_utc(base.completed_at, "completed_at")

    _require_non_negative_int(base.llm_attempt_count, "llm_attempt_count")
    # Chosen implementation-wide policy for flows without lint/build: always write integer totals (zero default).
    _require_non_negative_int(base.lint_error_count, "lint_error_count")
    _require_non_negative_int(base.lint_warning_count, "lint_warning_count")
    _require_non_negative_int(base.lint_info_count, "lint_info_count")

    if not isinstance(base.toolchain_versions, dict):
        raise TypeError("toolchain_versions must be a string->string map.")
    for key, value in base.toolchain_versions.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("toolchain_versions must be a string->string map.")


def _require_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _require_non_negative_int(value: object, field_name: str) -> None:
    if not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer.")
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0.")


def _require_rfc3339_utc(value: object, field_name: str) -> None:
    _require_non_empty_string(value, field_name)
    assert isinstance(value, str)
    if not RFC3339_UTC_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be RFC3339 UTC with trailing Z.")
