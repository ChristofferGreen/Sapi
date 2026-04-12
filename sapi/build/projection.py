"""Deterministic canonical-JSON projection helpers for site build."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class ProjectionContractError(ValueError):
    """Raised when canonical projection input contracts are violated."""


@dataclass(frozen=True)
class SpaceProjection:
    """Canonical projection payload extracted from one space root."""

    sources: list[dict[str, Any]]
    topics: list[dict[str, Any]]


def load_space_projection(space_root: Path) -> SpaceProjection:
    """Load deterministic build input from canonical source/topic JSON artifacts."""
    sources = _load_source_records(space_root)
    topics = _load_topic_records(space_root)
    _validate_topic_links(sources=sources, topics=topics)
    return SpaceProjection(sources=sources, topics=topics)


def _load_source_records(space_root: Path) -> list[dict[str, Any]]:
    records_dir = space_root / "sources" / "records"
    if not records_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for source_path in sorted(records_dir.glob("source-*.json")):
        payload = _read_json_object(source_path)
        source_id = payload.get("source_id")
        title = payload.get("title")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ProjectionContractError(f"{source_path}: source_id must be a non-empty string.")
        if not isinstance(title, str) or not title.strip():
            raise ProjectionContractError(f"{source_path}: title must be a non-empty string.")
        records.append(payload)
    return records


def _load_topic_records(space_root: Path) -> list[dict[str, Any]]:
    topics_dir = space_root / "topics"
    if not topics_dir.exists():
        return []
    topics: list[dict[str, Any]] = []
    for topic_path in sorted(topics_dir.glob("topic-*.json")):
        payload = _read_json_object(topic_path)
        topic_id = payload.get("topic_id")
        title = payload.get("title")
        sections = payload.get("sections")
        source_ids = payload.get("source_ids")
        if not isinstance(topic_id, str) or not topic_id.strip():
            raise ProjectionContractError(f"{topic_path}: topic_id must be a non-empty string.")
        if not isinstance(title, str) or not title.strip():
            raise ProjectionContractError(f"{topic_path}: title must be a non-empty string.")
        if not isinstance(sections, list):
            raise ProjectionContractError(f"{topic_path}: sections must be an array.")
        if not isinstance(source_ids, list):
            raise ProjectionContractError(f"{topic_path}: source_ids must be an array.")
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                raise ProjectionContractError(f"{topic_path}: sections[{index}] must be an object.")
            heading = section.get("heading")
            body = section.get("body")
            if not isinstance(heading, str) or not heading.strip():
                raise ProjectionContractError(
                    f"{topic_path}: sections[{index}].heading must be a non-empty string."
                )
            if not isinstance(body, str) or not body.strip():
                raise ProjectionContractError(
                    f"{topic_path}: sections[{index}].body must be a non-empty string."
                )
        topics.append(payload)
    return topics


def _validate_topic_links(*, sources: list[dict[str, Any]], topics: list[dict[str, Any]]) -> None:
    known_source_ids = {record["source_id"] for record in sources}
    for topic in topics:
        topic_id = topic["topic_id"]
        for index, source_id in enumerate(topic.get("source_ids", [])):
            if not isinstance(source_id, str) or not source_id.strip():
                raise ProjectionContractError(
                    f"{topic_id}: source_ids[{index}] must be a non-empty string."
                )
            if source_id not in known_source_ids:
                raise ProjectionContractError(
                    f"{topic_id}: unresolved source link `{source_id}` referenced by topic source_ids."
                )


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ProjectionContractError(f"{path}: invalid JSON ({exc}).") from exc
    if not isinstance(payload, dict):
        raise ProjectionContractError(f"{path}: payload must be a JSON object.")
    return payload
