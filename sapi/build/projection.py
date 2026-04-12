"""Deterministic canonical-JSON projection helpers for site build."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from sapi.build.topic_lifecycle import resolve_topic_lifecycle
from sapi.lint.lint_engine import LintIssue


class ProjectionContractError(ValueError):
    """Raised when canonical projection input contracts are violated."""


@dataclass(frozen=True)
class SpaceProjection:
    """Canonical projection payload extracted from one space root."""

    sources: list[dict[str, Any]]
    topics: list[dict[str, Any]]
    lint_issues: list[LintIssue]


def load_space_projection(space_root: Path) -> SpaceProjection:
    """Load deterministic build input from canonical source/topic JSON artifacts."""
    sources = _load_source_records(space_root)
    topics = _load_topic_records(space_root)
    lint_issues = _resolve_pinned_parent_links(space_root=space_root, topics=topics)
    lint_issues.extend(_resolve_topic_lifecycle_states(topics=topics))
    _validate_topic_links(sources=sources, topics=topics)
    return SpaceProjection(sources=sources, topics=topics, lint_issues=lint_issues)


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
        pinned_parent_ref = payload.get("pinned_parent_ref")
        if pinned_parent_ref is not None:
            if not isinstance(pinned_parent_ref, dict):
                raise ProjectionContractError(
                    f"{topic_path}: pinned_parent_ref must be an object when present."
                )
            parent_space = pinned_parent_ref.get("space_name")
            parent_topic_id = pinned_parent_ref.get("topic_id")
            if not isinstance(parent_space, str) or not parent_space.strip():
                raise ProjectionContractError(
                    f"{topic_path}: pinned_parent_ref.space_name must be a non-empty string."
                )
            if not isinstance(parent_topic_id, str) or not parent_topic_id.strip():
                raise ProjectionContractError(
                    f"{topic_path}: pinned_parent_ref.topic_id must be a non-empty string."
                )
            payload["pinned_parent_ref"] = {
                "space_name": parent_space.strip(),
                "topic_id": parent_topic_id.strip(),
            }
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


def _resolve_pinned_parent_links(*, space_root: Path, topics: list[dict[str, Any]]) -> list[LintIssue]:
    pinned_entries = _load_import_lock_entries(space_root)
    lint_issues: list[LintIssue] = []
    for topic in topics:
        topic_id = topic["topic_id"]
        pinned_parent_ref = topic.get("pinned_parent_ref")
        if not isinstance(pinned_parent_ref, dict):
            continue
        parent_space_name = str(pinned_parent_ref["space_name"])
        parent_topic_id = str(pinned_parent_ref["topic_id"])
        match = pinned_entries.get((parent_space_name, parent_topic_id))
        if match is None:
            topic["pinned_parent_link"] = {
                "resolved": False,
                "space_name": parent_space_name,
                "topic_id": parent_topic_id,
            }
            lint_issues.append(
                LintIssue(
                    check_id="unresolved_pinned_parent_link",
                    severity="error",
                    message=(
                        f"{topic_id}: unresolved pinned parent link `{parent_space_name}/{parent_topic_id}` "
                        "not found in imports.lock.md snapshot entries."
                    ),
                    path=f"topics/{topic_id}.json",
                )
            )
            continue
        topic["pinned_parent_link"] = {
            "resolved": True,
            "space_name": parent_space_name,
            "topic_id": parent_topic_id,
            "parent_space_name": match["parent_space_name"],
            "parent_snapshot": match["parent_snapshot"],
            "parent_site_base_url": match["parent_site_base_url"],
        }
    return lint_issues


def _resolve_topic_lifecycle_states(*, topics: list[dict[str, Any]]) -> list[LintIssue]:
    lint_issues: list[LintIssue] = []
    for topic in topics:
        topic_id = str(topic["topic_id"])
        try:
            resolution = resolve_topic_lifecycle(topic=topic, topic_id=topic_id)
        except ValueError as exc:
            raise ProjectionContractError(str(exc)) from exc
        topic["lifecycle_declared_state"] = resolution.declared_state
        topic["lifecycle_effective_state"] = resolution.effective_state
        topic["lifecycle_auto_transition"] = resolution.auto_transition
        lint_issues.extend(resolution.lint_issues)
    return lint_issues


def _load_import_lock_entries(space_root: Path) -> dict[tuple[str, str], dict[str, str]]:
    lock_path = space_root / "imports.lock.md"
    if not lock_path.is_file():
        return {}

    match = re.search(
        r"```json\s*(\{.*?\})\s*```",
        lock_path.read_text(),
        flags=re.DOTALL,
    )
    if match is None:
        return {}

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ProjectionContractError(f"{lock_path}: invalid JSON imports lock block ({exc}).") from exc
    if not isinstance(payload, dict):
        raise ProjectionContractError(f"{lock_path}: imports lock block must be a JSON object.")

    entries = payload.get("imports")
    if not isinstance(entries, list):
        raise ProjectionContractError(f"{lock_path}: imports lock JSON block must include an imports[] array.")

    resolved: dict[tuple[str, str], dict[str, str]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ProjectionContractError(
                f"{lock_path}: imports[{index}] must be a JSON object."
            )
        parent_space_name = entry.get("parent_space_name")
        parent_topic_id = entry.get("parent_topic_id")
        parent_snapshot = entry.get("parent_snapshot")
        parent_site_base_url = entry.get("parent_site_base_url")
        if not isinstance(parent_space_name, str) or not parent_space_name.strip():
            raise ProjectionContractError(
                f"{lock_path}: imports[{index}].parent_space_name must be a non-empty string."
            )
        if not isinstance(parent_topic_id, str) or not parent_topic_id.strip():
            raise ProjectionContractError(
                f"{lock_path}: imports[{index}].parent_topic_id must be a non-empty string."
            )
        if not isinstance(parent_snapshot, str) or not parent_snapshot.strip():
            raise ProjectionContractError(
                f"{lock_path}: imports[{index}].parent_snapshot must be a non-empty string."
            )
        if not isinstance(parent_site_base_url, str) or not parent_site_base_url.strip():
            raise ProjectionContractError(
                f"{lock_path}: imports[{index}].parent_site_base_url must be a non-empty string."
            )
        key = (parent_space_name.strip(), parent_topic_id.strip())
        if key in resolved:
            raise ProjectionContractError(
                f"{lock_path}: duplicate imports lock entry for parent {key[0]}/{key[1]}."
            )
        resolved[key] = {
            "parent_space_name": key[0],
            "parent_snapshot": parent_snapshot.strip(),
            "parent_site_base_url": parent_site_base_url.strip(),
        }
    return resolved


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
