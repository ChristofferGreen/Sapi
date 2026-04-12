"""Comment pipeline target-selection and preflight contracts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


COMMENT_COUNT_MIN = 5
COMMENT_COUNT_MAX = 50

EVIDENCE_MODE_CANONICAL_ONLY = "canonical-only"
EVIDENCE_MODE_WEB_AUGMENTED = "web-augmented"
_EVIDENCE_MODES = {EVIDENCE_MODE_CANONICAL_ONLY, EVIDENCE_MODE_WEB_AUGMENTED}
_PAGE_TYPES = {"topic", "source", "claim"}
_PAGE_REF_RE = re.compile(r"^(topic|source|claim):(.+)$")
_SAFE_PAGE_KEY_RE = re.compile(r"[^a-z0-9._-]+")


@dataclass(frozen=True)
class CommentTarget:
    page_ref: str
    page_type: str
    page_id: str
    page_path: Path
    page_payload: dict[str, Any]


def validate_comment_count(requested_count: int) -> int:
    if not isinstance(requested_count, int):
        raise TypeError("--count must be an integer.")
    if requested_count < COMMENT_COUNT_MIN or requested_count > COMMENT_COUNT_MAX:
        raise ValueError(
            f"--count must be in [{COMMENT_COUNT_MIN}, {COMMENT_COUNT_MAX}] for comment generation."
        )
    return requested_count


def normalize_evidence_mode(
    evidence_mode: str | None,
    *,
    comment_web_evidence: bool = False,
) -> str:
    normalized = EVIDENCE_MODE_CANONICAL_ONLY if evidence_mode is None else evidence_mode.strip().lower()
    if comment_web_evidence:
        if evidence_mode is not None and normalized != EVIDENCE_MODE_WEB_AUGMENTED:
            raise ValueError(
                "Cannot combine --comment-web-evidence with --comment-evidence-mode values other than web-augmented."
            )
        normalized = EVIDENCE_MODE_WEB_AUGMENTED
    if normalized not in _EVIDENCE_MODES:
        raise ValueError(
            "--comment-evidence-mode must be one of: canonical-only, web-augmented."
        )
    return normalized


def collect_comment_targets(
    *,
    space_root: Path,
    explicit_page_refs: list[str],
) -> list[CommentTarget]:
    if explicit_page_refs:
        return _collect_explicit_targets(space_root=space_root, explicit_page_refs=explicit_page_refs)
    targets = _collect_default_topic_targets(space_root=space_root)
    if not targets:
        raise ValueError(
            "No eligible parseable topic pages found for default targeting; pass --comment-page explicitly."
        )
    return targets


def parse_page_ref(page_ref: str) -> tuple[str, str]:
    if not isinstance(page_ref, str) or not page_ref.strip():
        raise ValueError("comment page references must be non-empty strings.")
    match = _PAGE_REF_RE.fullmatch(page_ref.strip())
    if match is None:
        raise ValueError(
            "Invalid --comment-page value. Expected one of: topic:<topic_id>, source:<source_id>, claim:<claim_id>."
        )
    page_type = match.group(1)
    page_id = match.group(2).strip()
    if page_type not in _PAGE_TYPES or not page_id:
        raise ValueError(f"Invalid --comment-page value: {page_ref}")
    return page_type, page_id


def page_ref_key(page_ref: str) -> str:
    page_type, page_id = parse_page_ref(page_ref)
    normalized_page_id = _SAFE_PAGE_KEY_RE.sub("-", page_id.strip().lower()).strip("-")
    if not normalized_page_id:
        raise ValueError(f"Unable to derive filesystem-safe page_ref_key from {page_ref!r}.")
    return f"{page_type}--{normalized_page_id}"


def _collect_default_topic_targets(*, space_root: Path) -> list[CommentTarget]:
    targets: list[CommentTarget] = []
    topics_dir = space_root / "topics"
    if not topics_dir.is_dir():
        return targets
    for topic_path in sorted(topics_dir.glob("*.json")):
        try:
            payload = _read_page_payload(topic_path)
        except ValueError:
            continue
        topic_id = payload.get("topic_id")
        if not isinstance(topic_id, str) or not topic_id.strip():
            continue
        page_ref = f"topic:{topic_id.strip()}"
        targets.append(
            CommentTarget(
                page_ref=page_ref,
                page_type="topic",
                page_id=topic_id.strip(),
                page_path=topic_path,
                page_payload=payload,
            )
        )
    return targets


def _collect_explicit_targets(
    *,
    space_root: Path,
    explicit_page_refs: list[str],
) -> list[CommentTarget]:
    targets: list[CommentTarget] = []
    seen_page_refs: set[str] = set()
    for raw_page_ref in explicit_page_refs:
        page_type, page_id = parse_page_ref(raw_page_ref)
        canonical_page_ref = f"{page_type}:{page_id}"
        if canonical_page_ref in seen_page_refs:
            continue
        seen_page_refs.add(canonical_page_ref)
        page_path = _page_path_for_ref(space_root=space_root, page_type=page_type, page_id=page_id)
        if not page_path.is_file():
            raise ValueError(f"Requested page target does not exist: {canonical_page_ref}")
        payload = _read_page_payload(page_path)
        targets.append(
            CommentTarget(
                page_ref=canonical_page_ref,
                page_type=page_type,
                page_id=page_id,
                page_path=page_path,
                page_payload=payload,
            )
        )
    if not targets:
        raise ValueError("At least one valid --comment-page target is required when explicit targeting is used.")
    return targets


def _page_path_for_ref(*, space_root: Path, page_type: str, page_id: str) -> Path:
    if page_type == "topic":
        return space_root / "topics" / f"{page_id}.json"
    if page_type == "source":
        return space_root / "sources" / "records" / f"{page_id}.json"
    if page_type == "claim":
        return space_root / "claims" / f"{page_id}.json"
    raise ValueError(f"Unsupported comment page type: {page_type}")


def _read_page_payload(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive parse gate
        raise ValueError(f"Page target JSON is not parseable: {path}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"Page target JSON must be an object: {path}")
    return parsed
