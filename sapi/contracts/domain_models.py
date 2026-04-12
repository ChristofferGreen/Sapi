"""Typed core domain models and boundary invariant checks (design Section 3)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, Sequence


_SPACE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PERSONA_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_SOURCE_ID_RE = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}$")
_CLAIM_ID_RE = re.compile(r"^claim-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}$")
_TOPIC_ID_RE = re.compile(r"^topic-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}$")
_COMMENT_UID_RE = re.compile(r"^comment-[a-z0-9]+(?:-[a-z0-9]+)*--[a-z0-9]{10,}$")

_UNDIRECTED_RELATION_TYPES: set[str] = {"contradictory", "similar"}
_DIRECTED_RELATION_TYPES: set[str] = {"supports", "derived_from", "falsifies"}
_ALLOWED_RELATION_TYPES: set[str] = _UNDIRECTED_RELATION_TYPES | _DIRECTED_RELATION_TYPES
_ALLOWED_COMMENT_PAGE_TYPES: set[str] = {"topic", "source", "claim", "persona_profile"}


@dataclass(frozen=True)
class Site:
    site_name: str
    site_root: str = "."
    site_base_url: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.site_name, "site_name")
        _require_non_empty(self.site_root, "site_root")
        if self.site_base_url is not None:
            _require_non_empty(self.site_base_url, "site_base_url")


@dataclass(frozen=True)
class Space:
    space_name: str
    site_name: str

    def __post_init__(self) -> None:
        _require_space_name(self.space_name)
        _require_non_empty(self.site_name, "site_name")


@dataclass(frozen=True)
class SubSpace:
    space_name: str
    parent_space_name: str
    parent_subspace_name: str | None = None
    title: str | None = None

    def __post_init__(self) -> None:
        _require_space_name(self.space_name)
        _require_space_name(self.parent_space_name)
        if self.space_name == self.parent_space_name:
            raise ValueError("sub-space name cannot equal parent space name.")
        if self.parent_subspace_name is not None:
            raise ValueError("Nested sub-spaces are prohibited by contract.")
        if self.title is not None:
            _require_non_empty(self.title, "title")


@dataclass(frozen=True)
class Source:
    source_id: str
    space_name: str

    def __post_init__(self) -> None:
        _require_source_id(self.source_id, "source_id")
        _require_space_name(self.space_name)


@dataclass(frozen=True)
class Claim:
    claim_id: str
    source_id: str
    space_name: str

    def __post_init__(self) -> None:
        _require_claim_id(self.claim_id, "claim_id")
        _require_source_id(self.source_id, "source_id")
        _require_space_name(self.space_name)


@dataclass(frozen=True)
class Relation:
    relation_id: str
    relation_type: str
    src_claim_id: str
    dst_claim_id: str
    space_name: str

    def __post_init__(self) -> None:
        if self.relation_type not in _ALLOWED_RELATION_TYPES:
            raise ValueError(f"Unsupported relation_type: {self.relation_type}")
        _require_claim_id(self.src_claim_id, "src_claim_id")
        _require_claim_id(self.dst_claim_id, "dst_claim_id")
        _require_non_empty(self.relation_id, "relation_id")
        _require_space_name(self.space_name)

        expected = canonical_relation_id(
            relation_type=self.relation_type,
            src_claim_id=self.src_claim_id,
            dst_claim_id=self.dst_claim_id,
        )
        if self.relation_id != expected:
            raise ValueError(
                f"relation_id must match canonical relation grammar for relation_type {self.relation_type}."
            )


@dataclass(frozen=True)
class TopicPage:
    topic_id: str
    space_name: str
    claim_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    narrative_id: str | None = None

    def __post_init__(self) -> None:
        _require_topic_id(self.topic_id, "topic_id")
        _require_space_name(self.space_name)
        if self.narrative_id is not None and self.narrative_id != self.topic_id:
            raise ValueError("legacy alias `narrative_id` must equal canonical `topic_id`.")
        for claim_id in self.claim_ids:
            _require_claim_id(claim_id, "claim_ids[]")
        for source_id in self.source_ids:
            _require_source_id(source_id, "source_ids[]")


@dataclass(frozen=True)
class Persona:
    persona_id: str
    display_name: str
    full_name: str | None = None
    id: str | None = None

    def __post_init__(self) -> None:
        if not _PERSONA_ID_RE.fullmatch(self.persona_id):
            raise ValueError(f"Invalid persona_id format: {self.persona_id}")
        _require_non_empty(self.display_name, "display_name")
        if self.full_name is not None:
            _require_non_empty(self.full_name, "full_name")
        if self.id is not None and self.id != self.persona_id:
            raise ValueError("legacy alias `id` must equal canonical `persona_id`.")


@dataclass(frozen=True)
class Comment:
    comment_uid: str
    persona_id: str
    space_name: str
    page_type: Literal["topic", "source", "claim", "persona_profile"]
    page_id: str
    parent_comment_uid: str | None = None

    def __post_init__(self) -> None:
        _require_comment_uid(self.comment_uid, "comment_uid")
        if not _PERSONA_ID_RE.fullmatch(self.persona_id):
            raise ValueError(f"Invalid persona_id format: {self.persona_id}")
        _require_space_name(self.space_name)
        if self.page_type not in _ALLOWED_COMMENT_PAGE_TYPES:
            raise ValueError(f"Unsupported page_type: {self.page_type}")
        _require_non_empty(self.page_id, "page_id")
        if self.parent_comment_uid is not None:
            _require_comment_uid(self.parent_comment_uid, "parent_comment_uid")

        if self.page_type == "topic":
            _require_topic_id(self.page_id, "page_id")
        elif self.page_type == "source":
            _require_source_id(self.page_id, "page_id")
        elif self.page_type == "claim":
            _require_claim_id(self.page_id, "page_id")
        else:
            if not _PERSONA_ID_RE.fullmatch(self.page_id):
                raise ValueError("persona_profile page_id must be a valid persona_id.")


def canonical_relation_id(*, relation_type: str, src_claim_id: str, dst_claim_id: str) -> str:
    if relation_type not in _ALLOWED_RELATION_TYPES:
        raise ValueError(f"Unsupported relation_type: {relation_type}")
    _require_claim_id(src_claim_id, "src_claim_id")
    _require_claim_id(dst_claim_id, "dst_claim_id")
    if relation_type in _UNDIRECTED_RELATION_TYPES:
        low, high = sorted((src_claim_id, dst_claim_id))
        return f"{relation_type}:{low}|{high}"
    return f"{relation_type}:{src_claim_id}->{dst_claim_id}"


def validate_boundary_invariants(
    *,
    space: Space,
    subspaces: Sequence[SubSpace] = (),
    sources: Sequence[Source] = (),
    claims: Sequence[Claim] = (),
    relations: Sequence[Relation] = (),
    topics: Sequence[TopicPage] = (),
    personas: Sequence[Persona] = (),
    comments: Sequence[Comment] = (),
) -> None:
    source_ids = {source.source_id for source in sources}
    claim_ids = {claim.claim_id for claim in claims}
    topic_ids = {topic.topic_id for topic in topics}
    persona_ids = {persona.persona_id for persona in personas}

    for subspace in subspaces:
        if subspace.parent_space_name != space.space_name:
            raise ValueError("Sub-space parent boundary mismatch.")

    for source in sources:
        if source.space_name != space.space_name:
            raise ValueError("Source boundary mismatch: source belongs to different space.")

    for claim in claims:
        if claim.space_name != space.space_name:
            raise ValueError("Claim boundary mismatch: claim belongs to different space.")
        if claim.source_id not in source_ids:
            raise ValueError("Claim boundary mismatch: claim references unknown source.")

    for relation in relations:
        if relation.space_name != space.space_name:
            raise ValueError("Relation boundary mismatch: relation belongs to different space.")
        if relation.src_claim_id not in claim_ids or relation.dst_claim_id not in claim_ids:
            raise ValueError("Relation boundary mismatch: relation references unknown claim(s).")

    for topic in topics:
        if topic.space_name != space.space_name:
            raise ValueError("Topic boundary mismatch: topic belongs to different space.")
        for claim_id in topic.claim_ids:
            if claim_id not in claim_ids:
                raise ValueError("Topic boundary mismatch: topic references unknown claim.")
        for source_id in topic.source_ids:
            if source_id not in source_ids:
                raise ValueError("Topic boundary mismatch: topic references unknown source.")

    for comment in comments:
        if comment.space_name != space.space_name:
            raise ValueError("Comment boundary mismatch: comment belongs to different space.")
        if persona_ids and comment.persona_id not in persona_ids:
            raise ValueError("Comment boundary mismatch: comment references unknown persona.")
        if comment.page_type == "topic" and comment.page_id not in topic_ids:
            raise ValueError("Comment boundary mismatch: comment references unknown topic page.")
        if comment.page_type == "source" and comment.page_id not in source_ids:
            raise ValueError("Comment boundary mismatch: comment references unknown source page.")
        if comment.page_type == "claim" and comment.page_id not in claim_ids:
            raise ValueError("Comment boundary mismatch: comment references unknown claim page.")
        if comment.page_type == "persona_profile" and persona_ids and comment.page_id not in persona_ids:
            raise ValueError("Comment boundary mismatch: persona profile page_id is unknown.")


def _require_non_empty(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")


def _require_space_name(space_name: str) -> None:
    if not _SPACE_NAME_RE.fullmatch(space_name):
        raise ValueError(f"Invalid space_name slug: {space_name}")


def _require_source_id(source_id: str, field_name: str) -> None:
    if not _SOURCE_ID_RE.fullmatch(source_id):
        raise ValueError(f"Invalid {field_name} format: {source_id}")


def _require_claim_id(claim_id: str, field_name: str) -> None:
    if not _CLAIM_ID_RE.fullmatch(claim_id):
        raise ValueError(f"Invalid {field_name} format: {claim_id}")


def _require_topic_id(topic_id: str, field_name: str) -> None:
    if not _TOPIC_ID_RE.fullmatch(topic_id):
        raise ValueError(f"Invalid {field_name} format: {topic_id}")


def _require_comment_uid(comment_uid: str, field_name: str) -> None:
    if not _COMMENT_UID_RE.fullmatch(comment_uid):
        raise ValueError(f"Invalid {field_name} format: {comment_uid}")
