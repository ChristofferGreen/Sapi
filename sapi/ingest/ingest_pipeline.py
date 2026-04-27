"""Ingest semantic-flow planning helpers for boundary-contract enforcement."""

from __future__ import annotations

from dataclasses import dataclass


_COMMENT_COUNT_MIN = 5
_COMMENT_COUNT_MAX = 50
_COMMENT_TARGET_PREFIXES: tuple[str, ...] = ("topic:", "source:", "claim:")


@dataclass(frozen=True)
class IngestSemanticExecutionPlan:
    """Canonical semantic flow ordering and invocation counts for one ingest run."""

    semantic_flows: list[str]
    semantic_flow_invocation_counts: dict[str, int]
    comment_enrichment_enabled: bool


def plan_ingest_semantic_execution(
    *,
    enable_comment_enrichment: bool = False,
    requested_comment_count: int | None = None,
    comment_target_page_refs: list[str] | None = None,
    include_source_revision_detection: bool = False,
) -> IngestSemanticExecutionPlan:
    """Build boundary-correct semantic flow metadata for ingest modes."""
    _validate_comment_enrichment_inputs(
        enable_comment_enrichment=enable_comment_enrichment,
        requested_comment_count=requested_comment_count,
        comment_target_page_refs=comment_target_page_refs,
    )

    semantic_flows: list[str] = []
    invocation_counts: dict[str, int] = {}
    if include_source_revision_detection:
        semantic_flows.append("source_revision_detection")
        invocation_counts["source_revision_detection"] = 1
    semantic_flows.extend(["ingest_extraction", "topic_generation"])
    invocation_counts.update({"ingest_extraction": 1, "topic_generation": 1})

    if enable_comment_enrichment:
        assert comment_target_page_refs is not None  # guarded in preflight validation
        semantic_flows.append("comment_section_generation")
        invocation_counts["comment_section_generation"] = len(comment_target_page_refs)

    return IngestSemanticExecutionPlan(
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=invocation_counts,
        comment_enrichment_enabled=enable_comment_enrichment,
    )


def _validate_comment_enrichment_inputs(
    *,
    enable_comment_enrichment: bool,
    requested_comment_count: int | None,
    comment_target_page_refs: list[str] | None,
) -> None:
    if not enable_comment_enrichment:
        if requested_comment_count is not None or comment_target_page_refs is not None:
            raise ValueError(
                "comment enrichment inputs require explicit opt-in (enable_comment_enrichment=True)."
            )
        return

    if requested_comment_count is None:
        raise ValueError("requested_comment_count is required when comment enrichment is enabled.")
    if not isinstance(requested_comment_count, int):
        raise TypeError("requested_comment_count must be an integer.")
    if requested_comment_count < _COMMENT_COUNT_MIN or requested_comment_count > _COMMENT_COUNT_MAX:
        raise ValueError(
            f"requested_comment_count must be in [{_COMMENT_COUNT_MIN}, {_COMMENT_COUNT_MAX}]."
        )

    if comment_target_page_refs is None or not comment_target_page_refs:
        raise ValueError("comment_target_page_refs must be a non-empty list when enrichment is enabled.")

    for page_ref in comment_target_page_refs:
        if not isinstance(page_ref, str) or not page_ref.strip():
            raise ValueError("comment_target_page_refs entries must be non-empty strings.")
        if not any(page_ref.startswith(prefix) for prefix in _COMMENT_TARGET_PREFIXES):
            raise ValueError(
                "comment_target_page_refs must target source/claim/topic pages."
            )
