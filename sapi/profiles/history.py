"""Persona profile-history persistence and update semantics."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal


HistoryWriteStatus = Literal["generated", "updated", "reused"]

_HISTORY_SCHEMA_VERSION = "persona_profile_history_v1"
_ARGUMENTATIVE_POSITIONS = {"support", "challenge", "rebuttal", "synthesis"}


@dataclass(frozen=True)
class PersonaHistoryMetrics:
    comments_total: int
    unsupported_claim_rate: float
    retraction_rate: float
    forecast_accuracy: float

    def to_entry(self, *, as_of: str) -> dict[str, object]:
        return {
            "as_of": as_of,
            "comments_total": self.comments_total,
            "unsupported_claim_rate": round(self.unsupported_claim_rate, 4),
            "retraction_rate": round(self.retraction_rate, 4),
            "forecast_accuracy": round(self.forecast_accuracy, 4),
        }


@dataclass(frozen=True)
class PersonaHistoryUpdate:
    status: HistoryWriteStatus
    payload: dict[str, object]


def history_path_for_persona(*, space_root: Path, persona_id: str) -> Path:
    return space_root / "outputs" / "persona_profile_history" / f"{persona_id}.json"


def compute_persona_history_metrics(
    *,
    space_root: Path,
    persona_id: str,
) -> PersonaHistoryMetrics:
    comments = _collect_persona_comments(space_root=space_root, persona_id=persona_id)
    comments_total = len(comments)
    unsupported_count = 0
    for comment in comments:
        turn = comment.get("turn")
        if not isinstance(turn, dict):
            continue
        position = str(turn.get("position") or "").strip().lower()
        if position not in _ARGUMENTATIVE_POSITIONS:
            continue
        evidence_refs = turn.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            unsupported_count += 1
    unsupported_claim_rate = 0.0
    if comments_total > 0:
        unsupported_claim_rate = unsupported_count / comments_total
    # Deterministic default placeholders until richer accountability signals are added.
    retraction_rate = 0.0
    forecast_accuracy = 0.0 if comments_total == 0 else min(1.0, 0.5 + comments_total * 0.03)
    return PersonaHistoryMetrics(
        comments_total=comments_total,
        unsupported_claim_rate=unsupported_claim_rate,
        retraction_rate=retraction_rate,
        forecast_accuracy=forecast_accuracy,
    )


def apply_persona_history_update(
    *,
    current_payload: dict[str, object] | None,
    space_name: str,
    persona_id: str,
    metrics: PersonaHistoryMetrics,
    as_of_date: str,
) -> PersonaHistoryUpdate:
    payload = (
        _normalize_existing_history_payload(
            payload=current_payload,
            expected_space_name=space_name,
            expected_persona_id=persona_id,
        )
        if current_payload is not None
        else {
            "schema_version": _HISTORY_SCHEMA_VERSION,
            "space_name": space_name,
            "persona_id": persona_id,
            "entries": [],
        }
    )

    entries = payload["entries"]
    assert isinstance(entries, list)
    new_entry = metrics.to_entry(as_of=as_of_date)
    new_entry_non_date = _entry_non_date(new_entry)
    if not entries:
        entries.append(new_entry)
        return PersonaHistoryUpdate(status="generated", payload=payload)

    last_entry = entries[-1]
    assert isinstance(last_entry, dict)
    same_day = str(last_entry.get("as_of") or "").strip() == as_of_date
    last_non_date = _entry_non_date(last_entry)
    changed = new_entry_non_date != last_non_date

    if same_day:
        if changed:
            entries[-1] = new_entry
            return PersonaHistoryUpdate(status="updated", payload=payload)
        return PersonaHistoryUpdate(status="reused", payload=payload)

    if changed:
        entries.append(new_entry)
        return PersonaHistoryUpdate(status="updated", payload=payload)

    return PersonaHistoryUpdate(status="reused", payload=payload)


def read_history_payload(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    parsed = json.loads(path.read_text())
    if not isinstance(parsed, dict):
        raise ValueError(f"Persona history must be a JSON object: {path}")
    return parsed


def _collect_persona_comments(*, space_root: Path, persona_id: str) -> list[dict[str, Any]]:
    all_comments: list[dict[str, Any]] = []
    for path in _iter_comment_page_payloads(space_root):
        payload = json.loads(path.read_text())
        if not isinstance(payload, dict):
            continue
        comment_section = payload.get("comment_section")
        if not isinstance(comment_section, dict):
            continue
        rows = comment_section.get("comments")
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("persona_id") or "") != persona_id:
                continue
            all_comments.append(row)
    return all_comments


def _iter_comment_page_payloads(space_root: Path) -> list[Path]:
    paths: list[Path] = []
    paths.extend(sorted((space_root / "topics").glob("*.json")))
    paths.extend(sorted((space_root / "sources" / "records").glob("*.json")))
    paths.extend(sorted((space_root / "claims").glob("*.json")))
    return paths


def _normalize_existing_history_payload(
    *,
    payload: dict[str, object],
    expected_space_name: str,
    expected_persona_id: str,
) -> dict[str, object]:
    if str(payload.get("schema_version") or "") != _HISTORY_SCHEMA_VERSION:
        raise ValueError(
            "Persona history schema mismatch; expected persona_profile_history_v1."
        )
    if str(payload.get("space_name") or "") != expected_space_name:
        raise ValueError(
            "Persona history space_name mismatch with requested space."
        )
    if str(payload.get("persona_id") or "") != expected_persona_id:
        raise ValueError(
            "Persona history persona_id mismatch with requested persona."
        )
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Persona history entries must be a JSON array.")
    normalized_entries: list[dict[str, object]] = []
    for row in entries:
        if not isinstance(row, dict):
            raise ValueError("Persona history entries must be JSON objects.")
        normalized_entries.append(dict(row))
    return {
        "schema_version": _HISTORY_SCHEMA_VERSION,
        "space_name": expected_space_name,
        "persona_id": expected_persona_id,
        "entries": normalized_entries,
    }


def _entry_non_date(entry: dict[str, object]) -> dict[str, object]:
    return {
        "comments_total": int(entry.get("comments_total", 0)),
        "unsupported_claim_rate": round(float(entry.get("unsupported_claim_rate", 0.0)), 4),
        "retraction_rate": round(float(entry.get("retraction_rate", 0.0)), 4),
        "forecast_accuracy": round(float(entry.get("forecast_accuracy", 0.0)), 4),
    }
