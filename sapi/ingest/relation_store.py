"""Relation persistence helpers with canonical ID and merge normalization rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


_UNDIRECTED_RELATION_TYPES: set[str] = {"contradictory", "similar"}
_DIRECTED_RELATION_TYPES: set[str] = {"supports", "derived_from", "falsifies"}
_ALLOWED_RELATION_TYPES: set[str] = _UNDIRECTED_RELATION_TYPES | _DIRECTED_RELATION_TYPES

_ALLOWED_STATUSES: set[str] = {
    "open",
    "resolved",
    "closed",  # semantic-output alias normalized to resolved
    "falsify",
    "not_falsify",
    "ambiguous",
}


def relation_file_id_from_relation_id(relation_id: str) -> str:
    if not isinstance(relation_id, str) or not relation_id.strip():
        raise ValueError("relation_id must be a non-empty string.")
    digest = hashlib.sha256(relation_id.encode("utf-8")).hexdigest()
    return f"rel-{digest}"


def canonical_relation_id(*, relation_type: str, src_claim_id: str, dst_claim_id: str) -> str:
    relation_type = _normalize_relation_type(relation_type)
    src_claim_id = _normalize_claim_id(src_claim_id, field_name="src_claim_id")
    dst_claim_id = _normalize_claim_id(dst_claim_id, field_name="dst_claim_id")

    if relation_type in _UNDIRECTED_RELATION_TYPES:
        low, high = sorted((src_claim_id, dst_claim_id))
        return f"{relation_type}:{low}|{high}"

    return f"{relation_type}:{src_claim_id}->{dst_claim_id}"


def write_relation(relation: dict[str, Any], space_root: Path) -> Path:
    normalized = normalize_relation_for_write(relation)
    relation_path = space_root / "relations" / f"{normalized['relation_file_id']}.json"
    relation_path.parent.mkdir(parents=True, exist_ok=True)

    if relation_path.is_file():
        existing = read_relation(relation_path)
        merged = merge_relation_records(existing=existing, incoming=normalized)
    else:
        merged = normalized

    relation_path.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n")
    return relation_path


def read_relation(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Relation file must contain a JSON object: {path}")
    relation_id = payload.get("relation_id")
    relation_file_id = payload.get("relation_file_id")
    if not isinstance(relation_id, str) or not isinstance(relation_file_id, str):
        raise ValueError(f"Relation record missing relation_id/relation_file_id: {path}")
    expected = relation_file_id_from_relation_id(relation_id)
    if relation_file_id != expected:
        raise ValueError(
            f"relation_file_id mismatch: stored={relation_file_id} expected={expected}"
        )
    return payload


def normalize_relation_for_write(relation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(relation, dict):
        raise TypeError("relation must be a dictionary.")

    relation_type = _normalize_relation_type(relation.get("relation_type"))
    src_claim_id = _normalize_claim_id(relation.get("src_claim_id"), field_name="src_claim_id")
    dst_claim_id = _normalize_claim_id(relation.get("dst_claim_id"), field_name="dst_claim_id")

    if relation_type in _UNDIRECTED_RELATION_TYPES:
        src_claim_id, dst_claim_id = sorted((src_claim_id, dst_claim_id))

    relation_id = canonical_relation_id(
        relation_type=relation_type,
        src_claim_id=src_claim_id,
        dst_claim_id=dst_claim_id,
    )
    relation_file_id = relation_file_id_from_relation_id(relation_id)
    _validate_provided_relation_identity(
        relation=relation,
        canonical_relation_id=relation_id,
        canonical_relation_file_id=relation_file_id,
    )

    normalized_status = _normalize_status(relation.get("status"))
    below_040_streak_raw = relation.get("below_040_streak", 0)
    if not isinstance(below_040_streak_raw, int) or below_040_streak_raw < 0:
        raise ValueError("below_040_streak must be a non-negative integer.")

    last_evaluated_run_id = relation.get("last_evaluated_run_id")
    if last_evaluated_run_id is not None and (
        not isinstance(last_evaluated_run_id, str) or not last_evaluated_run_id.strip()
    ):
        raise ValueError("last_evaluated_run_id must be null or non-empty string.")

    contradiction_confidence_band = relation.get("contradiction_confidence_band", "unknown")
    if not isinstance(contradiction_confidence_band, str) or not contradiction_confidence_band.strip():
        raise ValueError("contradiction_confidence_band must be a non-empty string.")

    normalized = dict(relation)
    normalized.update(
        {
            "relation_type": relation_type,
            "src_claim_id": src_claim_id,
            "dst_claim_id": dst_claim_id,
            "relation_id": relation_id,
            "relation_file_id": relation_file_id,
            "status": normalized_status,
            "below_040_streak": below_040_streak_raw,
            "last_evaluated_run_id": last_evaluated_run_id,
            "contradiction_confidence_band": contradiction_confidence_band,
        }
    )
    return normalized


def _validate_provided_relation_identity(
    *,
    relation: dict[str, Any],
    canonical_relation_id: str,
    canonical_relation_file_id: str,
) -> None:
    provided_relation_id = relation.get("relation_id")
    if provided_relation_id is not None:
        if not isinstance(provided_relation_id, str) or not provided_relation_id.strip():
            raise ValueError("relation_id must be a non-empty string when provided.")
        if provided_relation_id.strip() != canonical_relation_id:
            raise ValueError(
                "relation_id mismatch: provided value does not match canonical relation grammar."
            )

    provided_relation_file_id = relation.get("relation_file_id")
    if provided_relation_file_id is not None:
        if not isinstance(provided_relation_file_id, str) or not provided_relation_file_id.strip():
            raise ValueError("relation_file_id must be a non-empty string when provided.")
        if provided_relation_file_id.strip() != canonical_relation_file_id:
            raise ValueError(
                "relation_file_id mismatch: provided value does not match hash-derived storage key."
            )


def merge_relation_records(*, existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    existing_normalized = normalize_relation_for_write(existing)
    incoming_normalized = normalize_relation_for_write(incoming)
    if existing_normalized["relation_id"] != incoming_normalized["relation_id"]:
        raise ValueError("Cannot merge relation records with different canonical relation_id values.")

    merged = dict(existing_normalized)
    for key, value in incoming_normalized.items():
        if value is not None:
            merged[key] = value

    merged["status"] = _merge_status(
        existing_status=existing_normalized["status"],
        incoming_status=incoming_normalized["status"],
    )
    merged["below_040_streak"] = max(
        int(existing_normalized["below_040_streak"]),
        int(incoming_normalized["below_040_streak"]),
    )
    if incoming_normalized.get("last_evaluated_run_id") is None:
        merged["last_evaluated_run_id"] = existing_normalized.get("last_evaluated_run_id")
    return merged


def _normalize_relation_type(raw: Any) -> str:
    if not isinstance(raw, str):
        raise ValueError("relation_type must be a string.")
    relation_type = raw.strip()
    if relation_type not in _ALLOWED_RELATION_TYPES:
        raise ValueError(f"Unsupported relation_type: {relation_type}")
    return relation_type


def _normalize_claim_id(raw: Any, *, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return raw.strip()


def _normalize_status(raw: Any) -> str:
    if raw is None:
        return "open"
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("status must be null or a non-empty string.")
    status = raw.strip()
    if status not in _ALLOWED_STATUSES:
        raise ValueError(f"Unsupported relation status: {status}")
    if status == "closed":
        return "resolved"
    return status


def _merge_status(*, existing_status: str, incoming_status: str) -> str:
    if existing_status == "resolved" or incoming_status == "resolved":
        return "resolved"
    return incoming_status
