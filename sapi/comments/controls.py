"""Discussion-controls loading and precedence rules for comment generation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


_CANONICAL_SCHEMA_VERSION = "comment_section_discussion_controls_v1"
_SCHEMA_ALIASES = {_CANONICAL_SCHEMA_VERSION, "persona_discussion_controls_v1"}
_CONTROL_KEY_ALIASES = {
    "enabled": "enabled",
    "persona_discussion_enabled": "enabled",
    "roster": "roster",
    "persona_discussion_roster": "roster",
    "max_turns": "max_turns",
    "persona_discussion_max_turns": "max_turns",
    "reply_chance": "reply_chance",
    "persona_discussion_reply_chance": "reply_chance",
    "max_depth": "max_depth",
    "persona_discussion_max_depth": "max_depth",
}
_CANONICAL_CONTROL_KEYS = {"enabled", "roster", "max_turns", "reply_chance", "max_depth"}


@dataclass(frozen=True)
class SiteDiscussionControls:
    defaults: dict[str, Any]
    pages: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class PageDiscussionControlsResolution:
    effective_controls: dict[str, Any]
    canonical_page_controls: dict[str, Any] | None
    legacy_frontmatter_controls: dict[str, Any] | None
    canonical_page_controls_to_write: dict[str, Any] | None


def load_site_discussion_controls(*, site_path: Path) -> SiteDiscussionControls:
    controls_path = site_path / "config" / "discussion_controls.json"
    if not controls_path.is_file():
        return SiteDiscussionControls(defaults={}, pages={})
    try:
        payload = json.loads(controls_path.read_text())
    except json.JSONDecodeError:
        return SiteDiscussionControls(defaults={}, pages={})
    if not isinstance(payload, dict):
        return SiteDiscussionControls(defaults={}, pages={})
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or schema_version not in _SCHEMA_ALIASES:
        return SiteDiscussionControls(defaults={}, pages={})

    defaults = _normalize_controls(payload.get("defaults"))
    pages_raw = payload.get("pages")
    pages: dict[str, dict[str, Any]] = {}
    if isinstance(pages_raw, dict):
        for raw_page_ref, raw_page_controls in pages_raw.items():
            if not isinstance(raw_page_ref, str):
                continue
            page_ref = raw_page_ref.strip()
            if not page_ref:
                continue
            page_controls = _normalize_controls(raw_page_controls)
            if page_controls:
                pages[page_ref] = page_controls
    return SiteDiscussionControls(defaults=defaults, pages=pages)


def resolve_page_discussion_controls(
    *,
    site_controls: SiteDiscussionControls,
    page_ref: str,
    page_payload: dict[str, Any],
) -> PageDiscussionControlsResolution:
    defaults = dict(site_controls.defaults)
    page_overrides = dict(site_controls.pages.get(page_ref, {}))
    canonical_page_controls = _extract_canonical_page_controls(page_payload)
    legacy_frontmatter_controls = _extract_legacy_frontmatter_controls(page_payload)

    effective_controls = dict(defaults)
    effective_controls.update(page_overrides)
    if canonical_page_controls is not None:
        effective_controls.update(canonical_page_controls)
        return PageDiscussionControlsResolution(
            effective_controls=effective_controls,
            canonical_page_controls=canonical_page_controls,
            legacy_frontmatter_controls=legacy_frontmatter_controls,
            canonical_page_controls_to_write=None,
        )

    if legacy_frontmatter_controls:
        effective_controls.update(legacy_frontmatter_controls)
        return PageDiscussionControlsResolution(
            effective_controls=effective_controls,
            canonical_page_controls=None,
            legacy_frontmatter_controls=legacy_frontmatter_controls,
            canonical_page_controls_to_write=legacy_frontmatter_controls,
        )

    return PageDiscussionControlsResolution(
        effective_controls=effective_controls,
        canonical_page_controls=None,
        legacy_frontmatter_controls=legacy_frontmatter_controls,
        canonical_page_controls_to_write=None,
    )


def apply_canonical_page_discussion_controls(
    *,
    page_payload: dict[str, Any],
    canonical_page_controls: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(page_payload)
    updated["discussion_controls"] = dict(canonical_page_controls)
    return updated


def _extract_canonical_page_controls(page_payload: dict[str, Any]) -> dict[str, Any] | None:
    raw = page_payload.get("discussion_controls")
    if not isinstance(raw, dict):
        return None
    normalized = _normalize_controls(raw)
    return normalized if normalized else {}


def _extract_legacy_frontmatter_controls(page_payload: dict[str, Any]) -> dict[str, Any] | None:
    raw_frontmatter = page_payload.get("frontmatter")
    if not isinstance(raw_frontmatter, dict):
        return None
    normalized = _normalize_controls(raw_frontmatter)
    return normalized if normalized else None


def _normalize_controls(raw_controls: Any) -> dict[str, Any]:
    if not isinstance(raw_controls, dict):
        return {}
    normalized: dict[str, Any] = {}
    for raw_key, raw_value in raw_controls.items():
        if not isinstance(raw_key, str):
            continue
        canonical_key = _CONTROL_KEY_ALIASES.get(raw_key)
        if canonical_key is None or canonical_key not in _CANONICAL_CONTROL_KEYS:
            continue
        normalized_value = _normalize_control_value(canonical_key=canonical_key, raw_value=raw_value)
        if normalized_value is None:
            continue
        normalized[canonical_key] = normalized_value
    return normalized


def _normalize_control_value(*, canonical_key: str, raw_value: Any) -> Any | None:
    if canonical_key == "enabled":
        return raw_value if isinstance(raw_value, bool) else None
    if canonical_key == "roster":
        if not isinstance(raw_value, list):
            return None
        roster = [value.strip() for value in raw_value if isinstance(value, str) and value.strip()]
        return roster if roster else None
    if canonical_key == "max_turns":
        if isinstance(raw_value, int) and not isinstance(raw_value, bool) and raw_value > 0:
            return raw_value
        return None
    if canonical_key == "reply_chance":
        if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
            chance = float(raw_value)
            if 0.0 <= chance <= 1.0:
                return chance
        return None
    if canonical_key == "max_depth":
        if isinstance(raw_value, int) and not isinstance(raw_value, bool) and raw_value >= 0:
            return raw_value
        return None
    return None
