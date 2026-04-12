"""Lint severity vocabulary and canonical check-severity mappings."""

from __future__ import annotations

from typing import Literal


LintSeverity = Literal["error", "warning", "info"]


_ALLOWED_SEVERITIES: set[str] = {"error", "warning", "info"}

# High-signal examples from docs/design.md Section 5.8.
_CHECK_SEVERITY_BY_ID: dict[str, LintSeverity] = {
    "missing_claim_annotation": "error",
    "missing_claim_reference": "error",
    "missing_required_canonical_field": "error",
    "invalid_canonical_id_format": "error",
    "final_disputed_contradiction": "error",
    "missing_publication_date": "warning",
    "weak_support_single_source": "warning",
    "sparse_backlinks": "warning",
    "structural_hole": "warning",
    "high_ambiguous_match_volume": "warning",
    "ingest_source_suggestion": "info",
    "style_organization_suggestion": "info",
}


def normalize_lint_severity(value: str) -> LintSeverity:
    normalized = value.strip().lower()
    if normalized not in _ALLOWED_SEVERITIES:
        raise ValueError(f"Unsupported lint severity: {value!r}")
    return normalized  # type: ignore[return-value]


def severity_for_check(check_id: str) -> LintSeverity:
    try:
        return _CHECK_SEVERITY_BY_ID[check_id]
    except KeyError as exc:
        raise ValueError(
            f"Unknown lint check id {check_id!r}; provide an explicit severity."
        ) from exc
