"""Deterministic comment merge/normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sapi.contracts.ids import format_comment_no, make_comment_uid, slugify


@dataclass(frozen=True)
class MergeNormalizeResult:
    merged_comments: list[dict[str, Any]]
    comments_added: int
    new_comment_uids: list[str]


def merge_comment_section(
    *,
    page_ref: str,
    page_payload: dict[str, Any],
    semantic_comments: list[dict[str, Any]],
) -> MergeNormalizeResult:
    existing_comments = _load_existing_comments(page_payload)
    existing_by_comment_no = {
        _normalize_string(comment.get("comment_no")): _normalize_string(comment.get("comment_uid"))
        for comment in existing_comments
        if _normalize_string(comment.get("comment_no")) is not None
        and _normalize_string(comment.get("comment_uid")) is not None
    }
    existing_by_key: dict[tuple[str, str, str | None], dict[str, Any]] = {}
    known_comment_uids: set[str] = set()
    merged_comments: list[dict[str, Any]] = []
    for comment in existing_comments:
        normalized = _normalize_existing_comment(comment, existing_by_comment_no=existing_by_comment_no)
        key = (normalized["persona_id"], normalized["body"], normalized["parent_comment_uid"])
        existing_by_key[key] = normalized
        merged_comments.append(normalized)
        known_comment_uids.add(normalized["comment_uid"])

    draft_ref_map: dict[str, str] = {}
    comments_added = 0
    new_comment_uids: list[str] = []
    for index, raw_comment in enumerate(semantic_comments, start=1):
        normalized = _normalize_semantic_comment(raw_comment)
        parent_comment_uid = _resolve_parent_reference(
            normalized.get("parent_ref"),
            existing_by_comment_no=existing_by_comment_no,
            draft_ref_map=draft_ref_map,
        )
        key = (normalized["persona_id"], normalized["body"], parent_comment_uid)
        if key in existing_by_key:
            comment_uid = existing_by_key[key]["comment_uid"]
        else:
            comment_uid = _new_comment_uid(page_ref=page_ref, persona_id=normalized["persona_id"])
            while comment_uid in known_comment_uids:
                comment_uid = _new_comment_uid(page_ref=page_ref, persona_id=normalized["persona_id"])
            merged_comments.append(
                {
                    "comment_uid": comment_uid,
                    "persona_id": normalized["persona_id"],
                    "body": normalized["body"],
                    "parent_comment_uid": parent_comment_uid,
                }
            )
            known_comment_uids.add(comment_uid)
            comments_added += 1
            new_comment_uids.append(comment_uid)

        comment_ref = normalized.get("comment_ref")
        if comment_ref is not None:
            draft_ref_map[comment_ref] = comment_uid
        draft_ref_map[f"draft-{index}"] = comment_uid

    for ordinal, comment in enumerate(merged_comments, start=1):
        comment["comment_no"] = format_comment_no(ordinal)

    return MergeNormalizeResult(
        merged_comments=merged_comments,
        comments_added=comments_added,
        new_comment_uids=new_comment_uids,
    )


def apply_merged_comments_to_page(
    *,
    page_payload: dict[str, Any],
    page_ref: str,
    merged_comments: list[dict[str, Any]],
) -> dict[str, Any]:
    updated = dict(page_payload)
    updated["comment_section"] = {
        "page_ref": page_ref,
        "comments": merged_comments,
    }
    return updated


def _load_existing_comments(page_payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(page_payload, dict):
        return []
    comment_section = page_payload.get("comment_section")
    if isinstance(comment_section, dict):
        comments = comment_section.get("comments")
        if isinstance(comments, list):
            return [row for row in comments if isinstance(row, dict)]
    comments = page_payload.get("comments")
    if isinstance(comments, list):
        return [row for row in comments if isinstance(row, dict)]
    return []


def _normalize_existing_comment(
    raw_comment: dict[str, Any],
    *,
    existing_by_comment_no: dict[str | None, str | None],
) -> dict[str, Any]:
    comment_uid = _require_non_empty_string(raw_comment.get("comment_uid"), "comment_uid")
    persona_id = _require_non_empty_string(raw_comment.get("persona_id"), "persona_id")
    body = _require_non_empty_string(raw_comment.get("body"), "body")

    parent_comment_uid = _normalize_parent_reference(
        raw_comment.get("parent_comment_uid"),
        existing_by_comment_no=existing_by_comment_no,
    )
    if parent_comment_uid is None:
        parent_comment_uid = _normalize_parent_reference(
            raw_comment.get("parent_ref"),
            existing_by_comment_no=existing_by_comment_no,
        )

    normalized = dict(raw_comment)
    normalized["comment_uid"] = comment_uid
    normalized["persona_id"] = persona_id
    normalized["body"] = body
    normalized["parent_comment_uid"] = parent_comment_uid
    return normalized


def _normalize_semantic_comment(raw_comment: dict[str, Any]) -> dict[str, str | None]:
    if not isinstance(raw_comment, dict):
        raise ValueError("Generated comment rows must be JSON objects.")
    persona_id = _require_non_empty_string(raw_comment.get("persona_id"), "comments[].persona_id")
    body = _require_non_empty_string(raw_comment.get("body"), "comments[].body")
    parent_ref = _normalize_string(raw_comment.get("parent_ref"))
    comment_ref = _normalize_string(raw_comment.get("comment_ref"))
    return {
        "persona_id": persona_id,
        "body": body,
        "parent_ref": parent_ref,
        "comment_ref": comment_ref,
    }


def _resolve_parent_reference(
    raw_parent_ref: str | None,
    *,
    existing_by_comment_no: dict[str | None, str | None],
    draft_ref_map: dict[str, str],
) -> str | None:
    if raw_parent_ref is None:
        return None
    if raw_parent_ref.startswith("comment-"):
        return raw_parent_ref
    if raw_parent_ref.startswith("pc-"):
        return existing_by_comment_no.get(raw_parent_ref)
    return draft_ref_map.get(raw_parent_ref)


def _normalize_parent_reference(
    raw_parent_ref: Any,
    *,
    existing_by_comment_no: dict[str | None, str | None],
) -> str | None:
    normalized = _normalize_string(raw_parent_ref)
    if normalized is None:
        return None
    if normalized.startswith("comment-"):
        return normalized
    if normalized.startswith("pc-"):
        return existing_by_comment_no.get(normalized)
    return None


def _new_comment_uid(*, page_ref: str, persona_id: str) -> str:
    page_slug = slugify(page_ref.replace(":", "-"))
    persona_slug = slugify(persona_id)
    return make_comment_uid(slug=f"{page_slug}-{persona_slug}")


def _require_non_empty_string(raw: Any, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return raw.strip()


def _normalize_string(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        return None
    value = raw.strip()
    return value if value else None
