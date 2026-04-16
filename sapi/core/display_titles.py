"""Display-title normalization and fallback rules for source UI surfaces."""

from __future__ import annotations

import re
from typing import Iterable

_SPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"(https?://|www\.)", re.IGNORECASE)
_FILE_SUFFIX_RE = re.compile(r"\.(pdf|docx?|txt|md|markdown)\s*$", re.IGNORECASE)
_SOURCE_ID_RE = re.compile(r"^source-[a-z0-9-]+--[0-9a-f]{12,}$")
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'’/-]*")
def resolve_display_title(*, candidates: Iterable[object], fallback: object) -> str:
    """Resolve a source display title from prioritized candidates.

    Resolution uses two passes:
    1. strict quality gates for post-style UI titles
    2. relaxed compatibility gates for short/legacy title fields
    """
    candidate_list = list(candidates)
    for candidate in candidate_list:
        normalized = normalize_display_title_strict(candidate)
        if normalized is not None:
            return normalized

    for candidate in candidate_list:
        normalized = normalize_display_title(candidate)
        if normalized is not None:
            return normalized

    fallback_normalized = normalize_display_title(fallback)
    if fallback_normalized is not None:
        return fallback_normalized

    return "Untitled Source"


def normalize_display_title_strict(raw: object) -> str | None:
    """Normalize one display-title candidate under strict UI quality gates."""
    candidate = _normalize_raw_text(raw)
    if candidate is None:
        return None
    words = _WORD_RE.findall(candidate)
    if len(words) < 2 or len(words) > 16:
        return None
    if len(candidate) < 12 or len(candidate) > 120:
        return None
    if _looks_slugish(raw=raw, normalized=candidate):
        return None
    return candidate


def normalize_display_title(raw: object) -> str | None:
    """Normalize one display-title candidate with relaxed compatibility gates."""
    candidate = _normalize_raw_text(raw)
    if candidate is None:
        return None
    words = _WORD_RE.findall(candidate)
    if len(words) < 2:
        return None
    if len(candidate) < 4 or len(candidate) > 120:
        return None
    return candidate


def _normalize_raw_text(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    candidate = _SPACE_RE.sub(" ", raw).strip()
    if not candidate:
        return None
    candidate = candidate.strip("\"'`“”‘’")
    candidate = _FILE_SUFFIX_RE.sub("", candidate).strip(" -_:;,.")
    candidate = candidate.replace("_", " ")
    candidate = _SPACE_RE.sub(" ", candidate).strip()
    if not candidate:
        return None
    if _URL_RE.search(candidate):
        return None
    if _SOURCE_ID_RE.fullmatch(candidate.lower()):
        return None
    return candidate


def _looks_slugish(*, raw: object, normalized: str) -> bool:
    lowered = normalized.lower()
    has_year_or_numeric_fragment = bool(re.search(r"\b\d{2,}\b", lowered))
    if not has_year_or_numeric_fragment:
        return False
    if not isinstance(raw, str):
        return False
    raw_lowered = raw.strip().lower()
    has_slug_separator_shape = "_" in raw_lowered or raw_lowered.count("-") >= 2
    if has_slug_separator_shape and normalized == lowered:
        return True
    return False

