"""Deterministic comment merge/normalization helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any

from sapi.contracts.ids import format_comment_no, make_comment_uid, slugify


_TURN_POSITION_ARGUMENTATIVE = {"support", "challenge", "rebuttal", "synthesis"}
_TURN_POSITION_SOCIAL = "social"
_CLAIM_BADGE_ALLOWED_STATUSES = {"verified", "unverified", "disputed"}
_CLAIM_ID_RE = re.compile(r"^claim-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}$")
_SOURCE_ID_RE = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}$")
_UNCLASSIFIED_FACTUAL_CLAIM_RE = re.compile(
    r"(?:\[\[claims:[^\]]+\]\])|(?:\b(?:claim|source)-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}\b)"
)


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
    existing_by_key: dict[tuple[str, str, str | None, str | None, str | None], dict[str, Any]] = {}
    known_comment_uids: set[str] = set()
    merged_comments: list[dict[str, Any]] = []
    for comment in existing_comments:
        normalized = _normalize_existing_comment(comment, existing_by_comment_no=existing_by_comment_no)
        key = (
            normalized["persona_id"],
            normalized["body"],
            normalized["parent_comment_uid"],
            _turn_key(normalized.get("turn")),
            _claim_badges_key(normalized.get("claim_badges")),
        )
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
        key = (
            normalized["persona_id"],
            normalized["body"],
            parent_comment_uid,
            _turn_key(normalized.get("turn")),
            _claim_badges_key(normalized.get("claim_badges")),
        )
        if key in existing_by_key:
            existing_row = existing_by_key[key]
            comment_uid = existing_row["comment_uid"]
            if normalized.get("score_assessment") is not None:
                existing_row["score_assessment"] = normalized["score_assessment"]
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
                    **({"turn": normalized["turn"]} if normalized.get("turn") is not None else {}),
                    **(
                        {"claim_badges": normalized["claim_badges"]}
                        if normalized.get("claim_badges")
                        else {}
                    ),
                    **(
                        {"score_assessment": normalized["score_assessment"]}
                        if normalized.get("score_assessment") is not None
                        else {}
                    ),
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
    _attach_render_contract_fields(page_ref=page_ref, comments=merged_comments)

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
        "moderator_outcomes": _build_moderator_outcome_summary(comments=merged_comments),
    }
    return updated


def _attach_render_contract_fields(*, page_ref: str, comments: list[dict[str, Any]]) -> None:
    for comment in comments:
        comment_uid = _require_non_empty_string(comment.get("comment_uid"), "comment_uid")
        _require_non_empty_string(comment.get("persona_id"), "persona_id")
        _require_non_empty_string(comment.get("body"), "body")
        social_vote = _resolve_social_vote(comment)
        comment["social_vote"] = social_vote
        comment["permalink"] = f"#{comment_uid}"
        comment["thread_state_key"] = comment_uid
        comment["thread_expansion_key"] = comment_uid


def _turn_position(raw_turn: Any) -> str:
    if not isinstance(raw_turn, dict):
        return _TURN_POSITION_SOCIAL
    position = _normalize_string(raw_turn.get("position"))
    return position if position is not None else _TURN_POSITION_SOCIAL


def _resolve_social_vote(comment: dict[str, Any]) -> dict[str, int]:
    score_assessment = _normalize_score_assessment(comment.get("score_assessment"))
    if score_assessment is not None:
        score = int(score_assessment["score"])
        if score >= 0:
            upvotes = score + 12
            downvotes = 12
        else:
            upvotes = 12
            downvotes = 12 - score
        return {
            "upvotes": int(upvotes),
            "downvotes": int(downvotes),
            "score": int(score),
        }
    existing_vote = _normalize_social_vote(comment.get("social_vote"))
    if existing_vote is not None:
        return existing_vote
    return {
        "upvotes": 12,
        "downvotes": 12,
        "score": 0,
    }


def _build_moderator_outcome_summary(*, comments: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {
        "claim_citation": {"passed": 0, "failed": 0},
        "anti_repetition": {"passed": 0, "failed": 0},
        "strongest_opposing_point_ack": {"passed": 0, "failed": 0},
    }
    seen_comment_bodies: set[tuple[str, str]] = set()
    support_count = 0
    challenge_count = 0
    missing_evidence_priorities: list[str] = []

    for comment in comments:
        if not isinstance(comment, dict):
            continue
        persona_id = _normalize_string(comment.get("persona_id")) or ""
        body = _normalize_string(comment.get("body")) or ""

        body_key = (persona_id, " ".join(body.split()).strip().lower())
        if body_key in seen_comment_bodies:
            checks["anti_repetition"]["failed"] += 1
        else:
            checks["anti_repetition"]["passed"] += 1
            seen_comment_bodies.add(body_key)

        turn = comment.get("turn")
        position = _turn_position(turn)
        if position in {"support", "synthesis"}:
            support_count += 1
        elif position in {"challenge", "rebuttal"}:
            challenge_count += 1

        if not isinstance(turn, dict):
            continue
        if position in _TURN_POSITION_ARGUMENTATIVE:
            evidence_refs = turn.get("evidence_refs")
            if isinstance(evidence_refs, list) and len(evidence_refs) > 0:
                checks["claim_citation"]["passed"] += 1
            else:
                checks["claim_citation"]["failed"] += 1
                missing_evidence_priorities.append(
                    "Add evidence_refs for argumentative turns missing claim/source citations."
                )
        if position == "rebuttal":
            ack = _normalize_string(turn.get("strongest_opposing_point_ack"))
            if ack is not None:
                checks["strongest_opposing_point_ack"]["passed"] += 1
            else:
                checks["strongest_opposing_point_ack"]["failed"] += 1
                missing_evidence_priorities.append(
                    "Add strongest_opposing_point_ack before rebuttal text."
                )

    if support_count > challenge_count:
        consensus_rows = [
            "Supportive/synthesis turns currently outnumber challenge/rebuttal turns."
        ]
        disagreement_rows = ["No dominant open disagreement signal detected."]
    elif challenge_count > support_count:
        consensus_rows = ["No dominant consensus signal detected."]
        disagreement_rows = [
            "Challenge/rebuttal turns currently outnumber support/synthesis turns."
        ]
    else:
        consensus_rows = ["Support and challenge signals are currently balanced."]
        disagreement_rows = ["Open disagreements remain balanced across positions."]

    deduped_priorities: list[str] = []
    for item in missing_evidence_priorities:
        if item not in deduped_priorities:
            deduped_priorities.append(item)
    if not deduped_priorities:
        deduped_priorities = ["No immediate evidence-priority gaps detected."]

    moderator_check = (
        "- Moderator Check: "
        f"claim_citation={_check_status_label(checks['claim_citation'])}; "
        f"anti_repetition={_check_status_label(checks['anti_repetition'])}; "
        "strongest_opposing_point_ack="
        f"{_check_status_label(checks['strongest_opposing_point_ack'])}"
    )
    return {
        "moderator_check": moderator_check,
        "guardrail_checks": checks,
        "outcome_sections": {
            "Consensus": consensus_rows,
            "Open Disagreements": disagreement_rows,
            "Missing Evidence Priorities": deduped_priorities,
        },
    }


def _check_status_label(check_row: dict[str, int]) -> str:
    return "pass" if check_row.get("failed", 0) == 0 else "fail"


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
    body, turn = _normalize_body_and_turn(
        raw_body=raw_comment.get("body"),
        raw_turn=raw_comment.get("turn"),
        field_name_prefix="existing comments[].",
    )
    claim_badges = _normalize_claim_badges(
        raw_comment.get("claim_badges"),
        field_name_prefix="existing comments[].",
    )
    score_assessment = _normalize_score_assessment(raw_comment.get("score_assessment"))

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
    if turn is not None:
        normalized["turn"] = turn
    elif "turn" in normalized:
        normalized.pop("turn", None)
    if claim_badges:
        normalized["claim_badges"] = claim_badges
    elif "claim_badges" in normalized:
        normalized.pop("claim_badges", None)
    if score_assessment is not None:
        normalized["score_assessment"] = score_assessment
    elif "score_assessment" in normalized:
        normalized.pop("score_assessment", None)
    return normalized


def _normalize_semantic_comment(raw_comment: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_comment, dict):
        raise ValueError("Generated comment rows must be JSON objects.")
    persona_id = _require_non_empty_string(raw_comment.get("persona_id"), "comments[].persona_id")
    body, turn = _normalize_body_and_turn(
        raw_body=raw_comment.get("body"),
        raw_turn=raw_comment.get("turn"),
        field_name_prefix="comments[].",
    )
    parent_ref = _normalize_string(raw_comment.get("parent_ref"))
    comment_ref = _normalize_string(raw_comment.get("comment_ref"))
    claim_badges = _normalize_claim_badges(
        raw_comment.get("claim_badges"),
        field_name_prefix="comments[].",
    )
    score_assessment = _normalize_score_assessment(
        raw_comment.get("score_assessment"),
        field_name_prefix="comments[].",
        required=False,
    )
    normalized: dict[str, Any] = {
        "persona_id": persona_id,
        "body": body,
        "parent_ref": parent_ref,
        "comment_ref": comment_ref,
        "score_assessment": (
            score_assessment
            if score_assessment is not None
            else {
                "score": 0,
                "rationale": "Neutral fallback: score_assessment missing from semantic row.",
            }
        ),
    }
    if turn is not None:
        normalized["turn"] = turn
    if claim_badges:
        normalized["claim_badges"] = claim_badges
    return normalized


def _normalize_body_and_turn(
    *,
    raw_body: Any,
    raw_turn: Any,
    field_name_prefix: str,
) -> tuple[str, dict[str, Any] | None]:
    raw_body_text = _require_non_empty_string(raw_body, f"{field_name_prefix}body")
    body_without_marker, marker_turn = _extract_inline_turn_marker(raw_body_text)
    turn_from_row = _normalize_turn_payload(
        raw_turn,
        body=body_without_marker,
        field_name_prefix=field_name_prefix,
    )
    if marker_turn is not None and turn_from_row is not None and marker_turn != turn_from_row:
        raise ValueError(
            f"{field_name_prefix}turn must match inline turn marker when both are provided."
        )
    normalized_turn = marker_turn if marker_turn is not None else turn_from_row
    if normalized_turn is None:
        _reject_unclassified_factual_claims_in_social_body(
            body_without_marker,
            field_name_prefix=field_name_prefix,
        )
    return body_without_marker, normalized_turn


def _extract_inline_turn_marker(body: str) -> tuple[str, dict[str, Any] | None]:
    canonical = _extract_marker(body, prefix="<<turn:", suffix=">>")
    legacy = _extract_marker(body, prefix="<!-- turn:", suffix="-->")
    if canonical is not None and legacy is not None:
        raise ValueError("Comment body must not contain both canonical and legacy turn markers.")
    marker = canonical if canonical is not None else legacy
    if marker is None:
        return body, None
    marker_start, marker_end, marker_payload = marker
    try:
        parsed_payload = json.loads(marker_payload)
    except json.JSONDecodeError as exc:
        raise ValueError("Inline turn marker JSON is invalid.") from exc
    marker_turn = _normalize_turn_payload(
        parsed_payload,
        body=(body[:marker_start] + body[marker_end:]).strip(),
        field_name_prefix="inline turn marker ",
    )
    assert marker_turn is not None
    normalized_body = (body[:marker_start] + " " + body[marker_end:]).strip()
    if not normalized_body:
        raise ValueError("Comment body must include text outside the inline turn marker.")
    return normalized_body, marker_turn


def _extract_marker(
    body: str,
    *,
    prefix: str,
    suffix: str,
) -> tuple[int, int, str] | None:
    start = body.find(prefix)
    if start < 0:
        return None
    second_start = body.find(prefix, start + len(prefix))
    if second_start >= 0:
        raise ValueError("Comment body must not contain more than one inline turn marker.")
    payload_start = start + len(prefix)
    end = body.find(suffix, payload_start)
    if end < 0:
        raise ValueError("Inline turn marker is missing a closing delimiter.")
    return start, end + len(suffix), body[payload_start:end].strip()


def _normalize_turn_payload(
    raw_turn: Any,
    *,
    body: str,
    field_name_prefix: str,
) -> dict[str, Any] | None:
    if raw_turn is None:
        return None
    if not isinstance(raw_turn, dict):
        raise ValueError(f"{field_name_prefix}turn must be a JSON object when provided.")

    position = _require_non_empty_string(raw_turn.get("position"), f"{field_name_prefix}turn.position")
    if position in _TURN_POSITION_ARGUMENTATIVE:
        claim_ids = _normalize_claim_ids(
            raw_turn.get("claim_ids"),
            field_name=f"{field_name_prefix}turn.claim_ids",
            required_non_empty=True,
        )
        counter_claim_ids = _normalize_claim_ids(
            raw_turn.get("counter_claim_ids"),
            field_name=f"{field_name_prefix}turn.counter_claim_ids",
            required_non_empty=False,
        )
        evidence_refs = _normalize_evidence_refs(
            raw_turn.get("evidence_refs"),
            field_name=f"{field_name_prefix}turn.evidence_refs",
            required_non_empty=True,
        )
        confidence = _normalize_confidence(
            raw_turn.get("confidence"),
            field_name=f"{field_name_prefix}turn.confidence",
            required=True,
        )
        normalized: dict[str, Any] = {
            "position": position,
            "claim_ids": claim_ids,
            "evidence_refs": evidence_refs,
            "confidence": confidence,
        }
        if counter_claim_ids:
            normalized["counter_claim_ids"] = counter_claim_ids
        if position == "rebuttal":
            strongest_opposing_point_ack = _normalize_rebuttal_steelman_ack(
                raw_turn,
                field_name_prefix=field_name_prefix,
            )
            _validate_rebuttal_body_steelman_prefix(
                body=body,
                strongest_opposing_point_ack=strongest_opposing_point_ack,
                field_name_prefix=field_name_prefix,
            )
            normalized["strongest_opposing_point_ack"] = strongest_opposing_point_ack
        return normalized

    if position == _TURN_POSITION_SOCIAL:
        claim_ids = _normalize_claim_ids(
            raw_turn.get("claim_ids"),
            field_name=f"{field_name_prefix}turn.claim_ids",
            required_non_empty=False,
        )
        counter_claim_ids = _normalize_claim_ids(
            raw_turn.get("counter_claim_ids"),
            field_name=f"{field_name_prefix}turn.counter_claim_ids",
            required_non_empty=False,
        )
        evidence_refs = _normalize_evidence_refs(
            raw_turn.get("evidence_refs"),
            field_name=f"{field_name_prefix}turn.evidence_refs",
            required_non_empty=False,
        )
        if claim_ids or counter_claim_ids or evidence_refs:
            raise ValueError(
                f"{field_name_prefix}turn social position must not include claim/evidence references."
            )
        _reject_unclassified_factual_claims_in_social_body(
            body,
            field_name_prefix=field_name_prefix,
        )
        confidence = _normalize_confidence(
            raw_turn.get("confidence"),
            field_name=f"{field_name_prefix}turn.confidence",
            required=False,
        )
        normalized = {"position": _TURN_POSITION_SOCIAL}
        if confidence is not None:
            normalized["confidence"] = confidence
        return normalized

    raise ValueError(
        f"{field_name_prefix}turn.position must be one of support/challenge/rebuttal/synthesis/social."
    )


def _normalize_claim_ids(
    raw_values: Any,
    *,
    field_name: str,
    required_non_empty: bool,
) -> list[str]:
    if raw_values is None:
        if required_non_empty:
            raise ValueError(f"{field_name} must be a non-empty array.")
        return []
    if not isinstance(raw_values, list):
        raise ValueError(f"{field_name} must be an array when provided.")
    normalized: list[str] = []
    for item in raw_values:
        value = _require_non_empty_string(item, field_name)
        if not _CLAIM_ID_RE.fullmatch(value):
            raise ValueError(f"{field_name} contains invalid claim_id: {value}")
        normalized.append(value)
    if required_non_empty and not normalized:
        raise ValueError(f"{field_name} must be a non-empty array.")
    return normalized


def _normalize_evidence_refs(
    raw_values: Any,
    *,
    field_name: str,
    required_non_empty: bool,
) -> list[str]:
    if raw_values is None:
        if required_non_empty:
            raise ValueError(f"{field_name} must be a non-empty array.")
        return []
    if not isinstance(raw_values, list):
        raise ValueError(f"{field_name} must be an array when provided.")
    normalized: list[str] = []
    for item in raw_values:
        value = _require_non_empty_string(item, field_name)
        if value.startswith("claim:"):
            claim_id = value.split(":", 1)[1]
            if not _CLAIM_ID_RE.fullmatch(claim_id):
                raise ValueError(f"{field_name} contains invalid claim evidence ref: {value}")
        elif value.startswith("source:"):
            source_id = value.split(":", 1)[1]
            if not _SOURCE_ID_RE.fullmatch(source_id):
                raise ValueError(f"{field_name} contains invalid source evidence ref: {value}")
        else:
            raise ValueError(f"{field_name} refs must start with claim: or source:.")
        normalized.append(value)
    if required_non_empty and not normalized:
        raise ValueError(f"{field_name} must be a non-empty array.")
    return normalized


def _normalize_confidence(
    raw_value: Any,
    *,
    field_name: str,
    required: bool,
) -> float | None:
    if raw_value is None:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
        raise ValueError(f"{field_name} must be numeric.")
    confidence = float(raw_value)
    if not math.isfinite(confidence) or confidence < 0.0 or confidence > 1.0:
        raise ValueError(f"{field_name} must be finite and in [0.0, 1.0].")
    return confidence


def _normalize_score_assessment(
    raw_value: Any,
    *,
    field_name_prefix: str = "",
    required: bool = False,
) -> dict[str, Any] | None:
    field_name = f"{field_name_prefix}score_assessment" if field_name_prefix else "score_assessment"
    if raw_value is None:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    if not isinstance(raw_value, dict):
        raise ValueError(f"{field_name} must be an object.")
    raw_score = raw_value.get("score")
    if not isinstance(raw_score, int) or isinstance(raw_score, bool):
        raise ValueError(f"{field_name}.score must be an integer.")
    if raw_score < -30 or raw_score > 30:
        raise ValueError(f"{field_name}.score must be in [-30, 30].")
    rationale = _require_non_empty_string(raw_value.get("rationale"), f"{field_name}.rationale")
    return {
        "score": raw_score,
        "rationale": rationale,
    }


def _normalize_social_vote(raw_vote: Any) -> dict[str, int] | None:
    if not isinstance(raw_vote, dict):
        return None
    upvotes = raw_vote.get("upvotes")
    downvotes = raw_vote.get("downvotes")
    score = raw_vote.get("score")
    if (
        not isinstance(upvotes, int)
        or isinstance(upvotes, bool)
        or not isinstance(downvotes, int)
        or isinstance(downvotes, bool)
        or not isinstance(score, int)
        or isinstance(score, bool)
    ):
        return None
    return {
        "upvotes": int(upvotes),
        "downvotes": int(downvotes),
        "score": int(score),
    }


def _reject_unclassified_factual_claims_in_social_body(
    body: str,
    *,
    field_name_prefix: str,
) -> None:
    if _UNCLASSIFIED_FACTUAL_CLAIM_RE.search(body):
        raise ValueError(
            f"{field_name_prefix}body contains factual claim references without argumentative turn metadata."
        )


def _normalize_rebuttal_steelman_ack(
    raw_turn: dict[str, Any],
    *,
    field_name_prefix: str,
) -> str:
    primary_field = f"{field_name_prefix}turn.strongest_opposing_point_ack"
    alias_field = f"{field_name_prefix}turn.steelman_before_rebuttal"
    strongest_opposing_point_ack = _normalize_string(raw_turn.get("strongest_opposing_point_ack"))
    steelman_alias = _normalize_string(raw_turn.get("steelman_before_rebuttal"))

    if strongest_opposing_point_ack is None and steelman_alias is None:
        raise ValueError(
            f"{primary_field} is required for rebuttal turns."
        )
    if strongest_opposing_point_ack is not None and steelman_alias is not None:
        if strongest_opposing_point_ack != steelman_alias:
            raise ValueError(
                f"{primary_field} must match {alias_field} when both are provided."
            )
        return strongest_opposing_point_ack
    if strongest_opposing_point_ack is not None:
        return strongest_opposing_point_ack
    assert steelman_alias is not None
    return steelman_alias


def _validate_rebuttal_body_steelman_prefix(
    *,
    body: str,
    strongest_opposing_point_ack: str,
    field_name_prefix: str,
) -> None:
    body_normalized = " ".join(body.split()).strip().lower()
    ack_normalized = " ".join(strongest_opposing_point_ack.split()).strip().lower()
    if not body_normalized.startswith(ack_normalized):
        raise ValueError(
            f"{field_name_prefix}turn.strongest_opposing_point_ack must appear at the start of rebuttal body text."
        )
    if body_normalized == ack_normalized:
        raise ValueError(
            f"{field_name_prefix}body must include rebuttal text after strongest_opposing_point_ack."
        )


def _normalize_claim_badges(
    raw_claim_badges: Any,
    *,
    field_name_prefix: str,
) -> list[dict[str, Any]]:
    if raw_claim_badges is None:
        return []
    if not isinstance(raw_claim_badges, list):
        raise ValueError(f"{field_name_prefix}claim_badges must be an array when provided.")
    normalized: list[dict[str, Any]] = []
    for index, raw_badge in enumerate(raw_claim_badges):
        field_base = f"{field_name_prefix}claim_badges[{index}]"
        if not isinstance(raw_badge, dict):
            raise ValueError(f"{field_base} must be an object.")
        claim_id = _require_non_empty_string(raw_badge.get("claim_id"), f"{field_base}.claim_id")
        if not _CLAIM_ID_RE.fullmatch(claim_id):
            raise ValueError(f"{field_base}.claim_id contains invalid claim_id: {claim_id}")
        raw_status = _normalize_string(raw_badge.get("status"))
        if raw_status is None:
            status = "unverified"
        else:
            candidate = raw_status.lower()
            status = candidate if candidate in _CLAIM_BADGE_ALLOWED_STATUSES else "unverified"
        confidence = _normalize_confidence(
            raw_badge.get("confidence"),
            field_name=f"{field_base}.confidence",
            required=False,
        )
        normalized_badge: dict[str, Any] = {
            "claim_id": claim_id,
            "status": status,
        }
        if confidence is not None:
            normalized_badge["confidence"] = confidence
        normalized.append(normalized_badge)
    return normalized


def _turn_key(raw_turn: Any) -> str | None:
    if raw_turn is None:
        return None
    if not isinstance(raw_turn, dict):
        raise ValueError("turn payload must be a JSON object.")
    return json.dumps(raw_turn, sort_keys=True)


def _claim_badges_key(raw_claim_badges: Any) -> str | None:
    if raw_claim_badges is None:
        return None
    if not isinstance(raw_claim_badges, list):
        raise ValueError("claim_badges payload must be an array when provided.")
    return json.dumps(raw_claim_badges, sort_keys=True)


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
