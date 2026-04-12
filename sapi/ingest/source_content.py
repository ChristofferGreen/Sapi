"""Source title/date resolution contracts for ingest preflight."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class SourceDateResolution:
    """Normalized publication-date resolution output for ingest contract writes."""

    publication_date: str | None
    source_date_inference: dict[str, str | None]
    warnings: list[dict[str, str]]


def resolve_source_title(
    *,
    source_title_override: str | None,
    source_metadata_title: str | None,
    in_source_title_line: str | None,
    source_locator: str | None,
) -> str:
    """Resolve source title using the five-step contract priority from design.md."""
    candidates = (
        _normalize_non_empty(source_title_override),
        _normalize_non_empty(source_metadata_title),
        _normalize_non_empty(in_source_title_line),
        _title_from_locator(source_locator),
        "Untitled Source",
    )
    for candidate in candidates:
        if candidate is not None:
            return candidate
    raise AssertionError("Unreachable title resolution branch.")


def resolve_publication_date(
    *,
    explicit_source_date: str | None,
    inferred_source_date: str | None,
    require_source_date: bool,
    inference_rationale: str | None = None,
) -> SourceDateResolution:
    """Resolve publication date and source_date_inference under strict-date policy."""
    explicit = _parse_iso_date_or_none(explicit_source_date, field_name="explicit_source_date")
    inferred = _parse_iso_date_or_none(inferred_source_date, field_name="inferred_source_date")

    if explicit is not None:
        return SourceDateResolution(
            publication_date=explicit,
            source_date_inference={
                "date": explicit,
                "origin": "explicit",
                "confidence": "high",
                "rationale": _normalize_non_empty(inference_rationale),
            },
            warnings=[],
        )

    if inferred is not None:
        return SourceDateResolution(
            publication_date=inferred,
            source_date_inference={
                "date": inferred,
                "origin": "inferred",
                "confidence": "medium",
                "rationale": _normalize_non_empty(inference_rationale),
            },
            warnings=[],
        )

    if require_source_date:
        raise ValueError(
            "Publication date could not be resolved while strict-date mode (`--require-source-date`) is enabled."
        )

    return SourceDateResolution(
        publication_date=None,
        source_date_inference={
            "date": None,
            "origin": "unknown",
            "confidence": "unknown",
            "rationale": _normalize_non_empty(inference_rationale),
        },
        warnings=[
            {
                "code": "missing_publication_date",
                "message": "Publication date could not be resolved; continuing with date=null.",
            }
        ],
    )


def _title_from_locator(locator: str | None) -> str | None:
    normalized = _normalize_non_empty(locator)
    if normalized is None:
        return None

    parsed = urlparse(normalized)
    if parsed.scheme and parsed.netloc:
        leaf = parsed.path.rsplit("/", 1)[-1]
    else:
        leaf = Path(normalized).name

    leaf = unquote(leaf).strip()
    if not leaf:
        return None
    return _normalize_non_empty(Path(leaf).stem)


def _normalize_non_empty(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped


def _parse_iso_date_or_none(value: str | None, *, field_name: str) -> str | None:
    normalized = _normalize_non_empty(value)
    if normalized is None:
        return None
    try:
        parsed = date.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO date (`YYYY-MM-DD`).") from exc
    return parsed.isoformat()
