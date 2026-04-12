"""Persona-profile pipeline helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SelectedPersona:
    persona_id: str
    row: dict[str, Any]


def select_personas_for_profile_generation(
    *,
    persona_catalog: list[dict[str, Any]],
    requested_persona_ids: list[str],
) -> list[SelectedPersona]:
    if not persona_catalog:
        fallback_ids = (
            _dedupe_preserving_order(requested_persona_ids)
            if requested_persona_ids
            else ["commenter-1", "commenter-2", "commenter-3", "commenter-4", "commenter-5"]
        )
        return [
            SelectedPersona(
                persona_id=persona_id,
                row={
                    "persona_id": persona_id,
                    "display_name": persona_id,
                    "profile_image_path": None,
                    "prompt_fields": {"argument_style": "direct"},
                    "interests": [],
                },
            )
            for persona_id in fallback_ids
        ]

    rows_by_persona_id = {
        str(row["persona_id"]): row
        for row in persona_catalog
    }
    if requested_persona_ids:
        ordered_ids = _dedupe_preserving_order(requested_persona_ids)
        unknown = sorted(
            persona_id
            for persona_id in ordered_ids
            if persona_id not in rows_by_persona_id
        )
        if unknown:
            raise ValueError(
                "Unknown persona_id values requested via --persona-id: " + ", ".join(unknown)
            )
        return [
            SelectedPersona(persona_id=persona_id, row=dict(rows_by_persona_id[persona_id]))
            for persona_id in ordered_ids
        ]
    return [
        SelectedPersona(persona_id=str(row["persona_id"]), row=dict(row))
        for row in persona_catalog
    ]


def validate_profile_semantic_payload(
    *,
    payload: dict[str, Any],
    expected_persona_id: str,
    expected_space_name: str,
) -> dict[str, Any]:
    semantic_persona_id = str(payload.get("persona_id") or "").strip()
    semantic_space_name = str(payload.get("space_name") or "").strip()
    if semantic_persona_id != expected_persona_id:
        raise ValueError(
            "persona_profile_generation semantic payload persona_id mismatch: "
            f"expected {expected_persona_id!r}, got {semantic_persona_id!r}."
        )
    if semantic_space_name != expected_space_name:
        raise ValueError(
            "persona_profile_generation semantic payload space_name mismatch: "
            f"expected {expected_space_name!r}, got {semantic_space_name!r}."
        )
    return payload


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        deduped.append(normalized)
        seen.add(normalized)
    return deduped
