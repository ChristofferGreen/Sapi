"""Deterministic site-builder and site-root New-index projection functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
import hashlib
from html import escape
import json
import math
import os
from pathlib import Path
import re
import shutil
import unicodedata
from typing import Any
from urllib.parse import urlsplit

from sapi.build.projection import SpaceProjection, load_space_projection
from sapi.build.topic_claim_rendering import (
    claim_option_title,
    extract_claim_annotations,
    load_claim_option_titles,
    render_sentence_claim_body,
    render_sentence_claim_picker_script,
    sentence_claim_bindings,
    short_claim_option_label,
    split_sentences,
    truncate_text_for_ui,
)
from sapi.core.display_titles import resolve_display_title
from sapi.core.site_scope import load_site_scope, load_subspaces_metadata
from sapi.lint.lint_engine import LintSummary, default_lint_summary
from sapi.overview.overview_pipeline import resolve_overview_scope
from sapi.profiles.persona_catalog import derive_profile_image_thumb_path, load_seeded_persona_catalog
from sapi.questions.prepared_questions import PreparedQuestion, load_prepared_questions

_WIKI_SECTION_ORDER: tuple[str, ...] = (
    "lead summary",
    "key points",
    "background and context",
    "main concepts/subtopics",
    "evidence and claims",
    "related sources",
    "open questions / disagreements",
    "references",
)
TAB_PAGE_SIZE = 50
SOURCE_SORT_MODES: tuple[tuple[str, str, str, str, str], ...] = (
    ("date", "Date", "sources", "sources/by-date-asc", "desc"),
    ("citation_count", "Citation count", "sources/by-citation-count", "sources/by-citation-count-asc", "desc"),
    ("title", "Title", "sources/by-title-desc", "sources/by-title", "asc"),
)
TOPIC_SORT_MODES: tuple[tuple[str, str, str, str, str], ...] = (
    ("date", "Date", "topics", "topics/by-date-asc", "desc"),
    ("evidence_count", "Evidence", "topics/by-evidence", "topics/by-evidence-asc", "desc"),
    ("claim_count", "Claims", "topics/by-claims", "topics/by-claims-asc", "desc"),
    ("title", "Title", "topics/by-title-desc", "topics/by-title", "asc"),
)
NEW_SORT_MODES: tuple[tuple[str, str, str, str, str], ...] = (
    ("date", "Date", "new", "new/by-date-asc", "desc"),
    ("title", "Title", "new/by-title-desc", "new/by-title", "asc"),
    ("type", "Type", "new/by-type-desc", "new/by-type", "asc"),
)
USER_SORT_MODES: tuple[tuple[str, str, str, str, str], ...] = (
    ("name", "Name", "users/by-name-desc", "users", "asc"),
)
CLAIM_SORT_MODES: tuple[tuple[str, str, str, str, str], ...] = (
    ("score", "Score", "claims", "claims/by-score-asc", "desc"),
    ("date", "Date", "claims/by-date", "claims/by-date-asc", "desc"),
    ("title", "Title", "claims/by-title-desc", "claims/by-title", "asc"),
)
EVIDENCE_SORT_MODES: tuple[tuple[str, str, str, str, str], ...] = (
    ("title", "Title", "evidence/by-title-desc", "evidence", "asc"),
    ("source", "Source", "evidence/by-source-desc", "evidence/by-source", "asc"),
    ("claims", "Claims", "evidence/by-claims", "evidence/by-claims-asc", "desc"),
)
CONTEXTUAL_RELATED_LINK_TYPES: frozenset[str] = frozenset(
    {"encyclopedia", "repository", "discussion_forum"}
)
_ROOT_LOCAL_URL_ATTR_RE = re.compile(r'(?P<prefix>\b(?:href|src|action)=\")(?P<url>/[^\"]*)\"')


@dataclass(frozen=True)
class BuildResult:
    """Summary of one deterministic space build invocation."""

    space_name: str
    output_root: Path
    generated_files: list[Path]
    content_hashes: dict[str, str]
    lint_summary: LintSummary


@dataclass(frozen=True)
class _FeedEntry:
    timestamp: str
    space_name: str
    item_type: str
    item_id: str
    title: str
    summary: str
    display_timestamp: str = ""
    authors: tuple["_AuthorRef", ...] = ()
    source_preview_href: str | None = None
    citation_count: float | None = None
    evidence_count: int | None = None
    claim_count: int | None = None
    source_count: int | None = None


@dataclass(frozen=True)
class _AuthorRef:
    author_id: str
    display_name: str
    institution: str = ""


@dataclass(frozen=True)
class _AuthorIdentity:
    display_name: str
    institution: str = ""


@dataclass
class _AuthorProfile:
    author_id: str
    display_name: str
    institutions: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    source_ids: set[str] = field(default_factory=set)
    topic_ids: set[str] = field(default_factory=set)
    source_years: set[int] = field(default_factory=set)


@dataclass(frozen=True)
class _SourcePreviewEntry:
    source_id: str
    title: str
    summary: str
    preview_image_path: Path | None
    preview_suffix: str


@dataclass(frozen=True)
class _SearchIndexEntry:
    item_type: str
    item_id: str
    title: str
    href: str
    search_text: str


@dataclass(frozen=True)
class _EvidenceRecord:
    evidence_id: str
    title: str
    excerpt: str
    overview: str
    evidence_type: str
    source_id: str
    claim_ids: tuple[str, ...]
    page_refs: tuple[str, ...]
    topic_ids: tuple[str, ...]


@dataclass(frozen=True)
class _SpaceLayoutContext:
    site_name: str
    space_name: str
    all_space_names: list[str]
    site_subspaces_by_space: dict[str, list[tuple[str, str | None]]]
    subspaces: list[tuple[str, str | None]]
    sources: list[dict[str, Any]]
    topics: list[dict[str, Any]]
    questions: list[PreparedQuestion]
    overview: "_SpaceOverviewArtifact | None"
    tabs: tuple[str, ...]


@dataclass(frozen=True)
class _SpaceOverviewArtifact:
    overview_id: str
    title: str
    summary: str
    scope_kind: str
    scope_name: str
    sections: tuple[dict[str, Any], ...]
    source_ids: tuple[str, ...]
    claim_ids: tuple[str, ...]
    citation_anchors: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]


@dataclass
class _CommentRenderNode:
    comment_uid: str
    comment_no: str
    body: str
    parent_uid: str
    parent_resolved: bool
    persona_id: str
    avatar_href: str
    thread_state_key: str
    thread_expansion_key: str
    social_vote: dict[str, int]
    children: list["_CommentRenderNode"]


def build_space_site(
    space_root: Path,
    *,
    incremental: bool,
    site_presentation_mode: str = "public",
    compiled_stylesheet: bytes,
) -> BuildResult:
    """Build deterministic space HTML from canonical JSON artifacts only."""
    projection = load_space_projection(space_root)
    space_name = space_root.name
    output_root = space_root / "site"
    _reset_render_root_for_deterministic_build(render_root=output_root, incremental=incremental)
    output_root.mkdir(parents=True, exist_ok=True)
    stylesheet_path = output_root / "assets" / "site.css"
    _write_binary_file(stylesheet_path, compiled_stylesheet, incremental=incremental)
    site_path = space_root.parent.parent
    context = _build_layout_context(space_root=space_root, projection=projection, site_path=site_path)
    persona_rows = _load_persona_rows()
    evidence_records = _build_space_evidence_records(space_root=space_root, projection=projection)

    generated_files: list[Path] = [stylesheet_path]
    generated_files.extend(
        _write_source_pages(
            output_root=output_root,
            projection=projection,
            evidence_records=evidence_records,
            incremental=incremental,
            context=context,
        )
    )
    generated_files.extend(
        _write_topic_pages(
            output_root=output_root,
            projection=projection,
            evidence_records=evidence_records,
            incremental=incremental,
            site_presentation_mode=site_presentation_mode,
            context=context,
        )
    )
    generated_files.extend(
        _write_space_claim_pages(
            output_root=output_root,
            projection=projection,
            context=context,
            evidence_records=evidence_records,
            incremental=incremental,
            site_presentation_mode=site_presentation_mode,
        )
    )
    generated_files.extend(
        _write_space_evidence_pages(
            output_root=output_root,
            projection=projection,
            context=context,
            evidence_records=evidence_records,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_question_pages(
            output_root=output_root,
            projection=projection,
            context=context,
            evidence_records=evidence_records,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_tab_pages(
            output_root=output_root,
            projection=projection,
            context=context,
            persona_rows=persona_rows,
            evidence_records=evidence_records,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_user_profile_pages(
            output_root=output_root,
            projection=projection,
            context=context,
            persona_rows=persona_rows,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_author_pages(
            output_root=output_root,
            projection=projection,
            context=context,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_persona_avatar_assets(
            output_root=output_root,
            persona_rows=persona_rows,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_persona_profile_assets(
            output_root=output_root,
            persona_rows=persona_rows,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_search_page(
            output_root=output_root,
            projection=projection,
            context=context,
            persona_rows=persona_rows,
            evidence_records=evidence_records,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_overview_page(
            output_root=output_root,
            context=context,
            incremental=incremental,
        )
    )

    index_path = output_root / "index.html"
    _write_text_file(
        index_path,
        _render_space_index(
            space_name=space_name,
            projection=projection,
            context=context,
            evidence_records=evidence_records,
            site_path=site_path,
            stylesheet_href=_relative_href(from_file=index_path, to_file=stylesheet_path),
        ),
        incremental=incremental,
    )
    generated_files.append(index_path)
    _rewrite_root_relative_links_for_file_mode(
        root=output_root,
        site_path=site_path,
        incremental=incremental,
    )

    content_hashes = {str(path.relative_to(output_root)): _sha256(path) for path in sorted(generated_files)}
    lint_summary = default_lint_summary(issues=projection.lint_issues)
    return BuildResult(
        space_name=space_name,
        output_root=output_root,
        generated_files=sorted(generated_files),
        content_hashes=content_hashes,
        lint_summary=lint_summary,
    )


def refresh_site_new_index(
    site_path: Path,
    *,
    incremental: bool,
    compiled_stylesheet: bytes,
) -> Path:
    """Refresh site-root New index from canonical source/topic artifacts across spaces."""
    spaces_root = site_path / "spaces"
    entries: list[_FeedEntry] = []
    preview_entries: dict[str, _SourcePreviewEntry] = {}
    space_names: list[str] = []
    subspaces_by_space: dict[str, list[tuple[str, str | None]]] = {}
    for space_root in sorted(spaces_root.glob("*")):
        if not space_root.is_dir():
            continue
        space_name = space_root.name
        space_names.append(space_name)
        projection = load_space_projection(space_root)
        entries.extend(_space_feed_entries(space_name=space_name, projection=projection, site_path=site_path))
        for source in projection.sources:
            source_id = str(source["source_id"])
            preview_image_path, preview_suffix = _resolve_front_page_image_source_path(
                source=source,
                space_name=space_name,
                site_path=site_path,
            )
            candidate = _SourcePreviewEntry(
                source_id=source_id,
                title=_source_display_title(source),
                summary=_compact_summary(str(source.get("summary") or source.get("context") or "")),
                preview_image_path=preview_image_path,
                preview_suffix=preview_suffix,
            )
            existing = preview_entries.get(source_id)
            if existing is None or (
                existing.preview_image_path is None and candidate.preview_image_path is not None
            ):
                preview_entries[source_id] = candidate
        subspaces_by_space[space_name] = _load_subspaces(space_root)

    _sort_feed_entries(entries)
    root_space_names = _top_level_site_space_names(
        space_names=space_names,
        subspaces_by_space=subspaces_by_space,
    )

    site_name = _resolve_site_name(site_path)
    site_root = site_path / "site"
    _reset_render_root_for_deterministic_build(render_root=site_root, incremental=incremental)
    site_root.mkdir(parents=True, exist_ok=True)
    site_stylesheet_path = site_root / "assets" / "site.css"
    _write_binary_file(site_stylesheet_path, compiled_stylesheet, incremental=incremental)
    site_index_path = site_root / "index.html"
    _write_text_file(
        site_index_path,
        _render_site_root_index(
            site_name=site_name,
            space_names=root_space_names,
            subspaces_by_space=subspaces_by_space,
            latest_entries=entries[:10],
            stylesheet_href=_relative_href(from_file=site_index_path, to_file=site_stylesheet_path),
        ),
        incremental=incremental,
    )

    persona_rows = _load_persona_rows()
    _write_site_users_pages(
        site_root=site_root,
        site_name=site_name,
        persona_rows=persona_rows,
        space_names=space_names,
        root_space_names=root_space_names,
        subspaces_by_space=subspaces_by_space,
        incremental=incremental,
    )
    _write_site_feed_tab_pages(
        site_root=site_root,
        site_name=site_name,
        entries=entries,
        root_space_names=root_space_names,
        subspaces_by_space=subspaces_by_space,
        incremental=incremental,
    )
    _write_source_preview_assets(
        site_path=site_path,
        preview_entries=preview_entries,
        incremental=incremental,
    )

    for mode in NEW_SORT_MODES:
        sort_key, _sort_label, _desc_path, _asc_path, _default_direction = mode
        for direction in ("desc", "asc"):
            sort_path = _sort_mode_path(mode=mode, direction=direction)
            new_root = site_root / sort_path
            new_root.mkdir(parents=True, exist_ok=True)
            sorted_entries = _sorted_feed_entries(entries, sort_key=sort_key, direction=direction)
            pages = _paginate(sorted_entries, TAB_PAGE_SIZE)
            for page_number, page_entries in enumerate(pages, start=1):
                page_path = _paginated_page_path(new_root, page_number=page_number)
                _write_text_file(
                    page_path,
                    _render_site_new_page(
                        site_name=site_name,
                        space_names=root_space_names,
                        subspaces_by_space=subspaces_by_space,
                        page_entries=page_entries,
                        page_number=page_number,
                        page_count=len(pages),
                        stylesheet_href=_relative_href(from_file=page_path, to_file=site_stylesheet_path),
                        sort_key=sort_key,
                        sort_direction=direction,
                        sort_path=sort_path,
                    ),
                    incremental=incremental,
                )
    _rewrite_root_relative_links_for_file_mode(
        root=site_root,
        site_path=site_path,
        incremental=incremental,
    )
    return _paginated_page_path(new_root, page_number=1)


def _write_source_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    evidence_records: list[_EvidenceRecord],
    incremental: bool,
    context: _SpaceLayoutContext,
) -> list[Path]:
    sources_dir = output_root / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    site_path = output_root.parents[2]
    evidence_by_source_id = _evidence_records_by_source_id(evidence_records)
    claim_records = _load_claim_records(space_root=output_root.parent)
    claim_option_title_by_id = load_claim_option_titles(space_root=output_root.parent)
    for source in sorted(projection.sources, key=lambda item: item["source_id"]):
        _validate_source_access_policy(source)
        source_path = sources_dir / f"{source['source_id']}.html"
        stylesheet_href = _relative_href(
            from_file=source_path,
            to_file=output_root / "assets" / "site.css",
        )
        source_summary = str(source.get("summary") or source.get("context") or "").strip()
        source_file_href = _source_file_href(source=source, space_name=context.space_name)
        source_preview_href = _source_preview_site_href_for_source(
            source=source,
            space_name=context.space_name,
            site_path=site_path,
        )
        related_topics = _source_related_topics(
            source_id=str(source["source_id"]),
            topics=projection.topics,
        )
        related_claim_ids = _collect_claim_ids_from_topics(topics=related_topics)
        source_id = str(source["source_id"])
        source_claim_ids = _source_claim_ids(
            source_id=source_id,
            related_claim_ids=related_claim_ids,
            claim_records=claim_records,
        )
        source_metadata = _render_source_metadata_section(source=source, author_href_prefix="../authors/")
        source_dossier = _resolve_source_dossier(source=source)
        summary_short = str(source_summary).strip()
        if source_dossier is not None:
            candidate = str(source_dossier.get("summary_short") or "").strip()
            if candidate:
                summary_short = candidate
        source_preview_row = _render_source_preview_row(
            source=source,
            source_file_href=source_file_href,
            source_preview_href=source_preview_href,
        )
        related_topics_rows = (
            "\n".join(
                f"<li><a href=\"../topics/{escape(str(topic['topic_id']))}.html\">{escape(str(topic['title']))}</a></li>"
                for topic in related_topics
            )
            or "<li>(none linked yet)</li>"
        )
        related_claim_rows = (
            "\n".join(
                _render_source_claim_row(
                    claim_id=claim_id,
                    source_record=source,
                    claim_record=claim_records.get(claim_id, {}),
                    claim_option_title_by_id=claim_option_title_by_id,
                )
                for claim_id in source_claim_ids
            )
            or "<li>(none linked yet)</li>"
        )
        source_evidence_rows = (
            "\n".join(
                _render_source_evidence_row(
                    record=record,
                    claim_option_title_by_id=claim_option_title_by_id,
                )
                for record in evidence_by_source_id.get(source_id, [])
            )
            or "<li>(none linked yet)</li>"
        )
        source_analysis_section = _render_source_analysis_section(source=source)
        source_revisions_section = _render_source_revisions_section(
            source=source,
            sources=projection.sources,
        )
        external_related_links_card = _render_external_related_links_card(
            heading="External Related Links",
            links=_collect_external_related_links(source.get("external_related_links")),
        )
        summary_row = (
            f"<p class=\"source-summary\">{escape(summary_short)}</p>\n"
            if summary_short
            else "<p class=\"source-summary\">No summary available for this source yet.</p>\n"
        )
        body = (
            f"<h1>{escape(_source_display_title(source))}</h1>\n"
            + "<section class=\"source-hero\">\n"
            + "<div class=\"source-hero-main\">\n"
            + summary_row
            + source_metadata
            + "</div>\n"
            + "<aside class=\"source-hero-preview\">\n"
            + source_preview_row
            + "</aside>\n"
            + "</section>\n"
            + (
                _render_source_dossier_section(
                    dossier=source_dossier,
                    claim_option_title_by_id=claim_option_title_by_id,
                    source_claim_ids=source_claim_ids,
                    claim_records=claim_records,
                )
                if source_dossier is not None
                else ""
            )
            + source_analysis_section
            + source_revisions_section
            + "<section class=\"source-related-grid\">\n"
            + "<article class=\"source-related-card\">\n"
            + "<h2>Related Topics</h2>\n"
            + "<ul class=\"source-related-list\">\n"
            + related_topics_rows
            + "\n</ul>\n"
            + "</article>\n"
            + "<article class=\"source-related-card\">\n"
            + "<h2>Claims Referencing This Source</h2>\n"
            + "<ul class=\"source-related-list\">\n"
            + related_claim_rows
            + "\n</ul>\n"
            + "</article>\n"
            + "<article class=\"source-related-card\">\n"
            + "<h2>Evidence from This Source</h2>\n"
            + "<ul class=\"source-related-list\">\n"
            + source_evidence_rows
            + "\n</ul>\n"
            + "<p><a href=\"../evidence/index.html\">Browse all evidence</a></p>\n"
            + "</article>\n"
            + external_related_links_card
            + "</section>\n"
            + _render_page_comment_section(
                page_payload=source,
                default_page_ref=f"source:{source['source_id']}",
                space_name=context.space_name,
                show_empty_state=True,
            )
            + render_sentence_claim_picker_script()
        )
        _write_text_file(
            source_path,
            _render_space_layout(
                title=_source_display_title(source),
                body=body,
                context=context,
                current_tab="sources",
                current_page=f"source:{source['source_id']}",
                stylesheet_href=stylesheet_href,
            ),
            incremental=incremental,
        )
        written.append(source_path)
    return written


def _source_related_topics(*, source_id: str, topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    related: list[dict[str, Any]] = []
    for topic in topics:
        source_ids = topic.get("source_ids")
        if not isinstance(source_ids, list):
            continue
        if source_id in source_ids:
            related.append(topic)
    return sorted(related, key=lambda topic: str(topic.get("title") or topic.get("topic_id") or ""))


def _source_claim_ids(
    *,
    source_id: str,
    related_claim_ids: list[str],
    claim_records: dict[str, dict[str, Any]],
) -> list[str]:
    source_claim_ids = [
        claim_id
        for claim_id, claim_record in sorted(claim_records.items())
        if str(claim_record.get("source_id") or "").strip() == source_id
    ]
    ordered: list[str] = []
    seen: set[str] = set()
    for claim_id in source_claim_ids + related_claim_ids:
        normalized = str(claim_id).strip()
        if not normalized or normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
    return ordered


def _collect_claim_ids_from_topics(*, topics: list[dict[str, Any]]) -> list[str]:
    claim_ids: set[str] = set()
    for topic in topics:
        claim_ids.update(_collect_claim_ids_from_topic(topic=topic))
    return sorted(claim_ids)


def _collect_claim_ids_from_topic(*, topic: dict[str, object]) -> list[str]:
    claim_ids: set[str] = set()
    raw_claim_ids = topic.get("claim_ids")
    if isinstance(raw_claim_ids, list):
        for claim_id in raw_claim_ids:
            normalized = str(claim_id).strip()
            if normalized:
                claim_ids.add(normalized)
    sections = topic.get("sections")
    if not isinstance(sections, list):
        return sorted(claim_ids)
    for section in sections:
        if not isinstance(section, dict):
            continue
        _, annotation_groups = extract_claim_annotations(str(section.get("body") or ""))
        for group in annotation_groups:
            for claim_id in group:
                normalized = str(claim_id).strip()
                if normalized:
                    claim_ids.add(normalized)
    return sorted(claim_ids)


def _render_source_metadata_section(
    *,
    source: dict[str, Any],
    author_href_prefix: str,
) -> str:
    metadata_rows = _source_metadata_rows(
        source=source,
        author_href_prefix=author_href_prefix,
    )
    if not metadata_rows:
        return ""
    rows = []
    for label, value, is_html in metadata_rows:
        rows.append(
            f"<dt>{escape(label)}</dt><dd>{value if is_html else escape(value)}</dd>"
        )
    return (
        "<section class=\"source-meta-card\">"
        "<h2>Source Details</h2>"
        "<dl class=\"source-meta-grid\">"
        + "".join(rows)
        + "</dl>"
        "</section>\n"
    )


def _render_source_revisions_section(
    *,
    source: dict[str, Any],
    sources: list[dict[str, Any]],
) -> str:
    family_id = _source_family_id(source)
    if not family_id:
        return ""
    revisions = [
        candidate
        for candidate in sources
        if _source_family_id(candidate) == family_id
    ]
    if len(revisions) <= 1:
        return ""

    current_source_id = str(source.get("source_id") or "")
    rows: list[str] = []
    for revision in sorted(revisions, key=_source_revision_sort_key):
        source_id = str(revision.get("source_id") or "")
        if not source_id:
            continue
        badges: list[str] = []
        if source_id == current_source_id:
            badges.append("Current")
        if _source_revision_is_latest(revision):
            badges.append("Latest")
        badge_html = "".join(f"<span class=\"meta-badge\">{escape(label)}</span>" for label in badges)
        metadata = _source_revision_metadata_label(revision)
        rows.append(
            "<li>"
            f"<a href=\"../sources/{escape(source_id)}.html\">{escape(_source_display_title(revision))}</a>"
            f"{badge_html}"
            f"<p class=\"summary\">{escape(metadata)}</p>"
            "</li>"
        )
    if not rows:
        return ""
    return (
        "<section class=\"source-meta-card source-revisions-card\">"
        "<h2>Revisions</h2>"
        "<ul class=\"source-related-list\">"
        + "".join(rows)
        + "</ul>"
        "</section>\n"
    )


def _source_family_id(source: dict[str, Any]) -> str | None:
    raw = source.get("source_family_id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    revision = source.get("source_revision")
    if isinstance(revision, dict):
        raw = revision.get("source_family_id")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _source_revision_sort_key(source: dict[str, Any]) -> tuple[int, str, str]:
    revision = source.get("source_revision")
    raw_index = revision.get("revision_index") if isinstance(revision, dict) else None
    index = raw_index if isinstance(raw_index, int) and raw_index > 0 else 1_000_000
    return (
        index,
        str(source.get("ingested_at") or source.get("date") or ""),
        str(source.get("source_id") or ""),
    )


def _source_revision_is_latest(source: dict[str, Any]) -> bool:
    revision = source.get("source_revision")
    if isinstance(revision, dict) and isinstance(revision.get("is_latest"), bool):
        return bool(revision["is_latest"])
    return False


def _source_revision_metadata_label(source: dict[str, Any]) -> str:
    revision = source.get("source_revision")
    revision_index = revision.get("revision_index") if isinstance(revision, dict) else None
    parts: list[str] = []
    if isinstance(revision_index, int) and revision_index > 0:
        parts.append(f"Revision {revision_index}")
    date = source.get("date")
    ingested_at = source.get("ingested_at")
    if isinstance(date, str) and date.strip():
        parts.append(f"published {date.strip()}")
    if isinstance(ingested_at, str) and ingested_at.strip():
        parts.append(f"ingested {ingested_at.strip()}")
    return " - ".join(parts) if parts else "Revision record"


def _source_metadata_rows(
    *,
    source: dict[str, Any],
    author_href_prefix: str,
) -> list[tuple[str, str, bool]]:
    source_semantic = source.get("source_semantic")
    semantic = source_semantic if isinstance(source_semantic, dict) else {}
    rows: list[tuple[str, str, bool]] = []

    def _append(label: str, value: object, *, is_html: bool = False) -> None:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                rows.append((label, normalized, is_html))
            return
        if isinstance(value, (int, float)):
            rows.append((label, str(value), is_html))

    author_refs = _author_refs(_source_author_identities(source))
    if author_refs:
        name_counts: dict[str, int] = {}
        for author in author_refs:
            name_counts[author.display_name] = name_counts.get(author.display_name, 0) + 1
        author_links = ", ".join(
            (
                "<a class=\"feed-card-author\" href=\""
                + escape(author_href_prefix + author.author_id + ".html")
                + "\">"
                + escape(
                    (
                        f"{author.display_name} ({author.institution})"
                        if name_counts.get(author.display_name, 0) > 1 and author.institution
                        else author.display_name
                    )
                )
                + "</a>"
            )
            for author in author_refs
        )
        _append("Authors", author_links, is_html=True)

    institutions = sorted({author.institution for author in author_refs if author.institution})
    if institutions:
        _append("Institution" if len(institutions) == 1 else "Institutions", ", ".join(institutions))

    _append("Publication date", source.get("date"))
    _append("DOI", semantic.get("doi"))
    access_policy = _source_access_policy(source)
    landing_url = access_policy.get("landing_url")
    if isinstance(landing_url, str) and landing_url.strip():
        _append(
            "Landing page",
            f"<a href=\"{escape(landing_url.strip())}\">{escape(landing_url.strip())}</a>",
            is_html=True,
        )
    if access_policy.get("restricted") is True:
        _append("Access", "Restricted source file")
    _append("Article kind", source.get("article_kind"))
    _append("Source kind", source.get("source_kind"))
    _append("Media type", source.get("source_media_type"))
    citation_count = source.get("citation_count")
    citation_as_of = source.get("citation_count_as_of")
    citation_provider = source.get("citation_count_provider")
    citation_detail = _format_citation_count_for_ui(citation_count)
    if citation_detail != "unknown":
        if isinstance(citation_as_of, str) and citation_as_of.strip():
            citation_detail += f" (as of {citation_as_of.strip()})"
        if isinstance(citation_provider, str) and citation_provider.strip():
            citation_detail += f" via {citation_provider.strip()}"
    rows.append(("Citations", citation_detail, False))
    return rows


def _source_claim_summary(
    *,
    claim_id: str,
    source_record: dict[str, Any],
    claim_record: dict[str, Any],
) -> str:
    explicit = str(claim_record.get("overview") or "").strip()
    if explicit:
        return truncate_text_for_ui(explicit, max_length=260)
    dossier_summary = _claim_dossier_grounding_summary(claim_id=claim_id, source_record=source_record).strip()
    if dossier_summary:
        return truncate_text_for_ui(dossier_summary, max_length=260)
    return truncate_text_for_ui(_claim_text(claim_id=claim_id, claim_record=claim_record), max_length=260)


def _render_source_claim_row(
    *,
    claim_id: str,
    source_record: dict[str, Any],
    claim_record: dict[str, Any],
    claim_option_title_by_id: dict[str, str],
) -> str:
    return (
        "<li><a href=\"../claims/"
        + escape(claim_id)
        + ".html\">"
        + escape(
            claim_option_title(
                claim_id=claim_id,
                claim_option_title_by_id=claim_option_title_by_id,
            )
        )
        + "</a><p class=\"summary\">"
        + escape(
            _source_claim_summary(
                claim_id=claim_id,
                source_record=source_record,
                claim_record=claim_record,
            )
        )
        + "</p></li>"
    )


def _render_source_evidence_row(
    *,
    record: _EvidenceRecord,
    claim_option_title_by_id: dict[str, str],
) -> str:
    detail = str(record.overview or "").strip() or str(record.excerpt or "").strip()
    return (
        "<li><a href=\"../evidence/"
        + escape(record.evidence_id)
        + ".html\">"
        + escape(record.title)
        + "</a><p class=\"summary\">"
        + escape(truncate_text_for_ui(detail, max_length=260))
        + "</p><p class=\"meta\">claims</p>"
        + _evidence_claim_links_html(
            record.claim_ids,
            claim_option_title_by_id=claim_option_title_by_id,
        )
        + "</li>"
    )


def _render_source_analysis_section(*, source: dict[str, Any]) -> str:
    analysis_policy = source.get("analysis_policy")
    source_extraction = source.get("source_extraction")
    artifacts = source.get("artifacts")
    if not isinstance(analysis_policy, dict) and not isinstance(source_extraction, dict):
        return ""
    source_markdown_href = _source_artifact_href(source=source, artifact_key="source_markdown")
    source_file_href = _source_artifact_href(source=source, artifact_key="source_file")
    source_extraction_href = _source_artifact_href(source=source, artifact_key="source_extraction")
    quality_status = ""
    warnings: list[str] = []
    if isinstance(analysis_policy, dict):
        quality_status = str(analysis_policy.get("quality_status") or "").strip()
        raw_warnings = analysis_policy.get("warnings")
        if isinstance(raw_warnings, list):
            warnings.extend(str(item).strip() for item in raw_warnings if str(item).strip())
    converter_name = ""
    converter_version = ""
    extraction_status = ""
    if isinstance(source_extraction, dict):
        converter_name = str(source_extraction.get("converter_name") or "").strip()
        converter_version = str(source_extraction.get("converter_version") or "").strip()
        extraction_status = str(source_extraction.get("status") or "").strip()
        raw_warnings = source_extraction.get("warnings")
        if isinstance(raw_warnings, list):
            warnings.extend(str(item).strip() for item in raw_warnings if str(item).strip())
    warning_rows = "".join(f"<li>{escape(warning)}</li>" for warning in sorted(set(warnings)))
    detail_rows: list[str] = []
    if source_markdown_href:
        detail_rows.append(
            "<dt>Analysis text</dt><dd><a href=\""
            + escape(source_markdown_href)
            + "\">source.md</a></dd>"
        )
    if quality_status:
        detail_rows.append(f"<dt>Markdown quality</dt><dd>{escape(quality_status)}</dd>")
    if extraction_status:
        detail_rows.append(f"<dt>Extraction status</dt><dd>{escape(extraction_status)}</dd>")
    if converter_name:
        converter_label = converter_name
        if converter_version:
            converter_label += f" ({converter_version})"
        detail_rows.append(f"<dt>Converter</dt><dd>{escape(converter_label)}</dd>")
    if source_extraction_href:
        detail_rows.append(
            "<dt>Provenance</dt><dd><a href=\""
            + escape(source_extraction_href)
            + "\">source_extraction.json</a></dd>"
        )
    if source_file_href:
        detail_rows.append(
            "<dt>Fidelity fallback</dt><dd><a href=\""
            + escape(source_file_href)
            + "\">original artifact</a></dd>"
        )
    if not detail_rows and not warning_rows and not isinstance(artifacts, dict):
        return ""
    summary_text = (
        "Source-file and extracted source-text views are restricted; only extraction metadata is shown."
        if not _source_public_view_allowed(source) or not _source_public_download_allowed(source)
        else (
            "Use the extracted markdown by default for analysis. Fall back to the original artifact "
            "for tables, figures, and layout-sensitive content."
        )
    )
    return (
        "<section class=\"source-related-card\">"
        "<h2>Analysis Inputs</h2>"
        f"<p class=\"summary\">{escape(summary_text)}</p>"
        "<dl class=\"source-meta-grid\">"
        + "".join(detail_rows)
        + "</dl>"
        + ("<ul class=\"source-related-list\">" + warning_rows + "</ul>" if warning_rows else "")
        + "</section>\n"
    )


def _source_artifact_href(*, source: dict[str, Any], artifact_key: str) -> str | None:
    if not _source_public_view_allowed(source) and artifact_key in {
        "source_file",
        "source_markdown",
        "source_extraction",
        "source_provenance",
    }:
        return None
    if artifact_key == "source_file" and not _source_public_download_allowed(source):
        return None
    if artifact_key == "source_markdown" and not _source_public_view_allowed(source):
        return None
    artifacts = source.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    artifact_rel = artifacts.get(artifact_key)
    if not isinstance(artifact_rel, str) or not artifact_rel.strip():
        return None
    if Path(artifact_rel).is_absolute():
        return artifact_rel
    return "../../" + "/".join(part for part in Path(artifact_rel).parts if part and part != ".")


def _collect_external_related_links(
    raw_links: Any,
    *,
    allowed_link_types: frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(raw_links, list):
        return []
    normalized: list[dict[str, Any]] = []
    for row in raw_links:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        url = str(row.get("url") or "").strip()
        domain = str(row.get("domain") or "").strip()
        link_type = str(row.get("link_type") or "").strip()
        quality_status = str(row.get("quality_status") or "").strip()
        if not title or not url or not domain or not link_type or not quality_status:
            continue
        if allowed_link_types is not None and link_type not in allowed_link_types:
            continue
        if _is_unusable_external_related_link(url=url, title=title, domain=domain, link_type=link_type):
            continue
        title = _external_related_link_display_title(url=url, title=title, domain=domain)
        normalized.append(
            {
                "title": title,
                "url": url,
                "domain": domain,
                "link_type": link_type,
                "quality_status": quality_status,
                "rationale": str(row.get("rationale") or "").strip(),
                "confidence": str(row.get("confidence") or "").strip(),
                "provenance": row.get("provenance") if isinstance(row.get("provenance"), dict) else {},
                "source_refs": [],
            }
        )
    return normalized


def _is_unusable_external_related_link(*, url: str, title: str, domain: str, link_type: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return True
    has_specific_target = bool(parsed.path.strip("/")) or bool(parsed.query) or bool(parsed.fragment)
    if has_specific_target:
        return False
    normalized_domain = domain.strip().lower().removeprefix("www.")
    host = parsed.netloc.strip().lower().removeprefix("www.")
    normalized_title = title.strip().lower().strip("/")
    if link_type == "repository" and host in {"github.com", "gitlab.com"}:
        return True
    return normalized_title in {"", host, normalized_domain}


def _external_related_link_display_title(*, url: str, title: str, domain: str) -> str:
    parsed = urlsplit(url)
    host = (domain or parsed.netloc).strip().lower().removeprefix("www.")
    normalized_title = title.strip()
    weak_titles = {"", "/", url.strip(), parsed.netloc.strip(), host}
    bibliography_index_title = normalized_title.strip("[]").isdigit()
    if not bibliography_index_title and normalized_title.lower().strip("/") not in {
        item.lower().strip("/") for item in weak_titles
    }:
        return normalized_title
    path = parsed.path.strip("/")
    if host == "doi.org" and path:
        return f"DOI {path}"
    if host == "arxiv.org" and path.startswith("abs/"):
        return f"arXiv {path.removeprefix('abs/')}"
    if host in {"github.com", "gitlab.com"} and path:
        parts = path.split("/")
        if len(parts) >= 2:
            return f"{host}/{parts[0]}/{parts[1]}"
    if path:
        return f"{host}/{path}"
    return host or normalized_title


def _render_external_related_links_card(
    *,
    heading: str,
    links: list[dict[str, Any]],
    source_href_prefix: str | None = None,
) -> str:
    if not links:
        return ""
    rows = "\n".join(
        _render_external_related_link_row(link=link, source_href_prefix=source_href_prefix)
        for link in links
    )
    return (
        "<article class=\"source-related-card\">"
        + f"<h2>{escape(heading)}</h2>"
        + "<ul class=\"source-related-list external-related-list\">"
        + rows
        + "</ul>"
        + "</article>\n"
    )


def _render_external_related_link_row(
    *,
    link: dict[str, Any],
    source_href_prefix: str | None,
) -> str:
    rationale = str(link.get("rationale") or "").strip()
    provenance = link.get("provenance") if isinstance(link.get("provenance"), dict) else {}
    provenance_origin = str(provenance.get("origin") or "").strip().replace("_", " ")
    meta_parts = [
        str(link.get("link_type") or "").replace("_", " "),
        str(link.get("domain") or ""),
        str(link.get("quality_status") or "").replace("_", " "),
    ]
    confidence = str(link.get("confidence") or "").strip()
    if confidence:
        meta_parts.append(f"{confidence} confidence")
    if provenance_origin:
        meta_parts.append(f"from {provenance_origin}")
    source_refs = link.get("source_refs")
    source_rows = ""
    if isinstance(source_refs, list) and source_refs and source_href_prefix:
        source_rows = ", ".join(
            (
                "<a href=\""
                + escape(source_href_prefix + str(row.get("source_id") or "").strip() + ".html")
                + "\">"
                + escape(str(row.get("title") or row.get("source_id") or "").strip())
                + "</a>"
            )
            for row in source_refs
            if isinstance(row, dict) and str(row.get("source_id") or "").strip()
        )
        if source_rows:
            meta_parts.append("via " + source_rows)
    escaped_meta_parts = [
        escape(part)
        for part in meta_parts
        if part and not part.startswith("via <a ")
    ]
    if source_rows:
        escaped_meta_parts.append("via " + source_rows)
    return (
        "<li><a href=\""
        + escape(str(link.get("url") or ""))
        + "\">"
        + escape(str(link.get("title") or ""))
        + "</a>"
        + (f"<p class=\"summary\">{escape(rationale)}</p>" if rationale else "")
        + "<p class=\"meta\">"
        + " | ".join(part for part in escaped_meta_parts if part)
        + "</p></li>"
    )


def _topic_external_related_links(
    *,
    topic: dict[str, Any],
    context: _SpaceLayoutContext,
) -> list[dict[str, Any]]:
    topic_links = _collect_external_related_links(
        topic.get("external_related_links"),
        allowed_link_types=CONTEXTUAL_RELATED_LINK_TYPES,
    )
    source_ids = topic.get("source_ids")
    if not isinstance(source_ids, list):
        return topic_links
    inherited_links = _aggregate_external_related_links(
        source_ids=[str(source_id).strip() for source_id in source_ids if str(source_id).strip()],
        sources=context.sources,
        allowed_link_types=CONTEXTUAL_RELATED_LINK_TYPES,
    )
    return _merge_external_related_links(topic_links + inherited_links)


def _claim_external_related_links(
    *,
    claim_record: dict[str, Any],
    claim_source_id: str,
    source_ids: tuple[str, ...] | list[str],
    projection: SpaceProjection,
) -> list[dict[str, Any]]:
    claim_links = _collect_external_related_links(
        claim_record.get("external_related_links"),
        allowed_link_types=CONTEXTUAL_RELATED_LINK_TYPES,
    )
    candidate_ids = [source_id for source_id in source_ids if source_id]
    if claim_source_id and claim_source_id not in candidate_ids:
        candidate_ids.insert(0, claim_source_id)
    inherited_links = _aggregate_external_related_links(
        source_ids=candidate_ids,
        sources=projection.sources,
        allowed_link_types=CONTEXTUAL_RELATED_LINK_TYPES,
    )
    return _merge_external_related_links(claim_links + inherited_links)


def _aggregate_external_related_links(
    *,
    source_ids: list[str],
    sources: list[dict[str, Any]],
    allowed_link_types: frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    if not source_ids:
        return []
    source_map = {
        str(source.get("source_id") or "").strip(): source
        for source in sources
        if isinstance(source, dict) and str(source.get("source_id") or "").strip()
    }
    merged_by_url: dict[str, dict[str, Any]] = {}
    for source_id in source_ids:
        source = source_map.get(source_id)
        if source is None:
            continue
        source_title = _source_display_title(source)
        for link in _collect_external_related_links(
            source.get("external_related_links"),
            allowed_link_types=allowed_link_types,
        ):
            url = str(link.get("url") or "").strip()
            if not url:
                continue
            inherited_ref = {
                "source_id": source_id,
                "title": source_title,
            }
            if url not in merged_by_url:
                merged = dict(link)
                merged["source_refs"] = [inherited_ref]
                merged_by_url[url] = merged
                continue
            current = merged_by_url[url]
            current_refs = current.get("source_refs")
            if not isinstance(current_refs, list):
                current_refs = []
                current["source_refs"] = current_refs
            if inherited_ref not in current_refs:
                current_refs.append(inherited_ref)
    return sorted(
        merged_by_url.values(),
        key=_external_related_link_sort_key,
    )


def _merge_external_related_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged_by_url: dict[str, dict[str, Any]] = {}
    for link in links:
        url = str(link.get("url") or "").strip()
        if not url:
            continue
        if url not in merged_by_url:
            merged_by_url[url] = dict(link)
            continue
        current_refs = merged_by_url[url].get("source_refs")
        new_refs = link.get("source_refs")
        if not isinstance(current_refs, list):
            current_refs = []
            merged_by_url[url]["source_refs"] = current_refs
        if isinstance(new_refs, list):
            for source_ref in new_refs:
                if source_ref not in current_refs:
                    current_refs.append(source_ref)
    return sorted(merged_by_url.values(), key=_external_related_link_sort_key)


def _external_related_link_sort_key(link: dict[str, Any]) -> tuple[int, int, str, str]:
    quality_status = str(link.get("quality_status") or "")
    link_type = str(link.get("link_type") or "")
    quality_rank = {"trusted": 0, "contextual": 1}.get(quality_status, 99)
    type_rank = {
        "canonical_paper": 0,
        "primary_source": 1,
        "research_index": 2,
        "encyclopedia": 3,
        "repository": 4,
        "discussion_forum": 5,
    }.get(link_type, 99)
    return (
        quality_rank,
        type_rank,
        str(link.get("title") or "").lower(),
        str(link.get("url") or ""),
    )


def _resolve_source_dossier(
    *,
    source: dict[str, Any],
) -> dict[str, Any] | None:
    source_dossier = source.get("source_dossier")
    if isinstance(source_dossier, dict):
        normalized = _normalize_source_dossier(source_dossier=source_dossier)
        if normalized is not None:
            return normalized
    return None


def _normalize_source_dossier(*, source_dossier: dict[str, Any]) -> dict[str, Any] | None:
    summary_short = str(source_dossier.get("summary_short") or "").strip()
    summary_long = str(source_dossier.get("summary_long") or "").strip()
    raw_sections = source_dossier.get("sections")
    sections: list[dict[str, Any]] = []
    if isinstance(raw_sections, list):
        for section in raw_sections:
            if not isinstance(section, dict):
                continue
            heading = str(section.get("heading") or "").strip()
            body = str(section.get("body") or "").strip()
            if not heading or not body:
                continue
            raw_claim_ids = section.get("grounding_claim_ids")
            claim_ids = (
                [str(claim_id).strip() for claim_id in raw_claim_ids if str(claim_id).strip()]
                if isinstance(raw_claim_ids, list)
                else []
            )
            sections.append(
                {
                    "heading": heading,
                    "body": body,
                    "grounding_claim_ids": claim_ids,
                }
            )
    if not summary_short and not summary_long and not sections:
        return None
    return {
        "summary_short": summary_short,
        "summary_long": summary_long,
        "sections": sections,
    }


def _render_source_dossier_section(
    *,
    dossier: dict[str, Any],
    claim_option_title_by_id: dict[str, str],
    source_claim_ids: list[str],
    claim_records: dict[str, dict[str, Any]],
) -> str:
    summary_short = str(dossier.get("summary_short") or "").strip()
    summary_long = str(dossier.get("summary_long") or "").strip()
    sections = dossier.get("sections")
    section_rows: list[str] = []
    normalized_sections = [section for section in sections if isinstance(section, dict)] if isinstance(sections, list) else []
    claim_ref_map = _resolve_source_dossier_claim_ref_map(
        sections=normalized_sections,
        source_claim_ids=source_claim_ids,
        claim_records=claim_records,
    )
    if normalized_sections:
        for idx, section in enumerate(normalized_sections, start=1):
            heading = str(section.get("heading") or "").strip()
            body = str(section.get("body") or "").strip()
            if not heading or not body:
                continue
            raw_claim_ids = (
                [str(claim_id).strip() for claim_id in section.get("grounding_claim_ids", []) if str(claim_id).strip()]
                if isinstance(section.get("grounding_claim_ids"), list)
                else []
            )
            claim_ids = _resolve_section_claim_ids(raw_claim_ids=raw_claim_ids, claim_ref_map=claim_ref_map)
            sentence_bindings = [(sentence, claim_ids) for sentence in split_sentences(body)]
            rendered_body = render_sentence_claim_body(
                sentence_bindings=sentence_bindings,
                section_index=idx,
                site_presentation_mode="public",
                claim_option_title_by_id=claim_option_title_by_id,
            )
            section_rows.append(
                "<article class=\"source-dossier-section\">"
                + "<p class=\"source-dossier-section-kicker\">"
                + f"Section {idx:02d}"
                + "</p>"
                + f"<h3>{escape(heading)}</h3>"
                + f"<p>{rendered_body}</p>"
                + "</article>"
            )

    if not summary_short and not summary_long and not section_rows:
        return ""

    summary_rows = _render_source_dossier_summary_rows(
        summary_short=summary_short,
        summary_long=summary_long,
        has_structured_sections=bool(section_rows),
    )
    summary_class = "source-dossier-lead-block" if section_rows else "source-dossier-long"
    return (
        "<section class=\"source-dossier\">"
        "<h2>Overview and Commentary</h2>"
        + (f"<div class=\"{summary_class}\">{summary_rows}</div>" if summary_rows else "")
        + ("<div class=\"source-dossier-sections\">" + "".join(section_rows) + "</div>" if section_rows else "")
        + "</section>\n"
    )


def _render_source_dossier_summary_rows(
    *,
    summary_short: str,
    summary_long: str,
    has_structured_sections: bool,
) -> str:
    if has_structured_sections and summary_short:
        return f"<p class=\"source-dossier-lead\">{escape(summary_short)}</p>"

    source_text = summary_long or summary_short
    paragraphs = [paragraph.strip() for paragraph in source_text.split("\n\n") if paragraph.strip()]
    if len(paragraphs) == 1:
        paragraphs = _split_source_dossier_long_paragraph(paragraphs[0])
    return "".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs)


def _split_source_dossier_long_paragraph(paragraph: str) -> list[str]:
    sentences = split_sentences(paragraph)
    if len(sentences) <= 3:
        return [paragraph]
    chunks: list[str] = []
    for index in range(0, len(sentences), 3):
        chunks.append(" ".join(sentences[index : index + 3]).strip())
    return [chunk for chunk in chunks if chunk]


def _resolve_section_claim_ids(
    *,
    raw_claim_ids: list[str],
    claim_ref_map: dict[str, str],
) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for raw_claim_id in raw_claim_ids:
        claim_id = claim_ref_map.get(raw_claim_id, raw_claim_id).strip()
        if not claim_id or _is_numeric_claim_ref(claim_id) or claim_id in seen:
            continue
        resolved.append(claim_id)
        seen.add(claim_id)
    return resolved


def _resolve_source_dossier_claim_ref_map(
    *,
    sections: list[dict[str, Any]],
    source_claim_ids: list[str],
    claim_records: dict[str, dict[str, Any]],
) -> dict[str, str]:
    claim_ref_map: dict[str, str] = {}
    for claim_id in source_claim_ids:
        claim_ref_map[claim_id] = claim_id

    numeric_refs: dict[str, str] = {}
    for section in sections:
        heading = str(section.get("heading") or "").strip()
        body = str(section.get("body") or "").strip()
        if not heading and not body:
            continue
        section_context = f"{heading}\n{body}".strip()
        grounding_claim_ids = section.get("grounding_claim_ids")
        if not isinstance(grounding_claim_ids, list):
            continue
        for value in grounding_claim_ids:
            ref = str(value).strip()
            if not _is_numeric_claim_ref(ref):
                claim_ref_map[ref] = ref
                continue
            if ref in numeric_refs:
                numeric_refs[ref] = (numeric_refs[ref] + "\n" + section_context).strip()
            else:
                numeric_refs[ref] = section_context

    if not numeric_refs or not source_claim_ids:
        return claim_ref_map

    candidate_claim_ids = [claim_id for claim_id in source_claim_ids if claim_id]
    if not candidate_claim_ids:
        return claim_ref_map
    candidate_text_by_id = {
        claim_id: _claim_text(claim_id=claim_id, claim_record=claim_records.get(claim_id, {}))
        for claim_id in candidate_claim_ids
    }

    ranked_pairs: list[tuple[float, str, str]] = []
    for ref, context in numeric_refs.items():
        for claim_id in candidate_claim_ids:
            score = _dossier_claim_match_score(context=context, claim_text=candidate_text_by_id[claim_id])
            if score <= 0:
                continue
            ranked_pairs.append((score, ref, claim_id))
    ranked_pairs.sort(key=lambda row: (-row[0], row[1], row[2]))

    assigned_refs: set[str] = set()
    assigned_claim_ids: set[str] = set()
    for _, ref, claim_id in ranked_pairs:
        if ref in assigned_refs or claim_id in assigned_claim_ids:
            continue
        claim_ref_map[ref] = claim_id
        assigned_refs.add(ref)
        assigned_claim_ids.add(claim_id)

    fallback_claim_ids = [claim_id for claim_id in candidate_claim_ids if claim_id not in assigned_claim_ids]
    for ref in sorted((value for value in numeric_refs if value not in assigned_refs), key=lambda value: int(value)):
        index = int(ref)
        if 0 <= index < len(candidate_claim_ids):
            fallback_claim_id = candidate_claim_ids[index]
            claim_ref_map[ref] = fallback_claim_id
            assigned_claim_ids.add(fallback_claim_id)
            continue
        if fallback_claim_ids:
            fallback_claim_id = fallback_claim_ids.pop(0)
            claim_ref_map[ref] = fallback_claim_id
            assigned_claim_ids.add(fallback_claim_id)

    return claim_ref_map


def _dossier_claim_match_score(*, context: str, claim_text: str) -> float:
    context_tokens = _match_tokens(context)
    claim_tokens = _match_tokens(claim_text)
    if not context_tokens or not claim_tokens:
        return 0.0
    overlap = len(context_tokens & claim_tokens)
    if overlap == 0:
        return 0.0
    return (overlap / len(context_tokens)) + (overlap / len(claim_tokens))


def _match_tokens(text: str) -> set[str]:
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]{3,}", text.lower())
        if token not in _DOSSIER_MATCH_STOPWORDS
    }
    return tokens


def _is_numeric_claim_ref(value: str) -> bool:
    return bool(re.fullmatch(r"\d+", value.strip()))


_DOSSIER_MATCH_STOPWORDS = {
    "about",
    "also",
    "and",
    "are",
    "because",
    "been",
    "between",
    "both",
    "can",
    "does",
    "from",
    "into",
    "its",
    "not",
    "one",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "what",
    "which",
    "with",
}


def _write_topic_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    evidence_records: list[_EvidenceRecord],
    incremental: bool,
    site_presentation_mode: str,
    context: _SpaceLayoutContext,
) -> list[Path]:
    topics_dir = output_root / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)
    claim_option_title_by_id = load_claim_option_titles(space_root=output_root.parent)
    claim_records = _load_claim_records(space_root=output_root.parent)
    evidence_by_topic_id = _evidence_records_by_topic_id(evidence_records)
    written: list[Path] = []
    for topic in sorted(projection.topics, key=lambda item: item["topic_id"]):
        topic_id = str(topic["topic_id"])
        topic_path = topics_dir / f"{topic['topic_id']}.html"
        _write_text_file(
            topic_path,
            _render_topic_page(
                topic,
                site_presentation_mode=site_presentation_mode,
                context=context,
                claim_option_title_by_id=claim_option_title_by_id,
                claim_records=claim_records,
                topic_evidence_records=evidence_by_topic_id.get(topic_id, []),
                stylesheet_href=_relative_href(
                    from_file=topic_path,
                    to_file=output_root / "assets" / "site.css",
                ),
            ),
            incremental=incremental,
        )
        written.append(topic_path)
    return written


def _render_space_index(
    *,
    space_name: str,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    evidence_records: list[_EvidenceRecord],
    site_path: Path,
    stylesheet_href: str,
) -> str:
    display_space_name = _space_display_name(space_name)
    active_questions = [question for question in context.questions if question.status == "active"]
    sections: list[str] = [
        f"<h1>{escape(display_space_name)}</h1>\n",
        _render_question_front_page_section(active_questions),
    ]
    if context.overview is not None:
        sections.append(
            _render_space_home_overview_section(
                overview=context.overview,
                display_space_name=display_space_name,
            )
        )
    if context.subspaces:
        subspace_rows = "\n".join(
            (
                "<li><a href=\"../../"
                + escape(subspace_name)
                + "/site/index.html\">"
                + escape(_space_or_subspace_display_name(space_name=subspace_name, title=title))
                + "</a></li>"
            )
            for subspace_name, title in context.subspaces
        )
        sections.append(
            "<h2 class=\"space-home-section-heading\">Subspaces</h2>\n"
            "<ul class=\"feed-list\">\n" + subspace_rows + "\n</ul>\n"
        )
    feed_entries = _space_feed_entries(
        space_name=space_name,
        projection=projection,
        site_path=site_path,
        require_cross_source_topics=False,
    )
    source_rows = "\n".join(
        _render_feed_row(entry)
        for entry in sorted(
            (entry for entry in feed_entries if entry.item_type == "source"),
            key=lambda entry: entry.item_id,
        )
    )
    if source_rows:
        sections.append(
            "<h2 class=\"space-home-section-heading\">Sources</h2>\n"
            "<ul class=\"feed-list\">\n" + source_rows + "\n</ul>\n"
        )
    topic_rows = "\n".join(
        _render_feed_row(entry)
        for entry in sorted(
            (entry for entry in feed_entries if entry.item_type == "topic"),
            key=lambda entry: entry.item_id,
        )
    )
    if topic_rows:
        sections.append(
            "<h2 class=\"space-home-section-heading\">Topics</h2>\n"
            "<ul class=\"feed-list\">\n" + topic_rows + "\n</ul>\n"
        )
    if len(sections) == 2 and not active_questions:
        sections.append("<p>No sources, topics, evidence, or subspaces yet.</p>\n")
    body = "".join(sections)
    return _render_space_layout(
        title=f"{display_space_name} - Space Home",
        body=body,
        context=context,
        current_tab=None,
        current_page="space_home",
        stylesheet_href=stylesheet_href,
    )


def _render_question_front_page_section(questions: list[PreparedQuestion]) -> str:
    return (
        "<section class=\"question-front-page\" data-front-page=\"questions\">\n"
        "<h2>Questions</h2>\n"
        + _render_question_index_list(questions, href_prefix="questions/")
        + "</section>\n"
    )


def _render_space_home_overview_section(
    *,
    overview: _SpaceOverviewArtifact,
    display_space_name: str,
) -> str:
    stats = [
        f"{len(overview.source_ids)} source{'s' if len(overview.source_ids) != 1 else ''}",
        f"{len(overview.claim_ids)} claim{'s' if len(overview.claim_ids) != 1 else ''}",
        (
            f"{len(overview.citation_anchors)} citation anchor"
            f"{'s' if len(overview.citation_anchors) != 1 else ''}"
        ),
    ]
    if overview.warnings:
        stats.append(f"{len(overview.warnings)} warning{'s' if len(overview.warnings) != 1 else ''}")
    return (
        "<section class=\"space-overview-card\">"
        "<h2>Overview</h2>\n"
        + "<p class=\"space-overview-title\">"
        + escape(overview.title)
        + "</p>\n"
        + "<p class=\"space-overview-summary\">"
        + escape(overview.summary)
        + "</p>\n"
        + "<p class=\"space-overview-meta\">"
        + escape(" | ".join(stats))
        + "</p>\n"
        + "<p><a class=\"space-overview-link\" href=\"overview/index.html\" aria-label=\"Open full overview for "
        + escape(display_space_name)
        + "\">Open full overview</a></p>\n"
        + "</section>\n"
    )


def _render_question_index_section(
    questions: list[PreparedQuestion],
    *,
    href_prefix: str,
) -> str:
    return "<h2>Questions</h2>\n" + _render_question_index_list(questions, href_prefix=href_prefix)


def _render_question_index_list(
    questions: list[PreparedQuestion],
    *,
    href_prefix: str,
) -> str:
    rows = "\n".join(
        _render_question_summary_row(question=question, href_prefix=href_prefix)
        for question in sorted(questions, key=lambda item: (item.display_order, item.question_id))
    )
    if not rows:
        rows = "<li class=\"question-summary-empty\">No active prepared questions yet.</li>"
    return "<ul class=\"question-summary-list question-list\">\n" + rows + "\n</ul>\n"


def _render_question_summary_row(*, question: PreparedQuestion, href_prefix: str) -> str:
    short_answer = _question_front_page_short_answer(question)
    answer_html = (
        "<p class=\"question-summary-answer\">"
        + escape(short_answer)
        + "</p>"
        if short_answer
        else ""
    )
    return (
        "<li class=\"question-summary-row\">"
        + "<a class=\"question-summary-title\" href=\""
        + escape(href_prefix + question.question_id + ".html")
        + "\">"
        + escape(question.question)
        + "</a>"
        + "<p class=\"question-summary-meta\">"
        + escape(_question_front_page_stats(question))
        + "</p>"
        + answer_html
        + "</li>"
    )


def _question_front_page_stats(question: PreparedQuestion) -> str:
    stats = [
        _format_count(len(question.linked_source_ids), "source"),
        _format_count(len(question.claim_ids), "claim"),
        _format_count(len(question.evidence_ids), "evidence item"),
    ]
    if question.measurement_ids:
        stats.append(_format_count(len(question.measurement_ids), "measurement"))
    return " | ".join(stats)


def _question_front_page_short_answer(question: PreparedQuestion) -> str:
    value = question.synthesis.get("short_answer")
    if not isinstance(value, str):
        return ""
    return truncate_text_for_ui(value, max_length=260)


def _format_count(count: int, singular: str) -> str:
    if singular.endswith("y"):
        plural = singular[:-1] + "ies"
    else:
        plural = singular + "s"
    return f"{count} {singular if count == 1 else plural}"


def _write_question_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    evidence_records: list[_EvidenceRecord],
    incremental: bool,
) -> list[Path]:
    active_questions = [question for question in context.questions if question.status == "active"]
    renderable_questions = [
        question for question in context.questions if question.status in {"active", "inactive"}
    ]
    question_root = output_root / "questions"
    question_root.mkdir(parents=True, exist_ok=True)
    question_index_path = question_root / "index.html"
    display_space_name = _space_display_name(context.space_name)
    body = (
        "<h1>Questions</h1>\n"
        + _render_question_index_section(active_questions, href_prefix="")
    )
    _write_text_file(
        question_index_path,
        _render_space_layout(
            title=f"{display_space_name} - Questions",
            body=body,
            context=context,
            current_tab="questions",
            stylesheet_href=_relative_href(
                from_file=question_index_path,
                to_file=output_root / "assets" / "site.css",
            ),
        ),
        incremental=incremental,
    )
    written = [question_index_path]

    source_by_id = {str(source["source_id"]): source for source in projection.sources}
    claim_by_id = _load_claim_records(space_root=output_root.parent)
    claim_option_title_by_id = load_claim_option_titles(space_root=output_root.parent)
    evidence_by_id = {record.evidence_id: record for record in evidence_records}
    measurement_by_id = _load_question_measurement_records(space_root=output_root.parent)
    for question in renderable_questions:
        question_path = question_root / f"{question.question_id}.html"
        _write_text_file(
            question_path,
            _render_question_page(
                question=question,
                source_by_id=source_by_id,
                claim_by_id=claim_by_id,
                claim_option_title_by_id=claim_option_title_by_id,
                evidence_by_id=evidence_by_id,
                measurement_by_id=measurement_by_id,
                context=context,
                site_path=output_root.parents[2],
                stylesheet_href=_relative_href(
                    from_file=question_path,
                    to_file=output_root / "assets" / "site.css",
                ),
            ),
            incremental=incremental,
        )
        written.append(question_path)
    return written


def _render_question_page(
    *,
    question: PreparedQuestion,
    source_by_id: dict[str, dict[str, Any]],
    claim_by_id: dict[str, dict[str, Any]],
    claim_option_title_by_id: dict[str, str],
    evidence_by_id: dict[str, _EvidenceRecord],
    measurement_by_id: dict[str, dict[str, Any]],
    context: _SpaceLayoutContext,
    site_path: Path,
    stylesheet_href: str,
) -> str:
    linked_sources = [source_by_id[source_id] for source_id in question.linked_source_ids if source_id in source_by_id]
    linked_claims = [claim_by_id[claim_id] for claim_id in question.claim_ids if claim_id in claim_by_id]
    linked_evidence = [
        evidence_by_id[evidence_id] for evidence_id in question.evidence_ids if evidence_id in evidence_by_id
    ]
    linked_measurements = [
        measurement_by_id[measurement_id]
        for measurement_id in question.measurement_ids
        if measurement_id in measurement_by_id
        and measurement_by_id[measurement_id].get("question_id") == question.question_id
        and _question_measurement_is_interesting(measurement_by_id[measurement_id])
    ]
    stats = (
        f"{len(linked_sources)} source{'s' if len(linked_sources) != 1 else ''}, "
        f"{len(linked_claims)} claim{'s' if len(linked_claims) != 1 else ''}, "
        f"{len(linked_evidence)} evidence item{'s' if len(linked_evidence) != 1 else ''}, "
        f"{len(linked_measurements)} measurement{'s' if len(linked_measurements) != 1 else ''}"
    )
    sections = [
        "<p><a href=\"index.html\">Back to questions</a></p>\n",
        "<h1>" + escape(question.question) + "</h1>\n",
        "<p class=\"meta\">"
        + escape(f"{question.status.capitalize()} question | {stats}")
        + "</p>\n",
        _render_question_synthesis_section(question),
        _render_question_measurement_section(question, linked_measurements),
        _render_question_source_section(
            linked_sources,
            context=context,
            site_path=site_path,
        ),
        _render_question_claim_section(
            linked_claims,
            claim_option_title_by_id=claim_option_title_by_id,
        ),
        _render_question_evidence_section(linked_evidence),
    ]
    if question.warnings:
        warning_rows = "\n".join("<li>" + escape(warning) + "</li>" for warning in question.warnings)
        sections.append("<h2>Warnings</h2>\n<ul class=\"feed-list\">\n" + warning_rows + "\n</ul>\n")
    return _render_space_layout(
        title=f"{_space_display_name(context.space_name)} - {question.question}",
        body="".join(sections),
        context=context,
        current_tab=None,
        current_page=f"question:{question.question_id}",
        stylesheet_href=stylesheet_href,
    )


def _render_question_synthesis_section(question: PreparedQuestion) -> str:
    synthesis = question.synthesis
    short_answer = synthesis.get("short_answer")
    conclusions = synthesis.get("conclusions")
    if not isinstance(short_answer, str) or not short_answer.strip():
        return "<h2>Current synthesis</h2>\n<p>No synthesis has been generated for this question yet.</p>\n"
    body = "<h2>Current synthesis</h2>\n<p>" + escape(short_answer.strip()) + "</p>\n"
    if isinstance(conclusions, list) and conclusions:
        rows = "\n".join(
            "<li>" + escape(_question_synthesis_list_item_text(item)) + "</li>"
            for item in conclusions
            if _question_synthesis_list_item_text(item)
        )
        if rows:
            body += "<h3>Conclusions</h3>\n<ul class=\"feed-list\">\n" + rows + "\n</ul>\n"
    uncertainty = synthesis.get("uncertainty")
    if isinstance(uncertainty, str) and uncertainty.strip():
        body += "<h3>Uncertainty</h3>\n<p>" + escape(uncertainty.strip()) + "</p>\n"
    disagreements = synthesis.get("disagreements")
    if isinstance(disagreements, list) and disagreements:
        rows = "\n".join(
            "<li>" + escape(_question_synthesis_list_item_text(item)) + "</li>"
            for item in disagreements
            if _question_synthesis_list_item_text(item)
        )
        if rows:
            body += "<h3>Disagreements</h3>\n<ul class=\"feed-list\">\n" + rows + "\n</ul>\n"
    return body


def _render_question_measurement_section(
    question: PreparedQuestion,
    measurements: list[dict[str, Any]],
) -> str:
    if not measurements:
        return "<h2>Measurements</h2>\n<p>No key measurements have been extracted for this question yet.</p>\n"
    sorted_measurements = sorted(measurements, key=lambda item: str(item.get("measurement_id", "")))
    chart_groups = _compatible_question_measurement_chart_groups(
        question=question,
        measurements=sorted_measurements,
    )
    body = "<h2>Measurements</h2>\n"
    if chart_groups:
        body += "\n".join(
            _render_question_measurement_chart(group=group, measurements=sorted_measurements)
            for group in chart_groups
        )
    body += (
        "<div class=\"question-measurement-table-wrap\">"
        "<table class=\"question-measurement-table\">"
        "<thead><tr>"
        "<th>Measure</th><th>Value</th><th>Why it matters</th><th>Population</th><th>Outcome</th>"
        "<th>Comparator</th><th>Uncertainty</th><th>Links</th>"
        "</tr></thead><tbody>"
    )
    body += "".join(_render_question_measurement_row(measurement) for measurement in sorted_measurements)
    body += "</tbody></table></div>\n"
    if not chart_groups:
        body += "<p class=\"meta\">No compatible measurement group is available for charting.</p>\n"
    return body


def _render_question_measurement_chart(
    *,
    group: dict[str, Any],
    measurements: list[dict[str, Any]],
) -> str:
    measurement_by_id = {str(item.get("measurement_id")): item for item in measurements}
    group_measurements = [
        measurement_by_id[measurement_id]
        for measurement_id in group.get("measurement_ids", [])
        if measurement_id in measurement_by_id
    ]
    if not group_measurements:
        return ""
    max_value = max(
        float(item["value_max"] if item.get("value_max") is not None else item["value"])
        for item in group_measurements
    )
    if max_value <= 0:
        return ""
    title = (
        str(group.get("measure_name", "")).strip()
        + " / "
        + str(group.get("outcome", "")).strip()
        + " ("
        + str(group.get("unit", "")).strip()
        + ")"
    )
    rows = []
    for measurement in group_measurements:
        raw_value = float(measurement["value_max"] if measurement.get("value_max") is not None else measurement["value"])
        width = max(2.0, min(100.0, (raw_value / max_value) * 100.0))
        label = _measurement_link_label(measurement)
        rows.append(
            "<div class=\"question-measurement-chart-row\" data-measurement-id=\""
            + escape(str(measurement.get("measurement_id", "")))
            + "\">"
            + "<div class=\"question-measurement-chart-label\">"
            + label
            + "</div>"
            + "<div class=\"question-measurement-chart-track\"><span style=\"width: "
            + escape(f"{width:.1f}%")
            + "\"></span></div>"
            + "<div class=\"question-measurement-chart-value\">"
            + escape(_measurement_value_text(measurement))
            + "</div>"
            + "</div>"
        )
    return (
        "<section class=\"question-measurement-chart\" data-chart-group=\""
        + escape(str(group.get("chart_group_id", "")))
        + "\"><h3>"
        + escape(title)
        + "</h3>"
        + "\n".join(rows)
        + "</section>\n"
    )


def _question_measurement_is_interesting(measurement: dict[str, Any]) -> bool:
    question_relevance = measurement.get("question_relevance")
    return isinstance(question_relevance, str) and bool(question_relevance.strip())


def _render_question_measurement_row(measurement: dict[str, Any]) -> str:
    return (
        "<tr>"
        + "<td>"
        + escape(str(measurement.get("measure_name", "")))
        + "</td>"
        + "<td>"
        + escape(_measurement_value_text(measurement))
        + "</td>"
        + "<td>"
        + escape(str(measurement.get("question_relevance", "")))
        + "</td>"
        + "<td>"
        + escape(str(measurement.get("population", "")))
        + "</td>"
        + "<td>"
        + escape(str(measurement.get("outcome", "")))
        + "</td>"
        + "<td>"
        + escape(str(measurement.get("comparator", "")))
        + "</td>"
        + "<td>"
        + escape(str(measurement.get("uncertainty", "")))
        + "</td>"
        + "<td>"
        + _measurement_link_label(measurement)
        + "</td>"
        + "</tr>"
    )


def _compatible_question_measurement_chart_groups(
    *,
    question: PreparedQuestion,
    measurements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    metadata = question.freshness.get("question_measurement_extraction")
    chart_groups = metadata.get("chart_groups") if isinstance(metadata, dict) else []
    if not isinstance(chart_groups, list):
        return []
    measurement_by_id = {str(item.get("measurement_id")): item for item in measurements}
    compatible_groups: list[dict[str, Any]] = []
    for group in chart_groups:
        if not isinstance(group, dict):
            continue
        group_measurement_ids = group.get("measurement_ids")
        if not isinstance(group_measurement_ids, list) or not group_measurement_ids:
            continue
        compatible = True
        for measurement_id in group_measurement_ids:
            measurement = measurement_by_id.get(str(measurement_id))
            if measurement is None:
                compatible = False
                break
            for field in ("measure_name", "unit", "outcome", "population"):
                if measurement.get(field) != group.get(field):
                    compatible = False
                    break
            value = measurement.get("value")
            if isinstance(value, bool) or not isinstance(value, int | float):
                compatible = False
            if not compatible:
                break
        if compatible:
            compatible_groups.append(group)
    return compatible_groups


def _measurement_value_text(measurement: dict[str, Any]) -> str:
    value = _format_measurement_number(measurement.get("value"))
    value_max = measurement.get("value_max")
    unit = str(measurement.get("unit", "")).strip()
    if isinstance(value_max, int | float) and not isinstance(value_max, bool):
        text = value + "-" + _format_measurement_number(value_max)
    else:
        text = value
    return (text + " " + unit).strip()


def _format_measurement_number(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return ""
    as_float = float(value)
    if as_float.is_integer():
        return str(int(as_float))
    return f"{as_float:.3f}".rstrip("0").rstrip(".")


def _measurement_link_label(measurement: dict[str, Any]) -> str:
    links: list[str] = []
    source_id = measurement.get("source_id")
    if isinstance(source_id, str) and source_id:
        links.append(
            "<a href=\"../sources/" + escape(source_id) + ".html\">" + escape(source_id) + "</a>"
        )
    claim_id = measurement.get("claim_id")
    if isinstance(claim_id, str) and claim_id:
        links.append(
            "<a href=\"../claims/" + escape(claim_id) + ".html\">" + escape(claim_id) + "</a>"
        )
    evidence_id = measurement.get("evidence_id")
    if isinstance(evidence_id, str) and evidence_id:
        links.append(
            "<a href=\"../evidence/" + escape(evidence_id) + ".html\">" + escape(evidence_id) + "</a>"
        )
    return " / ".join(links) if links else escape(str(measurement.get("measurement_id", "")))


def _question_synthesis_list_item_text(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if not isinstance(item, dict):
        return ""
    text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        return ""
    support = item.get("support")
    if isinstance(support, str) and support.strip():
        return f"{text.strip()} ({support.strip()} support)"
    return text.strip()


def _render_question_source_section(
    sources: list[dict[str, Any]],
    *,
    context: _SpaceLayoutContext,
    site_path: Path,
) -> str:
    if not sources:
        return (
            "<h2 class=\"question-section-heading\">Sources</h2>\n"
            "<p>No sources have been linked to this question yet.</p>\n"
        )
    cards = "\n".join(
        _render_question_source_card(source=source, context=context, site_path=site_path)
        for source in sorted(sources, key=lambda item: str(item["source_id"]))
    )
    return (
        "<h2 class=\"question-section-heading\">Sources</h2>\n"
        "<div class=\"question-source-grid\">\n"
        + cards
        + "\n</div>\n"
    )


def _render_question_source_card(
    *,
    source: dict[str, Any],
    context: _SpaceLayoutContext,
    site_path: Path,
) -> str:
    source_id = str(source["source_id"])
    title = _source_display_title(source)
    preview_href = _source_preview_site_href_for_source(
        source=source,
        space_name=context.space_name,
        site_path=site_path,
    )
    return (
        "<a class=\"question-source-card\" href=\"../sources/"
        + escape(source_id)
        + ".html\">"
        + "<img class=\"question-source-thumb\" src=\""
        + escape(preview_href)
        + "\" alt=\"Preview for "
        + escape(title)
        + "\" loading=\"lazy\" />"
        + "<span class=\"question-source-title\">"
        + escape(title)
        + "</span></a>"
    )


def _render_question_claim_section(
    claims: list[dict[str, Any]],
    *,
    claim_option_title_by_id: dict[str, str],
) -> str:
    if not claims:
        return (
            "<h2 class=\"question-section-heading\">Claims</h2>\n"
            "<p>No claims have been linked to this question yet.</p>\n"
        )
    rows = "\n".join(
        (
            "<li><a href=\"../claims/"
            + escape(str(claim["claim_id"]))
            + ".html\">"
            + escape(
                claim_option_title(
                    claim_id=str(claim["claim_id"]),
                    claim_option_title_by_id=claim_option_title_by_id,
                )
            )
            + "</a></li>"
        )
        for claim in sorted(claims, key=lambda item: str(item["claim_id"]))
    )
    return (
        "<h2 class=\"question-section-heading\">Claims</h2>\n"
        "<ul class=\"question-link-list\">\n"
        + rows
        + "\n</ul>\n"
    )


def _render_question_evidence_section(evidence_records: list[_EvidenceRecord]) -> str:
    if not evidence_records:
        return (
            "<h2 class=\"question-section-heading\">Evidence</h2>\n"
            "<p>No evidence has been linked to this question yet.</p>\n"
        )
    rows = "\n".join(
        (
            "<li><a href=\"../evidence/"
            + escape(record.evidence_id)
            + ".html\">"
            + escape(record.title)
            + "</a></li>"
        )
        for record in sorted(evidence_records, key=lambda item: item.evidence_id)
    )
    return (
        "<h2 class=\"question-section-heading\">Evidence</h2>\n"
        "<ul class=\"question-link-list\">\n"
        + rows
        + "\n</ul>\n"
    )


def _render_topic_page(
    topic: dict[str, object],
    *,
    site_presentation_mode: str,
    context: _SpaceLayoutContext,
    claim_option_title_by_id: dict[str, str],
    claim_records: dict[str, dict[str, Any]],
    topic_evidence_records: list[_EvidenceRecord],
    stylesheet_href: str,
) -> str:
    if site_presentation_mode not in {"public", "debug"}:
        raise ValueError(f"Unsupported site_presentation_mode: {site_presentation_mode!r}")
    structure_type = _resolve_topic_structure_type(topic)
    sections = _ordered_topic_sections(topic, structure_type=structure_type)
    assert isinstance(sections, list)
    section_rows = "\n".join(
        _render_topic_section(
            section=section,
            section_index=index,
            site_presentation_mode=site_presentation_mode,
            claim_option_title_by_id=claim_option_title_by_id,
        )
        for index, section in enumerate(sections, start=1)
    )
    parent_link_row = _render_pinned_parent_link(topic)
    body = (
        "<article class=\"topic-article\">"
        + f"<h1>{escape(str(topic['title']))}</h1>\n"
        + (
            "<p class=\"topic-structure\" "
            f"data-structure-type=\"{escape(structure_type)}\">Structure: {escape(structure_type)}</p>\n"
        )
        + parent_link_row
        + section_rows
        + "</article>"
        + _render_topic_claims_section(
            topic=topic,
            claim_option_title_by_id=claim_option_title_by_id,
            claim_records=claim_records,
            site_presentation_mode=site_presentation_mode,
        )
        + _render_topic_evidence_section(topic_evidence_records=topic_evidence_records)
        + _render_external_related_links_card(
            heading="External Related Links",
            links=_topic_external_related_links(topic=topic, context=context),
            source_href_prefix="../sources/",
        )
        + _render_page_comment_section(
            page_payload=topic,
            default_page_ref=f"topic:{topic['topic_id']}",
            space_name=context.space_name,
            show_empty_state=True,
        )
        + render_sentence_claim_picker_script()
    )
    return _render_space_layout(
        title=str(topic["title"]),
        body=body,
        context=context,
        current_tab="topics",
        current_page=f"topic:{topic['topic_id']}",
        stylesheet_href=stylesheet_href,
        content_class="content-card topic-content-card",
    )


def _render_topic_claims_section(
    *,
    topic: dict[str, object],
    claim_option_title_by_id: dict[str, str],
    claim_records: dict[str, dict[str, Any]],
    site_presentation_mode: str,
) -> str:
    raw_claim_ids = topic.get("claim_ids")
    claim_ids = _collect_claim_ids_from_topic(topic=topic)
    if not claim_ids and isinstance(raw_claim_ids, list):
        claim_ids = [str(claim_id).strip() for claim_id in raw_claim_ids if str(claim_id).strip()]
    if not claim_ids:
        return (
            "<section class=\"source-related-card\">"
            "<h2>Claims Used by This Topic</h2>"
            "<p>(No claim links are currently attached to this topic.)</p>"
            "</section>"
        )
    row_values: list[str] = []
    for claim_id in claim_ids:
        label = claim_option_title_by_id.get(claim_id)
        if site_presentation_mode != "debug" and not label and claim_id not in claim_records:
            continue
        row_values.append(
            "<li><a href=\"../claims/"
            + escape(claim_id)
            + ".html\">"
            + escape(label if label else claim_id)
            + "</a><p class=\"summary\">"
            + escape(_topic_claim_summary(claim_id=claim_id, claim_record=claim_records.get(claim_id, {})))
            + "</p></li>"
        )
    rows = "\n".join(row_values)
    if not rows:
        return (
            "<section class=\"source-related-card\">"
            "<h2>Claims Used by This Topic</h2>"
            "<p>(No public claim summaries are currently attached to this topic.)</p>"
            "</section>"
        )
    return (
        "<section class=\"source-related-card\">"
        "<h2>Claims Used by This Topic</h2>"
        "<ul class=\"source-related-list\">"
        + rows
        + "</ul>"
        "<p><a href=\"../claims/index.html\">Browse all claims</a></p>"
        "</section>"
    )


def _topic_claim_summary(*, claim_id: str, claim_record: dict[str, Any]) -> str:
    explicit = str(claim_record.get("overview") or "").strip()
    if explicit:
        return truncate_text_for_ui(explicit, max_length=220)
    return truncate_text_for_ui(_claim_text(claim_id=claim_id, claim_record=claim_record), max_length=220)


def _render_topic_evidence_section(*, topic_evidence_records: list[_EvidenceRecord]) -> str:
    if not topic_evidence_records:
        return (
            "<section class=\"source-related-card\">"
            "<h2>Evidence Used by This Topic</h2>"
            "<p>(No evidence items are currently linked to claims in this topic.)</p>"
            "</section>"
        )
    rows = "\n".join(
        (
            "<li><a href=\"../evidence/"
            + escape(record.evidence_id)
            + ".html\">"
            + escape(record.title)
            + "</a><p class=\"summary\">"
            + escape(truncate_text_for_ui(record.excerpt, max_length=180))
            + "</p></li>"
        )
        for record in topic_evidence_records
    )
    return (
        "<section class=\"source-related-card\">"
        "<h2>Evidence Used by This Topic</h2>"
        "<ul class=\"source-related-list\">"
        + rows
        + "</ul>"
        "<p><a href=\"../evidence/index.html\">Browse all evidence</a></p>"
        "</section>"
    )


def _resolve_topic_structure_type(topic: dict[str, object]) -> str:
    raw_structure_type = topic.get("structure_type")
    if isinstance(raw_structure_type, str) and raw_structure_type.strip():
        normalized = raw_structure_type.strip()
        if normalized in {"wiki", "source_mirror"}:
            return normalized
        raise ValueError(f"Unsupported topic structure_type: {normalized!r}")
    source_ids = topic.get("source_ids")
    source_structure_outline = topic.get("source_structure_outline")
    if (
        isinstance(source_ids, list)
        and len(source_ids) == 1
        and isinstance(source_structure_outline, list)
        and any(isinstance(item, str) and item.strip() for item in source_structure_outline)
    ):
        return "source_mirror"
    return "wiki"


def _render_page_comment_section(
    *,
    page_payload: dict[str, object],
    default_page_ref: str,
    space_name: str,
    show_empty_state: bool = False,
) -> str:
    comment_section = page_payload.get("comment_section")
    if not isinstance(comment_section, dict):
        if show_empty_state:
            return (
                "<section class=\"comment-thread\">"
                "<h2>Comment Thread</h2>"
                "<p class=\"comment-empty\">No comments yet for this page.</p>"
                "</section>"
            )
        return ""
    comments = comment_section.get("comments")
    if not isinstance(comments, list):
        if show_empty_state:
            return (
                "<section class=\"comment-thread\">"
                "<h2>Comment Thread</h2>"
                "<p class=\"comment-empty\">No comments yet for this page.</p>"
                "</section>"
            )
        return ""
    page_ref = str(comment_section.get("page_ref") or default_page_ref)
    ordered_nodes: list[_CommentRenderNode] = []
    nodes_by_uid: dict[str, _CommentRenderNode] = {}
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        comment_uid = str(comment.get("comment_uid") or "").strip()
        if not comment_uid or comment_uid in nodes_by_uid:
            continue
        persona_id = str(comment.get("persona_id") or "").strip()
        avatar_href = _persona_avatar_site_href(space_name=space_name, persona_id=persona_id)
        comment_no = str(comment.get("comment_no") or "")
        body = str(comment.get("body") or "")
        parent_uid_raw = comment.get("parent_comment_uid")
        parent_uid = str(parent_uid_raw).strip() if isinstance(parent_uid_raw, str) else ""
        social_vote = _resolve_comment_social_vote(page_ref=page_ref, comment=comment)
        thread_state_key = str(comment.get("thread_state_key") or comment_uid)
        thread_expansion_key = str(comment.get("thread_expansion_key") or comment_uid)
        node = _CommentRenderNode(
            comment_uid=comment_uid,
            comment_no=comment_no,
            body=body,
            parent_uid=parent_uid,
            parent_resolved=False,
            persona_id=persona_id,
            avatar_href=avatar_href,
            thread_state_key=thread_state_key,
            thread_expansion_key=thread_expansion_key,
            social_vote=social_vote,
            children=[],
        )
        ordered_nodes.append(node)
        nodes_by_uid[comment_uid] = node

    roots: list[_CommentRenderNode] = []
    for node in ordered_nodes:
        if node.parent_uid and node.parent_uid != node.comment_uid:
            parent = nodes_by_uid.get(node.parent_uid)
            if parent is not None:
                node.parent_resolved = True
                parent.children.append(node)
                continue
        roots.append(node)
    if not roots and ordered_nodes:
        roots = ordered_nodes

    seen: set[str] = set()
    rendered_rows: list[str] = []
    for node in roots:
        row = _render_comment_tree_node(
            node=node,
            seen=seen,
            lineage=set(),
            space_name=space_name,
        )
        if row:
            rendered_rows.append(row)
    if len(seen) < len(ordered_nodes):
        for node in ordered_nodes:
            row = _render_comment_tree_node(
                node=node,
                seen=seen,
                lineage=set(),
                space_name=space_name,
            )
            if row:
                rendered_rows.append(row)

    if not rendered_rows:
        if show_empty_state:
            return (
                "<section class=\"comment-thread\">"
                "<h2>Comment Thread</h2>"
                "<p class=\"comment-empty\">No comments yet for this page.</p>"
                "</section>"
            )
        return ""
    thread_rows = (
        "<div class=\"comment-thread-list\">"
        + "".join(rendered_rows)
        + "</div>"
        if rendered_rows
        else ""
    )
    empty_row = (
        "<p class=\"comment-empty\">No comments yet for this page.</p>"
        if show_empty_state and not rendered_rows
        else ""
    )
    return (
        "<section class=\"comment-thread\">"
        "<h2>Comment Thread</h2>"
        + empty_row
        + thread_rows
        + "</section>"
    )


def _comment_dom_id(*, comment_uid: str, suffix: str) -> str:
    digest = hashlib.sha256(comment_uid.encode("utf-8")).hexdigest()[:12]
    return f"comment-{suffix}-{digest}"


def _render_comment_tree_node(
    *,
    node: _CommentRenderNode,
    seen: set[str],
    lineage: set[str],
    space_name: str,
) -> str:
    if node.comment_uid in seen or node.comment_uid in lineage:
        return ""
    seen.add(node.comment_uid)
    child_lineage = set(lineage)
    child_lineage.add(node.comment_uid)
    child_rows = "".join(
        _render_comment_tree_node(
            node=child,
            seen=seen,
            lineage=child_lineage,
            space_name=space_name,
        )
        for child in node.children
    )
    children_markup = (
        "<div class=\"comment-children\">"
        + child_rows
        + "</div>"
        if child_rows
        else ""
    )
    body_id = _comment_dom_id(comment_uid=node.comment_uid, suffix="body")
    vote = node.social_vote
    signal_label, signal_tone = _comment_signal_bucket(score=vote["score"])
    persona_label = _persona_label(persona_id=node.persona_id)
    avatar = (
        f"<img class=\"comment-avatar\" src=\"{escape(node.avatar_href)}\" "
        f"alt=\"Avatar for {escape(persona_label)}\" loading=\"lazy\" />"
        if node.avatar_href
        else ""
    )
    profile_href = _persona_profile_page_href(space_name=space_name, persona_id=node.persona_id)
    author = (
        f"<a class=\"comment-author\" href=\"{escape(profile_href)}\">"
        + avatar
        + f"<span class=\"comment-persona\">{escape(persona_label)}</span>"
        + "</a>"
        if profile_href
        else "<span class=\"comment-author\">"
        + avatar
        + f"<span class=\"comment-persona\">{escape(persona_label)}</span>"
        + "</span>"
    )
    parent_row = (
        f"<p class=\"comment-parent\">In reply to {escape(node.parent_uid)}</p>"
        if node.parent_uid and not node.parent_resolved
        else ""
    )
    open_attr = "" if vote["score"] < 0 else " open"
    return (
        f"<details class=\"comment-row\" id=\"{escape(node.comment_uid)}\" "
        f"data-comment-uid=\"{escape(node.comment_uid)}\" "
        f"data-thread-state-key=\"{escape(node.thread_state_key)}\" "
        f"data-thread-expansion-key=\"{escape(node.thread_expansion_key)}\"{open_attr}>"
        + "<summary class=\"comment-summary\">"
        + "<div class=\"comment-vote-stack "
        + f"comment-signal-{escape(signal_tone)}\" data-score=\"{vote['score']}\">"
        + f"<span class=\"comment-signal-label\">{escape(signal_label)}</span>"
        + f"<span class=\"comment-signal-points\">{vote['score']} points</span>"
        + "</div>"
        + "<div class=\"comment-summary-main\">"
        + "<div class=\"comment-meta\">"
        + "<span class=\"comment-toggle-indicator\" aria-hidden=\"true\"></span>"
        + author
        + "</div>"
        + "</div>"
        + "</summary>"
        + f"<div class=\"comment-body-wrap\" id=\"{escape(body_id)}\">"
        + f"<p class=\"comment-body\">{escape(node.body)}</p>"
        + parent_row
        + "</div>"
        + children_markup
        + "</details>"
    )


def _resolve_comment_social_vote(*, page_ref: str, comment: dict[str, object]) -> dict[str, int]:
    social_vote = comment.get("social_vote")
    if (
        isinstance(social_vote, dict)
        and isinstance(social_vote.get("upvotes"), int)
        and isinstance(social_vote.get("downvotes"), int)
        and isinstance(social_vote.get("score"), int)
    ):
        return {
            "upvotes": int(social_vote["upvotes"]),
            "downvotes": int(social_vote["downvotes"]),
            "score": int(social_vote["score"]),
        }
    score_assessment = comment.get("score_assessment")
    if isinstance(score_assessment, dict) and isinstance(score_assessment.get("score"), int):
        score = int(score_assessment["score"])
        if score >= 0:
            upvotes = score + 12
            downvotes = 12
        else:
            upvotes = 12
            downvotes = 12 - score
        return {"upvotes": int(upvotes), "downvotes": int(downvotes), "score": int(score)}
    _ = page_ref
    return {"upvotes": 12, "downvotes": 12, "score": 0}


def _comment_signal_bucket(*, score: int) -> tuple[str, str]:
    if score > 15:
        return "Insightful", "insightful"
    if score >= 0:
        return "Average", "average"
    return "Bad", "bad"


def _ordered_topic_sections(topic: dict[str, object], *, structure_type: str) -> list[dict[str, object]]:
    raw_sections = topic["sections"]
    assert isinstance(raw_sections, list)
    sections: list[dict[str, object]] = [section for section in raw_sections if isinstance(section, dict)]
    if structure_type == "wiki":
        return _ordered_wiki_sections(sections)
    assert structure_type == "source_mirror"
    return _ordered_source_mirror_sections(topic, sections=sections)


def _ordered_wiki_sections(sections: list[dict[str, object]]) -> list[dict[str, object]]:
    preferred_rank = {heading: rank for rank, heading in enumerate(_WIKI_SECTION_ORDER)}
    keyed_sections = []
    for index, section in enumerate(sections):
        normalized_heading = _normalize_heading(str(section.get("heading", "")))
        rank = preferred_rank.get(normalized_heading, len(preferred_rank))
        keyed_sections.append((rank, normalized_heading, index, section))
    keyed_sections.sort(key=lambda row: (row[0], row[1], row[2]))
    return [row[3] for row in keyed_sections]


def _ordered_source_mirror_sections(
    topic: dict[str, object],
    *,
    sections: list[dict[str, object]],
) -> list[dict[str, object]]:
    outline = topic.get("source_structure_outline")
    outline_rank: dict[str, int] = {}
    if isinstance(outline, list):
        for rank, item in enumerate(outline):
            if not isinstance(item, str) or not item.strip():
                continue
            normalized = _normalize_heading(item)
            outline_rank.setdefault(normalized, rank)

    keyed_sections = []
    for index, section in enumerate(sections):
        heading_raw = str(section.get("heading", ""))
        body_raw = str(section.get("body", ""))
        if _normalize_heading(heading_raw) == _normalize_heading(body_raw):
            raise ValueError(
                f"source_mirror section body must not mirror heading verbatim: {heading_raw!r}"
            )
        normalized_heading = _normalize_heading(heading_raw)
        rank = outline_rank.get(normalized_heading, len(outline_rank))
        keyed_sections.append((rank, index, section))
    keyed_sections.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in keyed_sections]


def _normalize_heading(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _render_topic_section(
    *,
    section: dict[str, object],
    section_index: int,
    site_presentation_mode: str,
    claim_option_title_by_id: dict[str, str],
) -> str:
    heading = escape(str(section["heading"]))
    body = str(section["body"])
    sentence_bindings = sentence_claim_bindings(body)
    rendered_body = render_sentence_claim_body(
        sentence_bindings=sentence_bindings,
        section_index=section_index,
        site_presentation_mode=site_presentation_mode,
        claim_option_title_by_id=claim_option_title_by_id,
    )
    return f"<h2 class=\"topic-section-heading\">{heading}</h2><p class=\"topic-section-body\">{rendered_body}</p>"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text_file(path: Path, content: str, *, incremental: bool) -> None:
    if incremental and path.is_file() and path.read_text() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write_binary_file(path: Path, content: bytes, *, incremental: bool) -> None:
    if incremental and path.is_file() and path.read_bytes() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _reset_render_root_for_deterministic_build(*, render_root: Path, incremental: bool) -> None:
    if incremental or not render_root.exists():
        return
    if render_root.is_file():
        render_root.unlink()
        return
    shutil.rmtree(render_root)


def _render_pinned_parent_link(topic: dict[str, object]) -> str:
    pinned_parent_link = topic.get("pinned_parent_link")
    if not isinstance(pinned_parent_link, dict):
        return ""
    space_name = escape(str(pinned_parent_link.get("space_name", "")))
    topic_id = escape(str(pinned_parent_link.get("topic_id", "")))
    resolved = bool(pinned_parent_link.get("resolved"))
    if resolved:
        parent_space_name = escape(str(pinned_parent_link.get("parent_space_name", "")))
        parent_snapshot = escape(str(pinned_parent_link.get("parent_snapshot", "")))
        parent_site_base_url = escape(str(pinned_parent_link.get("parent_site_base_url", "")))
        parent_href = _render_parent_topic_href(
            parent_site_base_url=str(pinned_parent_link.get("parent_site_base_url", "")),
            parent_space_name=str(pinned_parent_link.get("parent_space_name", "")),
            topic_id=str(pinned_parent_link.get("topic_id", "")),
        )
        return (
            "<p class=\"pinned-parent-link\""
            + f" data-space-name=\"{space_name}\""
            + f" data-topic-id=\"{topic_id}\""
            + f" data-parent-space-name=\"{parent_space_name}\""
            + f" data-parent-snapshot=\"{parent_snapshot}\""
            + f" data-parent-site-base-url=\"{parent_site_base_url}\">"
            + f"Parent topic: <a href=\"{escape(parent_href)}\">{space_name}/{topic_id}</a></p>\n"
        )
    return (
        "<p class=\"pinned-parent-link disabled\" aria-disabled=\"true\""
        + f" data-space-name=\"{space_name}\""
        + f" data-topic-id=\"{topic_id}\">"
        + f"Parent topic unavailable: {space_name}/{topic_id} (unresolved pinned import)</p>\n"
    )


def _render_parent_topic_href(*, parent_site_base_url: str, parent_space_name: str, topic_id: str) -> str:
    normalized_base = parent_site_base_url.rstrip("/")
    if not normalized_base:
        return "#"
    return f"{normalized_base}/spaces/{parent_space_name}/site/topics/{topic_id}.html"


def _build_layout_context(
    *,
    space_root: Path,
    projection: SpaceProjection,
    site_path: Path,
) -> _SpaceLayoutContext:
    all_space_names = _discover_site_spaces(site_path)
    questions = load_prepared_questions(space_root)
    return _SpaceLayoutContext(
        site_name=_resolve_site_name(site_path),
        space_name=space_root.name,
        all_space_names=all_space_names,
        site_subspaces_by_space=_load_site_subspaces_by_space(
            site_path=site_path,
            space_names=all_space_names,
        ),
        subspaces=_load_subspaces(space_root),
        sources=sorted(projection.sources, key=lambda item: str(item.get("source_id", ""))),
        topics=sorted(projection.topics, key=lambda item: str(item.get("topic_id", ""))),
        questions=questions,
        overview=_load_space_overview_artifact(space_root=space_root, site_path=site_path),
        tabs=tuple(_resolve_space_tabs(space_root=space_root, questions=questions)),
    )


def _resolve_site_name(site_path: Path) -> str:
    try:
        scope = load_site_scope(site_path=site_path)
    except (FileNotFoundError, TypeError, ValueError):
        return site_path.name
    return scope.site_name


def _discover_site_spaces(site_path: Path) -> list[str]:
    spaces_root = site_path / "spaces"
    if not spaces_root.exists():
        return []
    all_space_names = sorted(path.name for path in spaces_root.iterdir() if path.is_dir())
    if not all_space_names:
        return []

    declared_subspace_names: set[str] = set()
    known_space_names = set(all_space_names)
    for space_name in all_space_names:
        space_root = spaces_root / space_name
        try:
            metadata = load_subspaces_metadata(space_root=space_root)
        except (FileNotFoundError, TypeError, ValueError):
            continue
        for entry in metadata.subspaces:
            if entry.space_name in known_space_names:
                declared_subspace_names.add(entry.space_name)

    return [space_name for space_name in all_space_names if space_name not in declared_subspace_names]


def _top_level_site_space_names(
    *,
    space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
) -> list[str]:
    declared_subspace_names = {
        subspace_name
        for subspaces in subspaces_by_space.values()
        for subspace_name, _title in subspaces
    }
    return [space_name for space_name in sorted(space_names) if space_name not in declared_subspace_names]


def _load_subspaces(space_root: Path) -> list[tuple[str, str | None]]:
    try:
        metadata = load_subspaces_metadata(space_root=space_root)
    except FileNotFoundError:
        return []
    return sorted((entry.space_name, entry.title) for entry in metadata.subspaces)


def _load_site_subspaces_by_space(
    *,
    site_path: Path,
    space_names: list[str],
) -> dict[str, list[tuple[str, str | None]]]:
    spaces_root = site_path / "spaces"
    mapping: dict[str, list[tuple[str, str | None]]] = {}
    for space_name in sorted(space_names):
        mapping[space_name] = _load_subspaces(spaces_root / space_name)
    return mapping


def _resolve_space_tabs(*, space_root: Path, questions: list[PreparedQuestion]) -> list[str]:
    del space_root, questions
    return ["new", "questions", "sources", "topics", "users"]


def _load_space_overview_artifact(
    *,
    space_root: Path,
    site_path: Path,
) -> _SpaceOverviewArtifact | None:
    scope = resolve_overview_scope(site_path=site_path, space_name=space_root.name)
    overview_path = space_root / "outputs" / "space_overview" / scope.overview_id / "overview.json"
    if not overview_path.is_file():
        return None

    payload = json.loads(overview_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Overview artifact must be a JSON object: {overview_path}")

    metadata = payload.get("metadata")
    references = payload.get("references")
    sections = payload.get("sections")
    warnings = payload.get("warnings")
    if not isinstance(metadata, dict):
        raise ValueError(f"Overview artifact metadata must be an object: {overview_path}")
    if not isinstance(references, dict):
        raise ValueError(f"Overview artifact references must be an object: {overview_path}")
    if not isinstance(sections, list):
        raise ValueError(f"Overview artifact sections must be a list: {overview_path}")
    if not isinstance(warnings, list):
        raise ValueError(f"Overview artifact warnings must be a list: {overview_path}")
    citation_anchors = references.get("citation_anchors")
    if not isinstance(citation_anchors, list):
        raise ValueError(f"Overview artifact citation_anchors must be a list: {overview_path}")

    title = str(metadata.get("title") or "").strip()
    summary = str(metadata.get("summary") or "").strip()
    if not title or not summary:
        raise ValueError(f"Overview artifact must include non-empty title and summary: {overview_path}")

    return _SpaceOverviewArtifact(
        overview_id=str(metadata.get("overview_id") or scope.overview_id),
        title=title,
        summary=summary,
        scope_kind=str(metadata.get("scope_kind") or scope.scope_kind),
        scope_name=str(metadata.get("scope_name") or scope.scope_name),
        sections=tuple(section for section in sections if isinstance(section, dict)),
        source_ids=tuple(_normalized_string_rows(references.get("source_ids"))),
        claim_ids=tuple(_normalized_string_rows(references.get("claim_ids"))),
        citation_anchors=tuple(row for row in citation_anchors if isinstance(row, dict)),
        warnings=tuple(_normalized_string_rows(warnings)),
    )


def _normalized_string_rows(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    rows: list[str] = []
    for item in value:
        normalized = str(item).strip()
        if normalized:
            rows.append(normalized)
    return rows


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_persona_rows() -> list[dict[str, Any]]:
    repo_root = _repo_root()
    rows = load_seeded_persona_catalog(repo_root=repo_root)
    return sorted(rows, key=lambda row: str(row["persona_id"]))


def _persona_avatar_site_href(*, space_name: str, persona_id: str) -> str:
    if not persona_id or persona_id not in _persona_ids():
        return ""
    return f"/spaces/{space_name}/site/assets/persona_avatars/{persona_id}.jpg"


def _persona_profile_photo_site_href(*, space_name: str, persona_id: str) -> str:
    if not persona_id or persona_id not in _persona_ids():
        return ""
    return f"/spaces/{space_name}/site/assets/persona_profiles/{persona_id}.jpg"


def _write_space_overview_page(
    *,
    output_root: Path,
    context: _SpaceLayoutContext,
    incremental: bool,
) -> list[Path]:
    overview_root = output_root / "overview"
    overview_root.mkdir(parents=True, exist_ok=True)
    page_path = overview_root / "index.html"
    display_space_name = _space_display_name(context.space_name)
    if context.overview is None:
        body = (
            "<h1>Overview</h1>\n"
            + "<p>No overview has been generated for this space yet.</p>\n"
            + "<p><a href=\"../index.html\">Back to home</a></p>\n"
        )
    else:
        body = _render_space_overview_page_body(
            overview=context.overview,
            display_space_name=display_space_name,
        )
    _write_text_file(
        page_path,
        _render_space_layout(
            title=f"{display_space_name} - Overview",
            body=body,
            context=context,
            current_tab="overview",
            current_page="overview",
            stylesheet_href=_relative_href(
                from_file=page_path,
                to_file=output_root / "assets" / "site.css",
            ),
        ),
        incremental=incremental,
    )
    return [page_path]


def _render_space_overview_page_body(
    *,
    overview: _SpaceOverviewArtifact,
    display_space_name: str,
) -> str:
    body_parts = [
        "<article class=\"topic-article overview-article\">",
        "<header class=\"overview-header\">",
        "<h1>Overview</h1>\n",
        "<p class=\"space-overview-title\">",
        escape(overview.title),
        "</p>\n",
        "<p class=\"space-overview-summary\">",
        escape(overview.summary),
        "</p>\n",
        "<p class=\"space-overview-meta\">",
        escape(
            " | ".join(
                [
                    f"Scope: {overview.scope_kind}",
                    f"Sources: {len(overview.source_ids)}",
                    f"Claims: {len(overview.claim_ids)}",
                    f"Citation anchors: {len(overview.citation_anchors)}",
                ]
            )
        ),
        "</p>\n",
        "</header>",
    ]
    if overview.warnings:
        body_parts.extend(
            [
                "<section class=\"source-related-card\">",
                "<h2>Warnings</h2>",
                "<ul class=\"source-related-list\">",
                "".join(f"<li>{escape(warning)}</li>" for warning in overview.warnings),
                "</ul>",
                "</section>",
            ]
        )

    for section in overview.sections:
        heading = str(section.get("heading") or "").strip()
        body = str(section.get("body") or "").strip()
        section_id = str(section.get("section_id") or "").strip()
        if not heading or not body or not section_id:
            continue
        body_parts.extend(
            [
                "<section class=\"source-related-card overview-section\" data-section-id=\"",
                escape(section_id),
                "\">",
                "<h2>",
                escape(heading),
                "</h2>\n",
                _render_overview_body_paragraphs(body),
                _render_overview_section_reference_summary(section=section),
                "</section>",
            ]
        )

    body_parts.append(
        _render_overview_reference_card(overview=overview, display_space_name=display_space_name)
    )
    body_parts.append("</article>")
    return "".join(body_parts)


def _render_overview_body_paragraphs(body: str) -> str:
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", body) if chunk.strip()]
    if not paragraphs and body.strip():
        paragraphs = [body.strip()]
    return "".join(f"<p>{escape(paragraph)}</p>\n" for paragraph in paragraphs if paragraph)


def _render_overview_section_reference_summary(*, section: dict[str, Any]) -> str:
    source_ids = _normalized_string_rows(section.get("source_ids"))
    claim_ids = _normalized_string_rows(section.get("claim_ids"))
    citation_anchor_ids = _normalized_string_rows(section.get("citation_anchor_ids"))
    rows: list[str] = []
    if source_ids:
        rows.append(
            "<li>Sources: "
            + ", ".join(
                f"<a href=\"../sources/{escape(source_id)}.html\">{escape(source_id)}</a>"
                for source_id in source_ids
            )
            + "</li>"
        )
    if claim_ids:
        rows.append(
            "<li>Claims: "
            + ", ".join(
                f"<a href=\"../claims/{escape(claim_id)}.html\">{escape(claim_id)}</a>"
                for claim_id in claim_ids
            )
            + "</li>"
        )
    if citation_anchor_ids:
        rows.append(
            "<li>Citation anchors: "
            + ", ".join(escape(anchor_id) for anchor_id in citation_anchor_ids)
            + "</li>"
        )
    if not rows:
        return ""
    return "<ul class=\"source-related-list overview-section-references\">" + "".join(rows) + "</ul>\n"


def _render_overview_reference_card(
    *,
    overview: _SpaceOverviewArtifact,
    display_space_name: str,
) -> str:
    source_rows = (
        "".join(
            "<li><a href=\"../sources/"
            + escape(source_id)
            + ".html\">"
            + escape(source_id)
            + "</a></li>"
            for source_id in overview.source_ids
        )
        if overview.source_ids
        else "<li>(No source references recorded.)</li>"
    )
    claim_rows = (
        "".join(
            "<li><a href=\"../claims/"
            + escape(claim_id)
            + ".html\">"
            + escape(claim_id)
            + "</a></li>"
            for claim_id in overview.claim_ids
        )
        if overview.claim_ids
        else "<li>(No claim references recorded.)</li>"
    )
    citation_rows = (
        "".join(
            "<li>"
            + escape(str(anchor.get("label") or ""))
            + (
                " ("
                + escape(str(anchor.get("locator") or ""))
                + ")"
                if str(anchor.get("locator") or "").strip()
                else ""
            )
            + " via <a href=\"../sources/"
            + escape(str(anchor.get("source_id") or ""))
            + ".html\">"
            + escape(str(anchor.get("source_id") or ""))
            + "</a></li>"
            for anchor in overview.citation_anchors
        )
        if overview.citation_anchors
        else "<li>(No citation anchors recorded.)</li>"
    )
    return (
        "<section class=\"source-related-card\">"
        "<h2>References</h2>"
        "<p>Canonical references for the current overview of "
        + escape(display_space_name)
        + ".</p>"
        "<h3>Sources</h3>"
        "<ul class=\"source-related-list\">"
        + source_rows
        + "</ul>"
        "<h3>Claims</h3>"
        "<ul class=\"source-related-list\">"
        + claim_rows
        + "</ul>"
        "<h3>Citation anchors</h3>"
        "<ul class=\"source-related-list\">"
        + citation_rows
        + "</ul>"
        "</section>"
    )


def _persona_profile_page_href(*, space_name: str, persona_id: str) -> str:
    if not persona_id or persona_id not in _persona_ids():
        return ""
    return f"/spaces/{space_name}/site/users/persona-{persona_id}.html"


@lru_cache(maxsize=1)
def _persona_ids() -> set[str]:
    return {str(row["persona_id"]) for row in _load_persona_rows()}


@lru_cache(maxsize=1)
def _persona_label_by_id() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in _load_persona_rows():
        persona_id = str(row.get("persona_id") or "").strip()
        if not persona_id:
            continue
        display_name = str(row.get("display_name") or "").strip()
        full_name = str(row.get("full_name") or "").strip()
        mapping[persona_id] = display_name or full_name or persona_id
    return mapping


def _persona_label(*, persona_id: str) -> str:
    if not persona_id:
        return "anonymous"
    return _persona_label_by_id().get(persona_id, persona_id)


def _space_feed_entries(
    *,
    space_name: str,
    projection: SpaceProjection,
    site_path: Path,
    require_cross_source_topics: bool = True,
    topic_evidence_count_by_id: dict[str, int] | None = None,
) -> list[_FeedEntry]:
    entries: list[_FeedEntry] = []
    source_preview_by_id: dict[str, str] = {}
    source_author_identities_by_id: dict[str, list[_AuthorIdentity]] = {}
    source_timestamp_by_id: dict[str, str] = {}
    for source in projection.sources:
        source_id = str(source["source_id"])
        source_preview_href = _source_preview_site_href_for_source(
            source=source,
            space_name=space_name,
            site_path=site_path,
        )
        source_timestamp = str(source.get("ingested_at") or source.get("date") or "")
        source_date_inference = source.get("source_date_inference")
        inferred_source_date = (
            str(source_date_inference.get("date") or "").strip()
            if isinstance(source_date_inference, dict)
            else ""
        )
        source_display_timestamp = str(source.get("date") or "").strip() or inferred_source_date
        source_preview_by_id[source_id] = source_preview_href
        source_timestamp_by_id[source_id] = source_timestamp
        source_author_identities = _source_author_identities(source)
        source_author_identities_by_id[source_id] = source_author_identities
        entries.append(
            _FeedEntry(
                timestamp=source_timestamp,
                display_timestamp=source_display_timestamp,
                space_name=space_name,
                item_type="source",
                item_id=source_id,
                title=_source_display_title(source),
                summary=_source_card_overview(source),
                authors=_author_refs(source_author_identities),
                source_preview_href=source_preview_href,
                citation_count=_parse_nonnegative_float(source.get("citation_count")),
            )
        )
    for topic in projection.topics:
        summary = _topic_card_overview(topic)
        source_ids = [
            str(value).strip()
            for value in topic.get("source_ids", [])
            if isinstance(value, str) and str(value).strip()
        ]
        # New feeds only surface cross-source topics, but space home pages should show every local topic.
        if require_cross_source_topics and len(source_ids) < 2:
            continue
        topic_id = str(topic["topic_id"])
        claim_ids = _collect_claim_ids_from_topic(topic=topic)
        topic_timestamp = str(topic.get("updated_at") or topic.get("created_at") or "").strip()
        if not topic_timestamp:
            topic_timestamp = max(
                (source_timestamp_by_id.get(source_id, "") for source_id in source_ids),
                default="",
            )
        entries.append(
            _FeedEntry(
                timestamp=topic_timestamp,
                display_timestamp=topic_timestamp,
                space_name=space_name,
                item_type="topic",
                item_id=topic_id,
                title=str(topic["title"]),
                summary=_sanitize_card_overview(summary),
                authors=_author_refs(
                    _topic_author_identities(
                        topic=topic,
                        source_author_identities_by_id=source_author_identities_by_id,
                    )
                ),
                source_preview_href=None,
                evidence_count=(topic_evidence_count_by_id or {}).get(topic_id, 0),
                claim_count=len(claim_ids),
                source_count=len(source_ids),
            )
        )
    return entries


def _sort_feed_entries(entries: list[_FeedEntry]) -> None:
    entries.sort(key=lambda item: (item.space_name, item.item_type, item.item_id))
    entries.sort(key=lambda item: item.timestamp, reverse=True)


def _sort_mode_path(
    *,
    mode: tuple[str, str, str, str, str],
    direction: str | None = None,
) -> str:
    sort_key, _label, desc_path, asc_path, default_direction = mode
    del sort_key
    resolved_direction = direction or default_direction
    return asc_path if resolved_direction == "asc" else desc_path


def _opposite_direction(direction: str) -> str:
    return "asc" if direction == "desc" else "desc"


def _sort_direction_arrow(direction: str) -> str:
    return "↑" if direction == "asc" else "↓"


def _render_order_controls(
    *,
    label: str,
    space_name: str,
    modes: tuple[tuple[str, str, str, str, str], ...],
    current_sort_key: str,
    current_direction: str,
) -> str:
    links: list[str] = []
    for mode in modes:
        sort_key, mode_label, _desc_path, _asc_path, default_direction = mode
        is_current = sort_key == current_sort_key
        direction = current_direction if is_current else default_direction
        target_direction = _opposite_direction(current_direction) if is_current else default_direction
        classes = "source-order-link"
        if is_current:
            classes += " current"
        link_label = mode_label + (f" {_sort_direction_arrow(direction)}" if is_current else "")
        links.append(
            "<a class=\""
            + escape(classes)
            + "\" href=\"/spaces/"
            + escape(space_name)
            + "/site/"
            + escape(_sort_mode_path(mode=mode, direction=target_direction))
            + "/index.html\">"
            + escape(link_label)
            + "</a>"
        )
    return (
        "<nav class=\"source-order-controls\" aria-label=\""
        + escape(label)
        + "\">"
        + "<span class=\"source-order-label\">Order</span>"
        + "".join(links)
        + "</nav>\n"
    )


def _render_site_order_controls(
    *,
    label: str,
    modes: tuple[tuple[str, str, str, str, str], ...],
    current_sort_key: str,
    current_direction: str,
) -> str:
    links: list[str] = []
    for mode in modes:
        sort_key, mode_label, _desc_path, _asc_path, default_direction = mode
        is_current = sort_key == current_sort_key
        direction = current_direction if is_current else default_direction
        target_direction = _opposite_direction(current_direction) if is_current else default_direction
        classes = "source-order-link"
        if is_current:
            classes += " current"
        link_label = mode_label + (f" {_sort_direction_arrow(direction)}" if is_current else "")
        links.append(
            "<a class=\""
            + escape(classes)
            + "\" href=\"/site/"
            + escape(_sort_mode_path(mode=mode, direction=target_direction))
            + "/index.html\">"
            + escape(link_label)
            + "</a>"
        )
    return (
        "<nav class=\"source-order-controls\" aria-label=\""
        + escape(label)
        + "\">"
        + "<span class=\"source-order-label\">Order</span>"
        + "".join(links)
        + "</nav>\n"
    )


def _sorted_source_feed_entries(
    entries: list[_FeedEntry],
    *,
    sort_key: str,
    direction: str = "desc",
) -> list[_FeedEntry]:
    sorted_entries = list(entries)
    if sort_key == "citation_count":
        sorted_entries.sort(
            key=lambda item: (
                item.citation_count is None,
                (
                    -(item.citation_count or 0.0)
                    if direction == "desc"
                    else (item.citation_count or 0.0)
                ),
                item.title.casefold(),
                item.item_id,
            )
        )
        return sorted_entries
    if sort_key == "title":
        sorted_entries.sort(
            key=lambda item: (item.title.casefold(), item.item_id),
            reverse=direction == "desc",
        )
        return sorted_entries
    sorted_entries.sort(key=lambda item: (item.title.casefold(), item.item_id))
    if direction == "desc":
        sorted_entries.sort(key=lambda item: item.display_timestamp or item.timestamp, reverse=True)
    else:
        sorted_entries.sort(
            key=lambda item: (
                not (item.display_timestamp or item.timestamp),
                item.display_timestamp or item.timestamp,
            )
        )
    return sorted_entries


def _sorted_topic_feed_entries(
    entries: list[_FeedEntry],
    *,
    sort_key: str,
    direction: str = "desc",
) -> list[_FeedEntry]:
    sorted_entries = list(entries)
    if sort_key == "evidence_count":
        sorted_entries.sort(key=lambda item: (item.title.casefold(), item.item_id))
        sorted_entries.sort(key=lambda item: item.evidence_count or 0, reverse=direction == "desc")
        return sorted_entries
    if sort_key == "claim_count":
        sorted_entries.sort(key=lambda item: (item.title.casefold(), item.item_id))
        sorted_entries.sort(key=lambda item: item.claim_count or 0, reverse=direction == "desc")
        return sorted_entries
    if sort_key == "title":
        sorted_entries.sort(
            key=lambda item: (item.title.casefold(), item.item_id),
            reverse=direction == "desc",
        )
        return sorted_entries
    sorted_entries.sort(key=lambda item: (item.title.casefold(), item.item_id))
    if direction == "desc":
        sorted_entries.sort(key=lambda item: item.display_timestamp or item.timestamp, reverse=True)
    else:
        sorted_entries.sort(
            key=lambda item: (
                not (item.display_timestamp or item.timestamp),
                item.display_timestamp or item.timestamp,
            )
        )
    return sorted_entries


def _sorted_feed_entries(
    entries: list[_FeedEntry],
    *,
    sort_key: str,
    direction: str,
) -> list[_FeedEntry]:
    sorted_entries = list(entries)
    if sort_key == "title":
        sorted_entries.sort(
            key=lambda item: (item.title.casefold(), item.item_id),
            reverse=direction == "desc",
        )
        return sorted_entries
    if sort_key == "type":
        sorted_entries.sort(
            key=lambda item: (item.item_type, item.title.casefold(), item.item_id),
            reverse=direction == "desc",
        )
        return sorted_entries
    sorted_entries.sort(key=lambda item: (item.title.casefold(), item.item_id))
    if direction == "desc":
        sorted_entries.sort(key=lambda item: item.display_timestamp or item.timestamp, reverse=True)
    else:
        sorted_entries.sort(
            key=lambda item: (
                not (item.display_timestamp or item.timestamp),
                item.display_timestamp or item.timestamp,
            )
        )
    return sorted_entries


def _topic_evidence_count_by_id(*, evidence_records: list[_EvidenceRecord]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in evidence_records:
        for topic_id in record.topic_ids:
            counts[topic_id] = counts.get(topic_id, 0) + 1
    return counts


def _dedupe_ordered_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _compact_summary(text: str, *, limit: int = 120) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return ""
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_overview_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _topic_card_overview(topic: dict[str, Any]) -> str:
    summary = ""
    if isinstance(topic.get("card_overview"), str):
        summary = topic["card_overview"]
    elif isinstance(topic.get("summary"), str):
        summary = topic["summary"]
    else:
        sections = topic.get("sections")
        if isinstance(sections, list) and sections:
            first = sections[0]
            if isinstance(first, dict) and isinstance(first.get("body"), str):
                summary = first["body"]
    return _sanitize_card_overview(summary)


def _source_card_overview(source: dict[str, Any]) -> str:
    explicit = _sanitize_card_overview(str(source.get("card_overview") or ""))
    if explicit:
        return explicit
    source_dossier = source.get("source_dossier")
    if isinstance(source_dossier, dict):
        summary_short = _sanitize_card_overview(str(source_dossier.get("summary_short") or ""))
        if summary_short:
            return summary_short
        summary_long = str(source_dossier.get("summary_long") or "").strip()
        if summary_long:
            first_paragraph = summary_long.split("\n\n", 1)[0]
            normalized = _sanitize_card_overview(first_paragraph)
            if normalized:
                return normalized
    summary_fallback = _sanitize_card_overview(str(source.get("summary") or source.get("context") or ""))
    return summary_fallback


def _sanitize_card_overview(text: str) -> str:
    without_claim_markers = re.sub(r"\[\[claims:[^\]]+\]\]", "", text)
    return _normalize_overview_text(without_claim_markers)


def _normalize_author_name(name: str) -> str:
    normalized = re.sub(r"\s+", " ", name).strip(" ,;")
    if normalized.endswith("'s"):
        normalized = normalized[:-2].rstrip()
    return normalized


def _normalize_institution_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ,;")


def _split_author_text(raw: str) -> list[str]:
    text = _normalize_author_name(raw)
    if not text:
        return []
    text = text.replace("&", " and ")
    separators = [";", ", and ", " and ", ","]
    parts = [text]
    for separator in separators:
        next_parts: list[str] = []
        split = False
        for part in parts:
            if separator in part:
                split = True
                next_parts.extend(part.split(separator))
            else:
                next_parts.append(part)
        if split:
            parts = next_parts
    normalized_parts = [_normalize_author_name(part) for part in parts]
    return [part for part in normalized_parts if part]


def _extract_author_names(raw_authors: Any) -> list[str]:
    if isinstance(raw_authors, list):
        candidates: list[str] = []
        for item in raw_authors:
            candidates.extend(_split_author_text(str(item)))
        return _dedupe_ordered_strings(candidates)
    if isinstance(raw_authors, str):
        return _dedupe_ordered_strings(_split_author_text(raw_authors))
    return []


def _extract_institution_text(raw: Any) -> str:
    if isinstance(raw, str):
        return _normalize_institution_name(raw)
    if isinstance(raw, list):
        parts = [_normalize_institution_name(str(item)) for item in raw if _normalize_institution_name(str(item))]
        return "; ".join(parts)
    return ""


def _extract_author_identities(raw_authors: Any, *, default_institution: str = "") -> list[_AuthorIdentity]:
    identities: list[_AuthorIdentity] = []
    normalized_default_institution = _normalize_institution_name(default_institution)
    if isinstance(raw_authors, list):
        for item in raw_authors:
            if isinstance(item, dict):
                raw_name = str(
                    item.get("name")
                    or item.get("full_name")
                    or item.get("display_name")
                    or item.get("author")
                    or ""
                ).strip()
                item_institution = (
                    _extract_institution_text(item.get("institution"))
                    or _extract_institution_text(item.get("affiliation"))
                    or _extract_institution_text(item.get("organization"))
                    or _extract_institution_text(item.get("org"))
                    or normalized_default_institution
                )
                for name in _split_author_text(raw_name):
                    identities.append(_AuthorIdentity(display_name=name, institution=item_institution))
                continue
            for name in _split_author_text(str(item)):
                identities.append(_AuthorIdentity(display_name=name, institution=normalized_default_institution))
        return _dedupe_author_identities(identities)
    if isinstance(raw_authors, str):
        for name in _split_author_text(raw_authors):
            identities.append(_AuthorIdentity(display_name=name, institution=normalized_default_institution))
        return _dedupe_author_identities(identities)
    return []


def _dedupe_author_identities(identities: list[_AuthorIdentity]) -> list[_AuthorIdentity]:
    deduped: list[_AuthorIdentity] = []
    seen: set[tuple[str, str]] = set()
    for identity in identities:
        display_name = _normalize_author_name(identity.display_name)
        institution = _normalize_institution_name(identity.institution)
        if not _is_plausible_author_name(display_name):
            continue
        key = (display_name.lower(), institution.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(_AuthorIdentity(display_name=display_name, institution=institution))
    return deduped


def _is_plausible_author_name(name: str) -> bool:
    normalized = _normalize_author_name(name)
    if not normalized:
        return False
    folded = normalized.casefold()
    if folded in {
        "the",
        "this",
        "that",
        "these",
        "those",
        "paper",
        "article",
        "study",
        "authors",
        "researchers",
        "team",
        "editorial synthesis",
        "unknown",
    }:
        return False
    if normalized.startswith("/"):
        return False
    return True


def _derive_authors_from_source_title(title: str) -> list[str]:
    normalized = title.strip().lower()
    if not normalized or not re.fullmatch(r"[a-z0-9_\-]+", normalized):
        return []
    tokens = [token for token in re.split(r"[_\-]+", normalized) if token]
    if len(tokens) < 2:
        return []
    if re.fullmatch(r"\d{4}", tokens[-1]):
        tokens = tokens[:-1]
    if not tokens:
        return []
    if len(tokens) > 6:
        tokens = tokens[:6]
    return [token.capitalize() for token in tokens]


def _source_default_institution(source: dict[str, Any]) -> str:
    source_semantic = source.get("source_semantic")
    if not isinstance(source_semantic, dict):
        return ""
    direct_institution = (
        _extract_institution_text(source_semantic.get("institution"))
        or _extract_institution_text(source_semantic.get("affiliation"))
        or _extract_institution_text(source_semantic.get("organization"))
    )
    if direct_institution:
        return direct_institution
    institutions = source_semantic.get("institutions")
    if isinstance(institutions, list):
        flattened = [_normalize_institution_name(str(value)) for value in institutions if _normalize_institution_name(str(value))]
        if len(flattened) == 1:
            return flattened[0]
    return ""


def _source_institutions_for_author_page(*, source: dict[str, Any], space_root: Path) -> set[str]:
    institutions: set[str] = set()
    default_institution = _source_default_institution(source)
    if default_institution:
        institutions.add(default_institution)
    institutions.update(_source_markdown_affiliation_institutions(source=source, space_root=space_root))
    return {institution for institution in institutions if institution}


def _source_markdown_affiliation_institutions(*, source: dict[str, Any], space_root: Path) -> set[str]:
    markdown_path = _source_artifact_path(
        source=source,
        artifact_key="source_markdown",
        space_root=space_root,
    )
    if markdown_path is None or not markdown_path.is_file():
        return set()
    lines = markdown_path.read_text(errors="replace").splitlines()
    candidates: set[str] = set()
    stop_markers = ("edited by:", "reviewed by:", "*correspondence:", "correspondence:", "abstract")
    institution_terms = (
        "university",
        "institute",
        "laboratory",
        "hospital",
        "school",
        "college",
        "department",
        "centre",
        "center",
    )
    for line in lines[:80]:
        normalized = _normalize_institution_name(line)
        if not normalized:
            continue
        folded = normalized.casefold()
        if any(marker in folded for marker in stop_markers):
            break
        if not any(term in folded for term in institution_terms):
            continue
        if "doi:" in folded or folded.startswith("#"):
            continue
        candidates.add(normalized)
    return candidates


def _source_artifact_path(
    *,
    source: dict[str, Any],
    artifact_key: str,
    space_root: Path,
) -> Path | None:
    artifacts = source.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    artifact_rel = artifacts.get(artifact_key)
    if not isinstance(artifact_rel, str) or not artifact_rel.strip():
        return None
    path = Path(artifact_rel.strip())
    if path.is_absolute():
        return path
    return space_root / path


def _source_publication_year(source: dict[str, Any]) -> int | None:
    for value in (
        source.get("date"),
        _source_semantic_publication_date(source),
        _source_inferred_date(source),
        source.get("ingested_at"),
    ):
        year = _year_from_date_value(value)
        if year is not None:
            return year
    return None


def _source_semantic_publication_date(source: dict[str, Any]) -> str:
    source_semantic = source.get("source_semantic")
    if not isinstance(source_semantic, dict):
        return ""
    return str(
        source_semantic.get("publication_date")
        or source_semantic.get("published_date")
        or source_semantic.get("date")
        or ""
    ).strip()


def _source_inferred_date(source: dict[str, Any]) -> str:
    source_date_inference = source.get("source_date_inference")
    if not isinstance(source_date_inference, dict):
        return ""
    return str(source_date_inference.get("date") or "").strip()


def _year_from_date_value(value: object) -> int | None:
    match = re.search(r"(?:^|[^\d])((?:19|20)\d{2})(?:[^\d]|$)", str(value or ""))
    if match is None:
        return None
    return int(match.group(1))


def _format_author_active_years(years: set[int]) -> str:
    if not years:
        return ""
    first = min(years)
    last = max(years)
    if first == last:
        return str(first)
    return f"{first}-{last}"


def _source_author_identities(source: dict[str, Any]) -> list[_AuthorIdentity]:
    default_institution = _source_default_institution(source)
    direct = _extract_author_identities(source.get("authors"), default_institution=default_institution)
    if direct:
        return direct
    references = source.get("references")
    if isinstance(references, list):
        for reference in references:
            if not isinstance(reference, dict):
                continue
            reference_authors = _extract_author_identities(
                reference.get("authors"),
                default_institution=default_institution,
            )
            if reference_authors:
                return reference_authors
    source_semantic = source.get("source_semantic")
    if isinstance(source_semantic, dict):
        semantic_authors = _extract_author_identities(
            source_semantic.get("authors"),
            default_institution=default_institution,
        )
        if semantic_authors:
            return semantic_authors
        semantic_author_text = source_semantic.get("author")
        if semantic_author_text:
            semantic_author_identities = _extract_author_identities(
                str(semantic_author_text),
                default_institution=default_institution,
            )
            if semantic_author_identities:
                return semantic_author_identities
    derived_from_summary = _derive_authors_from_summary(str(source.get("summary") or source.get("context") or ""))
    if derived_from_summary:
        return [_AuthorIdentity(display_name=name, institution=default_institution) for name in derived_from_summary]
    return []


def _topic_author_identities(
    *,
    topic: dict[str, Any],
    source_author_identities_by_id: dict[str, list[_AuthorIdentity]],
) -> list[_AuthorIdentity]:
    direct = _extract_author_identities(topic.get("authors"))
    if direct:
        return direct
    persona_id = str(topic.get("persona_id") or "").strip()
    if persona_id:
        return [_AuthorIdentity(display_name=_persona_label(persona_id=persona_id))]
    candidates: list[_AuthorIdentity] = []
    for source_id in topic.get("source_ids", []):
        if not isinstance(source_id, str):
            continue
        source_authors = source_author_identities_by_id.get(source_id, [])
        candidates.extend(source_authors)
    candidates = _dedupe_author_identities(candidates)
    if candidates:
        return candidates
    return [_AuthorIdentity(display_name="editorial synthesis")]


def _derive_authors_from_summary(summary: str) -> list[str]:
    lead = summary.strip()
    if not lead:
        return []
    patterns = (
        r"^([A-Z][A-Za-z.\-']*(?:\s+[A-Z][A-Za-z.\-']*){0,5}(?:,\s+[A-Z][A-Za-z.\-']*)*(?:,\s+and\s+[A-Z][A-Za-z.\-']*|\s+and\s+[A-Z][A-Za-z.\-']*)?)\s+"
        r"(?:argues?|shows?|proposes?|finds?|presents?|reports?|concludes?)\b",
        r"^([A-Z][A-Za-z.\-']*(?:\s+[A-Z][A-Za-z.\-']*){0,5})(?:'s)?\s+(?:article|paper|study)\s+"
        r"(?:argues?|shows?|proposes?|finds?|presents?|reports?|concludes?)\b",
    )
    for pattern in patterns:
        match = re.match(pattern, lead)
        if not match:
            continue
        authors = re.sub(r"\s+", " ", match.group(1)).strip(" ,")
        if authors.endswith("'s"):
            authors = authors[:-2].rstrip()
        if authors:
            return _extract_author_names(authors)
    return []


def _canonical_author_id_with_institution(*, name: str, institution: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_only = ascii_only.lower()
    ascii_only = re.sub(r"['’]", "", ascii_only)
    name_slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    if not institution:
        return f"author-{name_slug}" if name_slug else "author-unknown"
    normalized_institution = unicodedata.normalize("NFKD", institution)
    inst_ascii = "".join(ch for ch in normalized_institution if not unicodedata.combining(ch))
    inst_ascii = inst_ascii.lower()
    inst_ascii = re.sub(r"['’]", "", inst_ascii)
    inst_slug = re.sub(r"[^a-z0-9]+", "-", inst_ascii).strip("-")
    if name_slug and inst_slug:
        return f"author-{name_slug}-{inst_slug}"
    if name_slug:
        return f"author-{name_slug}"
    return f"author-{inst_slug}" if inst_slug else "author-unknown"


def _author_refs(author_identities: list[_AuthorIdentity]) -> tuple[_AuthorRef, ...]:
    refs: list[_AuthorRef] = []
    for identity in _dedupe_author_identities(author_identities):
        name = _normalize_author_name(identity.display_name)
        institution = _normalize_institution_name(identity.institution)
        if name.lower() == "editorial synthesis":
            continue
        refs.append(
            _AuthorRef(
                author_id=_canonical_author_id_with_institution(name=name, institution=institution),
                display_name=name,
                institution=institution,
            )
        )
    return tuple(refs)


def _feed_item_label(item_type: str) -> str:
    return item_type.capitalize() if item_type else "Item"


def _space_display_name(space_name: str) -> str:
    tokens = [token for token in re.split(r"[-_\s]+", space_name.strip()) if token]
    if not tokens:
        return space_name.strip()
    return " ".join(token[:1].upper() + token[1:] for token in tokens)


def _space_or_subspace_display_name(*, space_name: str, title: str | None) -> str:
    candidate = str(title or "").strip()
    if candidate:
        return _space_display_name(candidate)
    return _space_display_name(space_name)


def _format_feed_timestamp_for_ui(value: str) -> str:
    raw = value.strip()
    if not raw:
        return "unknown"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}$", raw):
        parsed = datetime.strptime(raw, "%Y-%m-%d")
        return parsed.strftime("%b %d, %Y")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", raw):
        parsed = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
        return parsed.strftime("%b %d, %Y")
    return raw


def _feed_item_href(entry: _FeedEntry) -> str:
    return f"/spaces/{entry.space_name}/site/{entry.item_type}s/{entry.item_id}.html"


def _render_feed_row(entry: _FeedEntry) -> str:
    title_href = _feed_item_href(entry)
    preview_thumb = _render_feed_preview_thumb(entry)
    authors_html = _render_feed_authors(entry=entry)
    citation_html = _render_feed_citation_count(entry=entry)
    topic_count_html = _render_feed_topic_counts(entry=entry)
    timestamp_for_display = (
        entry.display_timestamp
        if entry.item_type == "source"
        else (entry.display_timestamp or entry.timestamp)
    )
    header = (
        "<p class=\"feed-card-head\">"
        + "<a class=\"feed-card-title\" href=\""
        + escape(title_href)
        + "\">"
        + escape(entry.title)
        + "</a>"
        + "<span class=\"feed-card-date\">"
        + escape(_format_feed_timestamp_for_ui(timestamp_for_display))
        + "</span>"
        + "<span class=\"feed-card-type\">"
        + escape(_feed_item_label(entry.item_type))
        + "</span>"
        + citation_html
        + topic_count_html
        + authors_html
        + "</p>"
    )
    summary = (
        "<p class=\"feed-card-overview\">"
        + escape(entry.summary)
        + "</p>"
        if entry.summary
        else "<p class=\"feed-card-overview\">No overview available.</p>"
    )
    return (
        "<li class=\"feed-card\">"
        + "<div class=\"feed-card-layout\">"
        + preview_thumb
        + "<div class=\"feed-card-copy\">"
        + header
        + summary
        + "</div></div></li>"
    )


def _render_feed_authors(*, entry: _FeedEntry) -> str:
    if not entry.authors:
        return "<span class=\"feed-card-authors\">Authors: unknown</span>"
    visible_authors = entry.authors[:3]
    name_counts: dict[str, int] = {}
    for author in entry.authors:
        name_counts[author.display_name] = name_counts.get(author.display_name, 0) + 1

    def _label(author: _AuthorRef) -> str:
        if name_counts.get(author.display_name, 0) > 1 and author.institution:
            return f"{author.display_name} ({author.institution})"
        return author.display_name

    linked_names = ", ".join(
        (
            "<a class=\"feed-card-author\" href=\"/spaces/"
            + escape(entry.space_name)
            + "/site/authors/"
            + escape(author.author_id)
            + ".html\">"
            + escape(_label(author))
            + "</a>"
        )
        for author in visible_authors
    )
    if len(entry.authors) > len(visible_authors):
        linked_names += ', <span class="feed-card-author-overflow">...</span>'
    return "<span class=\"feed-card-authors\">Authors: " + linked_names + "</span>"


def _render_feed_citation_count(*, entry: _FeedEntry) -> str:
    if entry.item_type != "source" or entry.citation_count is None:
        return ""
    return (
        "<span class=\"feed-card-citations\">Citations: "
        + escape(_format_citation_count_for_ui(entry.citation_count))
        + "</span>"
    )


def _render_feed_topic_counts(*, entry: _FeedEntry) -> str:
    if entry.item_type != "topic":
        return ""
    return (
        "<span class=\"feed-card-counts\">Evidence: "
        + escape(str(entry.evidence_count or 0))
        + "</span>"
        + "<span class=\"feed-card-counts\">Claims: "
        + escape(str(entry.claim_count or 0))
        + "</span>"
    )


def _render_source_order_controls(
    *,
    space_name: str,
    current_sort_key: str,
    current_direction: str,
) -> str:
    return _render_order_controls(
        label="Source order",
        space_name=space_name,
        modes=SOURCE_SORT_MODES,
        current_sort_key=current_sort_key,
        current_direction=current_direction,
    )


def _render_topic_order_controls(
    *,
    space_name: str,
    current_sort_key: str,
    current_direction: str,
) -> str:
    return _render_order_controls(
        label="Topic order",
        space_name=space_name,
        modes=TOPIC_SORT_MODES,
        current_sort_key=current_sort_key,
        current_direction=current_direction,
    )


def _write_space_tab_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    persona_rows: list[dict[str, Any]],
    evidence_records: list[_EvidenceRecord],
    incremental: bool,
) -> list[Path]:
    written: list[Path] = []
    display_space_name = _space_display_name(context.space_name)
    site_path = output_root.parents[2]
    topic_evidence_counts = _topic_evidence_count_by_id(evidence_records=evidence_records)
    feed_entries = _space_feed_entries(
        space_name=context.space_name,
        projection=projection,
        site_path=site_path,
        topic_evidence_count_by_id=topic_evidence_counts,
    )
    _sort_feed_entries(feed_entries)
    source_feed_entries = [entry for entry in feed_entries if entry.item_type == "source"]
    topic_feed_entries = [
        entry
        for entry in _space_feed_entries(
            space_name=context.space_name,
            projection=projection,
            site_path=site_path,
            require_cross_source_topics=False,
            topic_evidence_count_by_id=topic_evidence_counts,
        )
        if entry.item_type == "topic"
    ]

    user_rows_by_name = [
        (
            str(row["display_name"]).casefold(),
            (
                "<a class=\"user-card\" href=\"/spaces/"
                + escape(context.space_name)
                + "/site/users/persona-"
                + escape(str(row["persona_id"]))
                + ".html\">"
                + "<img class=\"user-card-photo\" src=\"/spaces/"
                + escape(context.space_name)
                + "/site/assets/persona_profiles/"
                + escape(str(row["persona_id"]))
                + ".jpg\" alt=\"Profile photo for "
                + escape(str(row["display_name"]))
                + "\" loading=\"lazy\" />"
                + "<span class=\"user-card-name\">"
                + escape(str(row["display_name"]))
                + "</span>"
                + "</a>"
            ),
        )
        for row in persona_rows
    ]

    tab_rows: dict[str, list[str]] = {}

    for tab_key in context.tabs:
        if tab_key == "questions":
            continue
        if tab_key == "sources":
            for mode in SOURCE_SORT_MODES:
                sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
                for direction in ("desc", "asc"):
                    sort_path = _sort_mode_path(mode=mode, direction=direction)
                    rows = [
                        _render_feed_row(entry)
                        for entry in _sorted_source_feed_entries(
                            source_feed_entries,
                            sort_key=sort_key,
                            direction=direction,
                        )
                    ]
                    tab_root = output_root / sort_path
                    tab_root.mkdir(parents=True, exist_ok=True)
                    pages = _paginate(rows, TAB_PAGE_SIZE)
                    for page_number, page_rows in enumerate(pages, start=1):
                        page_path = _paginated_page_path(tab_root, page_number=page_number)
                        pagination = _render_pagination(
                            page_number=page_number,
                            page_count=len(pages),
                            mode="tab",
                            base_href=f"/spaces/{context.space_name}/site/{sort_path}",
                        )
                        content = (
                            _render_source_order_controls(
                                space_name=context.space_name,
                                current_sort_key=sort_key,
                                current_direction=direction,
                            )
                            + "<ul class=\"feed-list\">\n"
                            + ("\n".join(page_rows) if page_rows else "<li>(none yet)</li>")
                            + "\n</ul>\n"
                        )
                        body = (
                            "<h1>Sources</h1>\n"
                            + f"<p class=\"tab-page-size\" data-tab-page-size=\"{TAB_PAGE_SIZE}\">Page size: {TAB_PAGE_SIZE}</p>\n"
                            + content
                            + pagination
                        )
                        _write_text_file(
                            page_path,
                            _render_space_layout(
                                title=f"{display_space_name} - Sources by {sort_label.lower()}",
                                body=body,
                                context=context,
                                current_tab=tab_key,
                                stylesheet_href=_relative_href(
                                    from_file=page_path,
                                    to_file=output_root / "assets" / "site.css",
                                ),
                            ),
                            incremental=incremental,
                        )
                        written.append(page_path)
            continue
        if tab_key == "topics":
            for mode in TOPIC_SORT_MODES:
                sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
                for direction in ("desc", "asc"):
                    sort_path = _sort_mode_path(mode=mode, direction=direction)
                    rows = [
                        _render_feed_row(entry)
                        for entry in _sorted_topic_feed_entries(
                            topic_feed_entries,
                            sort_key=sort_key,
                            direction=direction,
                        )
                    ]
                    tab_root = output_root / sort_path
                    tab_root.mkdir(parents=True, exist_ok=True)
                    pages = _paginate(rows, TAB_PAGE_SIZE)
                    for page_number, page_rows in enumerate(pages, start=1):
                        page_path = _paginated_page_path(tab_root, page_number=page_number)
                        pagination = _render_pagination(
                            page_number=page_number,
                            page_count=len(pages),
                            mode="tab",
                            base_href=f"/spaces/{context.space_name}/site/{sort_path}",
                        )
                        content = (
                            _render_topic_order_controls(
                                space_name=context.space_name,
                                current_sort_key=sort_key,
                                current_direction=direction,
                            )
                            + "<ul class=\"feed-list\">\n"
                            + ("\n".join(page_rows) if page_rows else "<li>(none yet)</li>")
                            + "\n</ul>\n"
                        )
                        body = (
                            "<h1>Topics</h1>\n"
                            + f"<p class=\"tab-page-size\" data-tab-page-size=\"{TAB_PAGE_SIZE}\">Page size: {TAB_PAGE_SIZE}</p>\n"
                            + content
                            + pagination
                        )
                        _write_text_file(
                            page_path,
                            _render_space_layout(
                                title=f"{display_space_name} - Topics by {sort_label.lower()}",
                                body=body,
                                context=context,
                                current_tab=tab_key,
                                stylesheet_href=_relative_href(
                                    from_file=page_path,
                                    to_file=output_root / "assets" / "site.css",
                                ),
                            ),
                            incremental=incremental,
                        )
                        written.append(page_path)
            continue
        if tab_key == "new":
            for mode in NEW_SORT_MODES:
                sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
                for direction in ("desc", "asc"):
                    sort_path = _sort_mode_path(mode=mode, direction=direction)
                    rows = [
                        _render_feed_row(entry)
                        for entry in _sorted_feed_entries(
                            feed_entries,
                            sort_key=sort_key,
                            direction=direction,
                        )
                    ]
                    tab_root = output_root / sort_path
                    tab_root.mkdir(parents=True, exist_ok=True)
                    pages = _paginate(rows, TAB_PAGE_SIZE)
                    for page_number, page_rows in enumerate(pages, start=1):
                        page_path = _paginated_page_path(tab_root, page_number=page_number)
                        pagination = _render_pagination(
                            page_number=page_number,
                            page_count=len(pages),
                            mode="tab",
                            base_href=f"/spaces/{context.space_name}/site/{sort_path}",
                        )
                        content = (
                            _render_order_controls(
                                label="New order",
                                space_name=context.space_name,
                                modes=NEW_SORT_MODES,
                                current_sort_key=sort_key,
                                current_direction=direction,
                            )
                            + "<ul class=\"feed-list\">\n"
                            + ("\n".join(page_rows) if page_rows else "<li>(none yet)</li>")
                            + "\n</ul>\n"
                        )
                        body = (
                            "<h1>New</h1>\n"
                            + f"<p class=\"tab-page-size\" data-tab-page-size=\"{TAB_PAGE_SIZE}\">Page size: {TAB_PAGE_SIZE}</p>\n"
                            + content
                            + pagination
                        )
                        _write_text_file(
                            page_path,
                            _render_space_layout(
                                title=f"{display_space_name} - New by {sort_label.lower()}",
                                body=body,
                                context=context,
                                current_tab=tab_key,
                                stylesheet_href=_relative_href(
                                    from_file=page_path,
                                    to_file=output_root / "assets" / "site.css",
                                ),
                            ),
                            incremental=incremental,
                        )
                        written.append(page_path)
            continue
        if tab_key == "users":
            for mode in USER_SORT_MODES:
                sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
                for direction in ("desc", "asc"):
                    sort_path = _sort_mode_path(mode=mode, direction=direction)
                    sorted_user_rows = sorted(
                        user_rows_by_name,
                        key=lambda row: row[0],
                        reverse=direction == "desc",
                    )
                    rows = [row_html for _name, row_html in sorted_user_rows]
                    tab_root = output_root / sort_path
                    tab_root.mkdir(parents=True, exist_ok=True)
                    pages = _paginate(rows, TAB_PAGE_SIZE)
                    for page_number, page_rows in enumerate(pages, start=1):
                        page_path = _paginated_page_path(tab_root, page_number=page_number)
                        pagination = _render_pagination(
                            page_number=page_number,
                            page_count=len(pages),
                            mode="tab",
                            base_href=f"/spaces/{context.space_name}/site/{sort_path}",
                        )
                        content = (
                            _render_order_controls(
                                label="User order",
                                space_name=context.space_name,
                                modes=USER_SORT_MODES,
                                current_sort_key=sort_key,
                                current_direction=direction,
                            )
                            + "<div class=\"user-card-grid\">\n"
                            + ("\n".join(page_rows) if page_rows else "<p>(none yet)</p>")
                            + "\n</div>\n"
                        )
                        body = (
                            "<h1>Users</h1>\n"
                            + f"<p class=\"tab-page-size\" data-tab-page-size=\"{TAB_PAGE_SIZE}\">Page size: {TAB_PAGE_SIZE}</p>\n"
                            + content
                            + pagination
                        )
                        _write_text_file(
                            page_path,
                            _render_space_layout(
                                title=f"{display_space_name} - Users by {sort_label.lower()}",
                                body=body,
                                context=context,
                                current_tab=tab_key,
                                stylesheet_href=_relative_href(
                                    from_file=page_path,
                                    to_file=output_root / "assets" / "site.css",
                                ),
                            ),
                            incremental=incremental,
                        )
                        written.append(page_path)
            continue
        rows = tab_rows.get(tab_key, [])
        tab_title = tab_key.capitalize()
        tab_root = output_root / tab_key
        tab_root.mkdir(parents=True, exist_ok=True)
        pages = _paginate(rows, TAB_PAGE_SIZE)
        for page_number, page_rows in enumerate(pages, start=1):
            page_path = _paginated_page_path(tab_root, page_number=page_number)
            pagination = _render_pagination(
                page_number=page_number,
                page_count=len(pages),
                mode="tab",
                base_href=f"/spaces/{context.space_name}/site/{tab_key}",
            )
            if tab_key == "users":
                content = (
                    "<div class=\"user-card-grid\">\n"
                    + ("\n".join(page_rows) if page_rows else "<p>(none yet)</p>")
                    + "\n</div>\n"
                )
            else:
                content = (
                    "<ul class=\"feed-list\">\n"
                    + ("\n".join(page_rows) if page_rows else "<li>(none yet)</li>")
                    + "\n</ul>\n"
                )
            body = (
                f"<h1>{escape(tab_title)}</h1>\n"
                + f"<p class=\"tab-page-size\" data-tab-page-size=\"{TAB_PAGE_SIZE}\">Page size: {TAB_PAGE_SIZE}</p>\n"
                + content
                + pagination
            )
            _write_text_file(
                page_path,
                _render_space_layout(
                    title=f"{display_space_name} - {tab_title}",
                    body=body,
                    context=context,
                    current_tab=tab_key,
                    stylesheet_href=_relative_href(
                        from_file=page_path,
                        to_file=output_root / "assets" / "site.css",
                    ),
                ),
                incremental=incremental,
            )
            written.append(page_path)
    return written


def _collect_space_author_profiles(
    *,
    projection: SpaceProjection,
    space_root: Path,
) -> dict[str, _AuthorProfile]:
    profiles: dict[str, _AuthorProfile] = {}
    source_author_identities_by_id: dict[str, list[_AuthorIdentity]] = {}

    for source in projection.sources:
        source_id = str(source.get("source_id") or "").strip()
        if not source_id:
            continue
        author_identities = _source_author_identities(source)
        source_author_identities_by_id[source_id] = author_identities
        source_year = _source_publication_year(source)
        source_institutions = _source_institutions_for_author_page(
            source=source,
            space_root=space_root,
        )
        for ref in _author_refs(author_identities):
            profile = profiles.get(ref.author_id)
            if profile is None:
                profile = _AuthorProfile(author_id=ref.author_id, display_name=ref.display_name)
                profiles[ref.author_id] = profile
            profile.aliases.add(ref.display_name)
            if ref.institution:
                profile.institutions.add(ref.institution)
            profile.institutions.update(source_institutions)
            if source_year is not None:
                profile.source_years.add(source_year)
            profile.source_ids.add(source_id)

    for topic in projection.topics:
        topic_id = str(topic.get("topic_id") or "").strip()
        if not topic_id:
            continue
        author_identities = _topic_author_identities(
            topic=topic,
            source_author_identities_by_id=source_author_identities_by_id,
        )
        for ref in _author_refs(author_identities):
            profile = profiles.get(ref.author_id)
            if profile is None:
                profile = _AuthorProfile(author_id=ref.author_id, display_name=ref.display_name)
                profiles[ref.author_id] = profile
            profile.aliases.add(ref.display_name)
            if ref.institution:
                profile.institutions.add(ref.institution)
            profile.topic_ids.add(topic_id)

    return profiles


def _write_space_author_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    incremental: bool,
) -> list[Path]:
    profiles = _collect_space_author_profiles(
        projection=projection,
        space_root=output_root.parent,
    )
    if not profiles:
        return []

    source_title_by_id = {
        str(source.get("source_id") or ""): _source_display_title(source)
        for source in projection.sources
    }
    topic_title_by_id = {
        str(topic.get("topic_id") or ""): str(topic.get("title") or "").strip()
        for topic in projection.topics
    }

    authors_root = output_root / "authors"
    authors_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    sorted_profiles = sorted(
        profiles.values(),
        key=lambda profile: (profile.display_name.lower(), profile.author_id),
    )
    for profile in sorted_profiles:
        source_rows = [
            "<li><a href=\"/spaces/"
            + escape(context.space_name)
            + "/site/sources/"
            + escape(source_id)
            + ".html\">"
            + escape(source_title_by_id.get(source_id, source_id))
            + "</a></li>"
            for source_id in sorted(
                profile.source_ids,
                key=lambda value: source_title_by_id.get(value, value).lower(),
            )
        ]
        topic_rows = [
            "<li><a href=\"/spaces/"
            + escape(context.space_name)
            + "/site/topics/"
            + escape(topic_id)
            + ".html\">"
            + escape(topic_title_by_id.get(topic_id, topic_id))
            + "</a></li>"
            for topic_id in sorted(
                profile.topic_ids,
                key=lambda value: topic_title_by_id.get(value, value).lower(),
            )
        ]
        alias_rows = sorted(alias for alias in profile.aliases if alias and alias != profile.display_name)
        institution_rows = sorted(inst for inst in profile.institutions if inst)
        active_years = _format_author_active_years(profile.source_years)
        path = authors_root / f"{profile.author_id}.html"
        body = (
            f"<h1>{escape(profile.display_name)}</h1>\n"
            + f"<p class=\"meta\">author id: {escape(profile.author_id)}</p>\n"
            + (
                "<p class=\"meta\">Institutions: "
                + escape(", ".join(institution_rows))
                + "</p>\n"
                if institution_rows
                else ""
            )
            + (
                "<p class=\"meta\">Years active in this space: "
                + escape(active_years)
                + "</p>\n"
                if active_years
                else ""
            )
            + (
                "<p class=\"meta\">Also appears as: "
                + escape(", ".join(alias_rows))
                + "</p>\n"
                if alias_rows
                else ""
            )
            + "<section class=\"source-related-card\">\n"
            + "<h2>Sources</h2>\n"
            + "<ul class=\"source-related-list\">\n"
            + ("\n".join(source_rows) if source_rows else "<li>(none yet)</li>")
            + "\n</ul>\n"
            + "</section>\n"
            + "<section class=\"source-related-card\">\n"
            + "<h2>Topics</h2>\n"
            + "<ul class=\"source-related-list\">\n"
            + ("\n".join(topic_rows) if topic_rows else "<li>(none yet)</li>")
            + "\n</ul>\n"
            + "</section>\n"
        )
        _write_text_file(
            path,
            _render_space_layout(
                title=f"{_space_display_name(context.space_name)} - {profile.display_name}",
                body=body,
                context=context,
                current_tab=None,
                stylesheet_href=_relative_href(
                    from_file=path,
                    to_file=output_root / "assets" / "site.css",
                ),
            ),
            incremental=incremental,
        )
        written.append(path)
    return written


def _write_space_user_profile_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    persona_rows: list[dict[str, Any]],
    incremental: bool,
) -> list[Path]:
    users_root = output_root / "users"
    users_root.mkdir(parents=True, exist_ok=True)
    persona_comment_activity = _collect_persona_comment_activity(
        output_root=output_root,
        projection=projection,
    )
    written: list[Path] = []
    for row in persona_rows:
        persona_id = str(row["persona_id"])
        display_name = str(row["display_name"])
        profile_payload = _load_persona_profile_payload(
            space_root=output_root.parent,
            persona_id=persona_id,
        )
        biography_profile = (
            _profile_section_content(profile_payload, "Profile biography")
            or str(row.get("biography_profile") or "").strip()
        )
        profile_photo_href = _persona_profile_photo_site_href(
            space_name=context.space_name,
            persona_id=persona_id,
        )
        profile_photo = ""
        if profile_photo_href:
            profile_photo = (
                "<figure class=\"profile-photo-frame\">"
                + f"<img class=\"profile-photo\" src=\"{escape(profile_photo_href)}\" alt=\"Profile photo for {escape(display_name)}\" loading=\"lazy\" />"
                + "</figure>\n"
            )
        short_cv_items = [
            _render_profile_cv_item(entry)
            for entry in _profile_cv_entries(profile_payload=profile_payload, persona_row=row)
        ]
        activity_items = persona_comment_activity.get(persona_id, [])
        activity_rows = []
        for activity in activity_items:
            activity_rows.append(
                "<li>"
                + "<a href=\""
                + escape(activity["href"])
                + "\">"
                + escape(activity["page_title"])
                + "</a>"
                + "<p class=\"meta\">"
                + f"Score: {activity['score']}"
                + "</p>"
                + "<p class=\"summary\">"
                + escape(activity["body"])
                + "</p>"
                + "</li>"
            )
        comments_section = ""
        if activity_rows:
            comments_section = (
                "<section class=\"source-related-card\">\n"
                + "<h2>Comments by This User</h2>\n"
                + "<ul class=\"source-related-list\">\n"
                + "\n".join(activity_rows)
                + "\n</ul>\n"
                + "</section>\n"
            )
        path = users_root / f"persona-{persona_id}.html"
        body = (
            f"<h1>{escape(display_name)}</h1>\n"
            + "<section class=\"profile-biography\">\n"
            + "<div class=\"profile-biography-copy\">\n"
            + "<h2>Biography</h2>\n"
            + f"<p>{escape(biography_profile)}</p>\n"
            + "</div>\n"
            + profile_photo
            + "</section>\n"
            + "<section class=\"profile-cv\">\n"
            + "<h2>Short CV</h2>\n"
            + "<ol class=\"profile-cv-list\">\n"
            + ("\n".join(short_cv_items) if short_cv_items else "<li class=\"profile-cv-empty\">(none listed)</li>")
            + "\n</ol>\n"
            + "</section>\n"
            + comments_section
        )
        _write_text_file(
            path,
            _render_space_layout(
                title=f"{_space_display_name(context.space_name)} - {display_name if display_name else persona_id}",
                body=body,
                context=context,
                current_tab="users",
                stylesheet_href=_relative_href(
                    from_file=path,
                    to_file=output_root / "assets" / "site.css",
                ),
            ),
            incremental=incremental,
        )
        written.append(path)
    return written


def _load_persona_profile_payload(*, space_root: Path, persona_id: str) -> dict[str, Any]:
    profile_path = space_root / "profiles" / f"persona-{persona_id}.json"
    if not profile_path.is_file():
        return {}
    payload = json.loads(profile_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{profile_path} must contain a JSON object.")
    return payload


def _profile_section_content(profile_payload: dict[str, Any], title: str) -> str:
    sections = profile_payload.get("profile_sections")
    if not isinstance(sections, list):
        return ""
    expected_title = title.strip().casefold()
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_title = str(section.get("title") or "").strip().casefold()
        if section_title != expected_title:
            continue
        return str(section.get("content") or "").strip()
    return ""


def _profile_cv_entries(
    *,
    profile_payload: dict[str, Any],
    persona_row: dict[str, Any],
) -> list[dict[str, str]]:
    structured_entries = _profile_cv_entries_from_payload(profile_payload)
    if structured_entries:
        return structured_entries

    section_entries = _profile_cv_entries_from_section(
        _profile_section_content(profile_payload, "Short CV")
    )
    if section_entries:
        return section_entries

    short_cv = persona_row.get("short_cv")
    if isinstance(short_cv, list):
        return [
            _profile_cv_entry_from_text(str(item))
            for item in short_cv
            if str(item).strip()
        ]
    return []


def _profile_cv_entries_from_payload(profile_payload: dict[str, Any]) -> list[dict[str, str]]:
    entries = profile_payload.get("short_cv_entries")
    if not isinstance(entries, list):
        return []

    normalized_entries: list[dict[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        role = str(entry.get("role") or "").strip()
        organization = str(entry.get("organization") or "").strip()
        period = str(entry.get("period") or "").strip()
        description = str(entry.get("description") or "").strip()
        if not role:
            continue
        normalized_entries.append(
            {
                "role": role,
                "organization": organization,
                "period": period,
                "description": description,
            }
        )
    return normalized_entries


def _profile_cv_entries_from_section(content: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for line in content.splitlines():
        list_match = re.match(r"^\s*(?:[-*]|\d+[.)])\s*(.+)$", line)
        normalized = list_match.group(1).strip() if list_match else line.strip()
        if list_match is None and re.search(r"\([^)]*((?:19|20)\d{2}|present)[^)]*\)", normalized, re.IGNORECASE) is None:
            continue
        if normalized:
            entries.append(_profile_cv_entry_from_text(normalized))
    return entries


def _collect_persona_comment_activity(
    *,
    output_root: Path,
    projection: SpaceProjection,
) -> dict[str, list[dict[str, Any]]]:
    activity_by_persona: dict[str, list[dict[str, Any]]] = {}
    claim_records = _load_claim_records(space_root=output_root.parent)
    for topic in sorted(projection.topics, key=lambda item: str(item.get("topic_id") or "")):
        topic_id = str(topic.get("topic_id") or "").strip()
        if not topic_id:
            continue
        _extend_persona_comment_activity(
            activity_by_persona=activity_by_persona,
            page_payload=topic,
            page_ref_default=f"topic:{topic_id}",
            page_title=str(topic.get("title") or topic_id),
            page_href=f"../topics/{topic_id}.html",
        )
    for source in sorted(projection.sources, key=lambda item: str(item.get("source_id") or "")):
        source_id = str(source.get("source_id") or "").strip()
        if not source_id:
            continue
        _extend_persona_comment_activity(
            activity_by_persona=activity_by_persona,
            page_payload=source,
            page_ref_default=f"source:{source_id}",
            page_title=_source_display_title(source),
            page_href=f"../sources/{source_id}.html",
        )
    for claim_id in sorted(claim_records):
        claim_record = claim_records[claim_id]
        _extend_persona_comment_activity(
            activity_by_persona=activity_by_persona,
            page_payload=claim_record,
            page_ref_default=f"claim:{claim_id}",
            page_title=_claim_display_title(claim_id=claim_id, claim_record=claim_record),
            page_href=f"../claims/{claim_id}.html",
        )
    return activity_by_persona


def _extend_persona_comment_activity(
    *,
    activity_by_persona: dict[str, list[dict[str, Any]]],
    page_payload: dict[str, Any],
    page_ref_default: str,
    page_title: str,
    page_href: str,
) -> None:
    comment_section = page_payload.get("comment_section")
    if not isinstance(comment_section, dict):
        return
    comments = comment_section.get("comments")
    if not isinstance(comments, list):
        return
    page_ref = str(comment_section.get("page_ref") or page_ref_default)
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        persona_id = str(comment.get("persona_id") or "").strip()
        if not persona_id:
            continue
        comment_uid = str(comment.get("comment_uid") or "").strip()
        permalink = str(comment.get("permalink") or "").strip()
        anchor = permalink if permalink.startswith("#") else (f"#{comment_uid}" if comment_uid else "")
        body = " ".join(str(comment.get("body") or "").split()).strip()
        score = _resolve_comment_social_vote(page_ref=page_ref, comment=comment)["score"]
        activity_by_persona.setdefault(persona_id, []).append(
            {
                "href": page_href + anchor,
                "page_title": page_title,
                "body": body,
                "score": score,
            }
        )


def _render_profile_cv_item(entry: dict[str, str]) -> str:
    role = entry.get("role", "")
    organization = entry.get("organization", "")
    period = entry.get("period", "")
    description = entry.get("description", "")
    return (
        "<li class=\"profile-cv-item\">"
        + "<div class=\"profile-cv-heading\">"
        + f"<p class=\"profile-cv-role\">{escape(role)}</p>"
        + (f"<span class=\"profile-cv-period\">{escape(period)}</span>" if period else "")
        + "</div>"
        + (f"<p class=\"profile-cv-org\">{escape(organization)}</p>" if organization else "")
        + (
            f"<p class=\"profile-cv-description\">{escape(description)}</p>"
            if description
            else ""
        )
        + "</li>"
    )


def _profile_cv_entry_from_text(entry: str) -> dict[str, str]:
    role, organization, period, description = _parse_short_cv_entry(entry)
    return {
        "role": role,
        "organization": organization,
        "period": period,
        "description": description,
    }


def _parse_short_cv_entry(entry: str) -> tuple[str, str, str, str]:
    normalized = " ".join(str(entry).split()).strip()
    if not normalized:
        return "", "", "", ""

    description = ""
    description_match = re.search(r"\)\s*:\s+", normalized)
    if description_match is not None:
        description = normalized[description_match.end() :].strip()
        normalized = normalized[: description_match.start() + 1].strip()

    period = ""
    period_match = re.search(r"\(([^()]*)\)\s*$", normalized)
    if period_match is not None:
        period = period_match.group(1).strip()
        normalized = normalized[: period_match.start()].rstrip(" ,")

    role = normalized
    organization = ""
    if "," in normalized:
        role, organization = normalized.split(",", 1)
        role = role.strip()
        organization = organization.strip()

    if not role:
        role = normalized
    return role, organization, period, description


def _write_space_persona_avatar_assets(
    *,
    output_root: Path,
    persona_rows: list[dict[str, Any]],
    incremental: bool,
) -> list[Path]:
    assets_root = output_root / "assets" / "persona_avatars"
    assets_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for row in persona_rows:
        persona_id = str(row["persona_id"])
        source_path = _resolve_persona_avatar_source_path(row)
        if source_path is None:
            continue
        target_path = assets_root / f"{persona_id}.jpg"
        _write_binary_file(target_path, source_path.read_bytes(), incremental=incremental)
        written.append(target_path)
    return written


def _write_space_persona_profile_assets(
    *,
    output_root: Path,
    persona_rows: list[dict[str, Any]],
    incremental: bool,
) -> list[Path]:
    assets_root = output_root / "assets" / "persona_profiles"
    assets_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for row in persona_rows:
        persona_id = str(row["persona_id"])
        source_path = _resolve_persona_profile_source_path(row)
        if source_path is None:
            continue
        target_path = assets_root / f"{persona_id}.jpg"
        _write_binary_file(target_path, source_path.read_bytes(), incremental=incremental)
        written.append(target_path)
    return written


def _resolve_persona_avatar_source_path(row: dict[str, Any]) -> Path | None:
    profile_image_path = str(row.get("profile_image_path") or "").strip()
    if not profile_image_path:
        return None
    thumb_path = _repo_root() / str(
        row.get("profile_image_thumb_path")
        or derive_profile_image_thumb_path(profile_image_path=profile_image_path)
    )
    if thumb_path.is_file():
        return thumb_path
    profile_path = _repo_root() / profile_image_path
    if profile_path.is_file():
        return profile_path
    return None


def _resolve_persona_profile_source_path(row: dict[str, Any]) -> Path | None:
    profile_image_path = str(row.get("profile_image_path") or "").strip()
    if not profile_image_path:
        return None
    profile_path = _repo_root() / profile_image_path
    if profile_path.is_file():
        return profile_path
    return None


def _write_space_search_page(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    persona_rows: list[dict[str, Any]],
    evidence_records: list[_EvidenceRecord],
    incremental: bool,
) -> list[Path]:
    search_root = output_root / "search"
    search_root.mkdir(parents=True, exist_ok=True)
    search_path = search_root / "index.html"
    entries = _space_search_entries(
        space_name=context.space_name,
        projection=projection,
        questions=context.questions,
        persona_rows=persona_rows,
        evidence_records=evidence_records,
    )
    rows = "\n".join(
        (
            "<li class=\"search-index-row\" data-search-text=\""
            + escape(entry.search_text)
            + "\"><span class=\"meta\">"
            + escape(entry.item_type)
            + "</span> <a href=\""
            + escape(entry.href)
            + "\">"
            + escape(entry.title)
            + "</a></li>"
        )
        for entry in entries
    )
    body = (
        "<h1>Search</h1>\n"
        + "<p id=\"search-results-summary\" class=\"search-results-summary\">"
        + f"{len(entries)} indexed item(s)</p>\n"
        + "<ul class=\"search-index feed-list\">\n"
        + rows
        + "\n</ul>\n"
        + "<script>\n"
        + "(function(){\n"
        + "  var params=new URLSearchParams(window.location.search);\n"
        + "  var query=(params.get('q')||'').toLowerCase().trim();\n"
        + "  var rows=document.querySelectorAll('.search-index-row');\n"
        + "  var visible=0;\n"
        + "  rows.forEach(function(row){\n"
        + "    var haystack=(row.getAttribute('data-search-text')||'').toLowerCase();\n"
        + "    var show=!query||haystack.indexOf(query)!==-1;\n"
        + "    row.style.display=show?'':'none';\n"
        + "    if(show){visible+=1;}\n"
        + "  });\n"
        + "  var summary=document.getElementById('search-results-summary');\n"
        + "  if(summary){\n"
        + "    summary.textContent=query?visible+' result(s) for \"'+query+'\"':visible+' indexed item(s)';\n"
        + "  }\n"
        + "})();\n"
        + "</script>\n"
    )
    _write_text_file(
        search_path,
        _render_space_layout(
            title=f"{_space_display_name(context.space_name)} - Search",
            body=body,
            context=context,
            current_tab=None,
            stylesheet_href=_relative_href(
                from_file=search_path,
                to_file=output_root / "assets" / "site.css",
            ),
        ),
        incremental=incremental,
    )
    return [search_path]


def _write_space_claim_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    evidence_records: list[_EvidenceRecord],
    incremental: bool,
    site_presentation_mode: str,
) -> list[Path]:
    space_root = output_root.parent
    claim_records = _load_claim_records(space_root=space_root)
    evidence_by_claim_id = _evidence_records_by_claim_id(evidence_records)
    claim_ids = sorted(set(_collect_claim_ids(projection=projection)) | set(claim_records.keys()))
    claims_root = output_root / "claims"
    claims_root.mkdir(parents=True, exist_ok=True)
    stylesheet_path = output_root / "assets" / "site.css"
    source_title_by_id = {
        str(source.get("source_id")): _source_display_title(source)
        for source in projection.sources
        if isinstance(source, dict) and source.get("source_id")
    }
    source_added_at_by_id = {
        str(source.get("source_id")): str(source.get("ingested_at") or source.get("date") or "").strip()
        for source in projection.sources
        if isinstance(source, dict) and source.get("source_id")
    }
    source_citation_count_by_id = {
        str(source.get("source_id")): _parse_nonnegative_float(source.get("citation_count"))
        for source in projection.sources
        if isinstance(source, dict) and source.get("source_id")
    }

    claim_index_items: list[dict[str, Any]] = []
    for claim_id in claim_ids:
        claim_record = claim_records.get(claim_id, {})
        claim_title = _claim_display_title(
            claim_id=claim_id,
            claim_record=claim_record,
        )
        claim_added_at = _claim_added_at(
            claim_record=claim_record,
            source_added_at=source_added_at_by_id.get(str(claim_record.get("source_id") or "").strip(), ""),
        )
        claim_added_label = _format_claim_added_at_for_ui(claim_added_at)
        usage_rows, usage_stats = _claim_usage_rows(
            claim_id=claim_id,
            projection=projection,
            source_title_by_id=source_title_by_id,
            claim_source_id=str(claim_record.get("source_id") or "").strip(),
            include_kind_label=False,
        )
        claim_evidence_records = evidence_by_claim_id.get(claim_id, [])
        evidence_rows = _claim_evidence_rows(
            claim_record=claim_record,
            evidence_records=claim_evidence_records,
        )
        strength = _claim_strength_stats(
            evidence_count=len(evidence_rows),
            topic_usage_count=usage_stats["topic_usage_count"],
            source_usage_count=usage_stats["source_usage_count"],
            citation_count_max=_max_citation_count_for_claim(
                source_ids=usage_stats.get("source_ids", ()),
                source_citation_count_by_id=source_citation_count_by_id,
            ),
        )
        score = int(strength["score"])
        score_band = str(strength.get("band") or "medium")
        if score_band not in {"high", "medium", "low"}:
            score_band = "medium"
        score_class = f"claim-score-value claim-score-{score_band}"
        primary_usage_rows = usage_rows[:2]
        overflow_usage_rows = usage_rows[2:]
        usage_markup = (
            "<div class=\"claim-card-usage\">"
            + "<ul class=\"claim-card-usage-list claim-card-usage-list-primary\">"
            + "".join(primary_usage_rows)
            + "</ul>"
            + "</div>"
            if usage_rows
            else "<p class=\"claim-card-usage-empty\">Used by: none yet</p>"
        )
        overflow_usage_markup = (
            "<ul class=\"claim-card-usage-list claim-card-usage-list-overflow\">"
            + "".join(overflow_usage_rows)
            + "</ul>"
            if overflow_usage_rows
            else ""
        )
        claim_row_html = (
            "<li data-claim-id=\""
            + escape(claim_id)
            + "\" data-claim-title=\""
            + escape(claim_title.lower())
            + "\" data-claim-score=\""
            + escape(str(score))
            + "\" data-claim-added-at=\""
            + escape(claim_added_at)
            + "\" class=\"claim-index-card\">"
            + "<div class=\"claim-card-row\">"
            + "<div class=\"claim-card-copy\">"
            + "<a href=\""
            + escape(claim_id)
            + ".html\">"
            + escape(claim_title)
            + "</a><p class=\"meta\">"
            + (
                "score: "
                + "<span class=\""
                + escape(score_class)
                + "\">"
                + escape(str(score))
                + "</span>"
                + " | "
                if site_presentation_mode == "debug"
                else ""
            )
            + "added: "
            + escape(claim_added_label)
            + "</p>"
            + "</div>"
            + usage_markup
            + "</div>"
            + overflow_usage_markup
            + "</li>"
        )
        claim_index_items.append(
            {
                "row_html": claim_row_html,
                "title": claim_title.casefold(),
                "score": score,
                "added_at": claim_added_at,
                "claim_id": claim_id,
            }
        )

    generated_paths: list[Path] = []
    if claim_ids:
        for mode in CLAIM_SORT_MODES:
            sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
            for direction in ("desc", "asc"):
                sort_path = _sort_mode_path(mode=mode, direction=direction)
                sorted_claim_items = _sorted_claim_index_items(
                    claim_index_items,
                    sort_key=sort_key,
                    direction=direction,
                )
                rows = [str(item["row_html"]) for item in sorted_claim_items]
                tab_root = output_root / sort_path
                tab_root.mkdir(parents=True, exist_ok=True)
                pages = _paginate(rows, TAB_PAGE_SIZE)
                for page_number, page_rows in enumerate(pages, start=1):
                    page_path = _paginated_page_path(tab_root, page_number=page_number)
                    body = (
                        "<h1>Claims</h1>\n"
                        + _render_order_controls(
                            label="Claim order",
                            space_name=context.space_name,
                            modes=CLAIM_SORT_MODES,
                            current_sort_key=sort_key,
                            current_direction=direction,
                        )
                        + "<ul class=\"feed-list\" id=\"claims-index-list\">\n"
                        + "\n".join(page_rows)
                        + "\n</ul>\n"
                        + _render_pagination(
                            page_number=page_number,
                            page_count=len(pages),
                            mode="tab",
                            base_href=f"/spaces/{context.space_name}/site/{sort_path}",
                        )
                    )
                    _write_text_file(
                        page_path,
                        _render_space_layout(
                            title=f"{_space_display_name(context.space_name)} - Claims by {sort_label.lower()}",
                            body=body,
                            context=context,
                            current_tab="claims",
                            stylesheet_href=_relative_href(from_file=page_path, to_file=stylesheet_path),
                        ),
                        incremental=incremental,
                    )
                    generated_paths.append(page_path)
    else:
        index_path = claims_root / "index.html"
        _write_text_file(
            index_path,
            _render_space_layout(
                title=f"{_space_display_name(context.space_name)} - Claims",
                body="<h1>Claims</h1>\n<p>No claim references indexed for this space yet.</p>\n",
                context=context,
                current_tab="claims",
                stylesheet_href=_relative_href(from_file=index_path, to_file=stylesheet_path),
            ),
            incremental=incremental,
        )
        generated_paths.append(index_path)
    for claim_id in claim_ids:
        claim_record = claim_records.get(claim_id, {})
        claim_text = _claim_text(claim_id=claim_id, claim_record=claim_record)
        claim_title = _claim_display_title(
            claim_id=claim_id,
            claim_record=claim_record,
            max_length=None,
        )
        usage_rows, usage_stats = _claim_usage_rows(
            claim_id=claim_id,
            projection=projection,
            source_title_by_id=source_title_by_id,
            claim_source_id=str(claim_record.get("source_id") or "").strip(),
        )
        usage_summary_rows, _ = _claim_usage_rows(
            claim_id=claim_id,
            projection=projection,
            source_title_by_id=source_title_by_id,
            claim_source_id=str(claim_record.get("source_id") or "").strip(),
            include_kind_label=False,
        )
        claim_evidence_records = evidence_by_claim_id.get(claim_id, [])
        evidence_rows = _claim_evidence_rows(
            claim_record=claim_record,
            evidence_records=claim_evidence_records,
        )
        strength = _claim_strength_stats(
            evidence_count=len(evidence_rows),
            topic_usage_count=usage_stats["topic_usage_count"],
            source_usage_count=usage_stats["source_usage_count"],
            citation_count_max=_max_citation_count_for_claim(
                source_ids=usage_stats.get("source_ids", ()),
                source_citation_count_by_id=source_citation_count_by_id,
            ),
        )
        source_record = _find_source_record(
            projection=projection,
            source_id=str(claim_record.get("source_id") or "").strip(),
        )
        overview = _claim_overview_text(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_record=claim_record,
            source_record=source_record,
            usage_stats=usage_stats,
            strength=strength,
            include_score_summary=site_presentation_mode == "debug",
        )
        source_row = _claim_primary_source_row(
            claim_source_id=str(claim_record.get("source_id") or "").strip(),
            source_title_by_id=source_title_by_id,
        )
        comments_section = _render_page_comment_section(
            page_payload=claim_record if isinstance(claim_record, dict) else {},
            default_page_ref=f"claim:{claim_id}",
            space_name=context.space_name,
        )
        claim_external_links = _claim_external_related_links(
            claim_record=claim_record,
            claim_source_id=str(claim_record.get("source_id") or "").strip(),
            source_ids=usage_stats.get("source_ids", ()),
            projection=projection,
        )
        strength_stats_section = (
            "<article class=\"source-related-card\">\n"
            + "<h2>Debug Score Metadata</h2>\n"
            + "<p class=\"meta\">Score metadata is computed from stored evidence/source/citation fields "
            + "and is exposed only in debug presentation mode.</p>\n"
            + "<dl class=\"source-meta-grid\">\n"
            + f"<dt>Score</dt><dd>{strength['score']} / 100 ({escape(strength['band'])})</dd>\n"
            + "<dt>Formula</dt><dd>"
            + escape(strength["formula"])
            + "</dd>\n"
            + f"<dt>Evidence excerpts</dt><dd>{strength['evidence_count']}</dd>\n"
            + f"<dt>Evidence factor</dt><dd>{strength['evidence_factor']:.2f}</dd>\n"
            + f"<dt>Topic usages (informational only)</dt><dd>{strength['topic_usage_count']}</dd>\n"
            + f"<dt>Source usages</dt><dd>{strength['source_usage_count']}</dd>\n"
            + f"<dt>Source factor</dt><dd>{strength['source_factor']:.2f}</dd>\n"
            + "<dt>Max source citations</dt><dd>"
            + escape(_format_citation_count_for_ui(strength.get("citation_count_max")))
            + "</dd>\n"
            + f"<dt>Citation factor</dt><dd>{strength['citation_factor']:.2f}</dd>\n"
            + "<dt>Citation signal basis</dt><dd>"
            + (
                "citation_count unavailable"
                if bool(strength.get("citation_factor_defaulted"))
                else "log-scaled from source citation_count"
            )
            + "</dd>\n"
            + "</dl>\n"
            + "</article>\n"
            if site_presentation_mode == "debug"
            else ""
        )
        claim_path = claims_root / f"{claim_id}.html"
        _write_text_file(
            claim_path,
            _render_space_layout(
                title=claim_title,
                body=(
                    f"<h1>{escape(claim_title)}</h1>\n"
                    + "<section class=\"source-related-grid\">\n"
                    + "<article class=\"source-related-card\">\n"
                    + "<h2>Claim Statement</h2>\n"
                    + f"<p>{escape(claim_text)}</p>\n"
                    + source_row
                    + "</article>\n"
                    + "<article class=\"source-related-card\">\n"
                    + "<h2>Overview and Interpretation</h2>\n"
                    + "".join(f"<p>{escape(paragraph)}</p>\n" for paragraph in overview)
                    + _render_claim_usage_summary_links(usage_summary_rows)
                    + "</article>\n"
                    + "</section>\n"
                    + "<section class=\"source-related-grid\">\n"
                    + "<article class=\"source-related-card\">\n"
                    + "<h2>Pages Using This Claim</h2>\n"
                    + (
                        "<ul class=\"source-related-list claim-page-usage-list\">\n"
                        + "\n".join(usage_rows)
                        + "\n</ul>\n"
                        if usage_rows
                        else "<p>(No topic/source pages currently reference this claim.)</p>\n"
                    )
                    + "</article>\n"
                    + strength_stats_section
                    + "</section>\n"
                    + "<section class=\"source-related-card\">\n"
                    + "<h2>Evidence Items</h2>\n"
                    + (
                        "<ul class=\"source-related-list claim-page-evidence-list\">\n"
                        + "\n".join(evidence_rows)
                        + "\n</ul>\n"
                        if evidence_rows
                        else "<p>(No evidence excerpts were stored for this claim.)</p>\n"
                    )
                    + "<p><a href=\"../evidence/index.html\">Browse all evidence</a></p>\n"
                    + "</section>\n"
                    + _render_external_related_links_card(
                        heading="External Related Links",
                        links=claim_external_links,
                        source_href_prefix="../sources/",
                    )
                    + comments_section
                    + "\n"
                    "<p><a href=\"index.html\">Back to claims index</a></p>\n"
                ),
                context=context,
                current_tab="claims",
                current_page=f"claim:{claim_id}",
                stylesheet_href=_relative_href(from_file=claim_path, to_file=stylesheet_path),
            ),
            incremental=incremental,
        )
        generated_paths.append(claim_path)
    return generated_paths


def _render_evidence_index_row(
    *,
    space_name: str,
    record: _EvidenceRecord,
    claim_option_title_by_id: dict[str, str],
    claim_href_prefix: str,
    source_title_by_id: dict[str, str],
    source_preview_by_id: dict[str, str],
) -> str:
    source_title = source_title_by_id.get(record.source_id, record.source_id)
    source_href = (
        "/spaces/"
        + escape(space_name)
        + "/site/sources/"
        + escape(record.source_id)
        + ".html"
        if record.source_id
        else ""
    )
    source_thumb = _render_evidence_source_preview_thumb(
        source_href=source_href,
        source_title=source_title,
        preview_href=source_preview_by_id.get(record.source_id, ""),
    )
    source_row = (
        "<p class=\"meta evidence-source-meta\">Source: <a href=\""
        + source_href
        + "\">"
        + escape(source_title)
        + "</a></p>"
        if record.source_id
        else ""
    )
    return (
        "<li class=\"evidence-card\"><div class=\"evidence-card-layout\">"
        + source_thumb
        + "<div class=\"evidence-card-copy\"><a href=\""
        + "/spaces/"
        + escape(space_name)
        + "/site/evidence/"
        + escape(record.evidence_id)
        + ".html\">"
        + escape(record.title)
        + "</a>"
        + "<p class=\"meta\">claims</p>"
        + _evidence_claim_links_html(
            record.claim_ids,
            claim_option_title_by_id=claim_option_title_by_id,
            claim_href_prefix=claim_href_prefix,
        )
        + source_row
        + "<p class=\"summary\">"
        + escape(truncate_text_for_ui(record.excerpt, max_length=220))
        + "</p></div></div></li>"
    )


def _render_evidence_source_preview_thumb(*, source_href: str, source_title: str, preview_href: str) -> str:
    if not source_href or not preview_href:
        return ""
    return (
        "<a class=\"source-preview-feed-link evidence-source-preview-link\" href=\""
        + source_href
        + "\" aria-label=\"Open source: "
        + escape(source_title)
        + "\">"
        + "<img class=\"source-preview-feed evidence-source-preview\" src=\""
        + escape(preview_href)
        + "\" alt=\"Preview for "
        + escape(source_title)
        + "\" /></a>"
    )


def _sorted_evidence_records(
    records: list[_EvidenceRecord],
    *,
    source_title_by_id: dict[str, str],
    sort_key: str,
    direction: str,
) -> list[_EvidenceRecord]:
    sorted_records = list(records)
    sorted_records.sort(key=lambda item: (item.title.casefold(), item.evidence_id))
    if sort_key == "source":
        sorted_records.sort(
            key=lambda item: (
                source_title_by_id.get(item.source_id, item.source_id).casefold(),
                item.title.casefold(),
                item.evidence_id,
            ),
            reverse=direction == "desc",
        )
        return sorted_records
    if sort_key == "claims":
        sorted_records.sort(
            key=lambda item: (len(item.claim_ids), item.title.casefold(), item.evidence_id),
            reverse=direction == "desc",
        )
        return sorted_records
    if direction == "desc":
        sorted_records.reverse()
    return sorted_records


def _write_space_evidence_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    evidence_records: list[_EvidenceRecord],
    incremental: bool,
) -> list[Path]:
    evidence_root = output_root / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    stylesheet_path = output_root / "assets" / "site.css"
    source_title_by_id = {
        str(source.get("source_id")): _source_display_title(source)
        for source in projection.sources
        if isinstance(source, dict) and source.get("source_id")
    }
    site_path = output_root.parents[2]
    source_preview_by_id = {
        str(source.get("source_id")): _source_preview_site_href_for_source(
            source=source,
            space_name=context.space_name,
            site_path=site_path,
        )
        for source in projection.sources
        if isinstance(source, dict) and source.get("source_id")
    }
    claim_option_title_by_id = load_claim_option_titles(space_root=output_root.parent)
    topic_title_by_id = {
        str(topic.get("topic_id")): str(topic.get("title") or topic.get("topic_id"))
        for topic in projection.topics
        if isinstance(topic, dict) and topic.get("topic_id")
    }

    generated_paths: list[Path] = []
    for mode in EVIDENCE_SORT_MODES:
        sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
        for direction in ("desc", "asc"):
            sort_path = _sort_mode_path(mode=mode, direction=direction)
            sorted_records = _sorted_evidence_records(
                evidence_records,
                source_title_by_id=source_title_by_id,
                sort_key=sort_key,
                direction=direction,
            )
            index_rows = (
                "\n".join(
                    _render_evidence_index_row(
                        space_name=context.space_name,
                        record=record,
                        claim_option_title_by_id=claim_option_title_by_id,
                        claim_href_prefix=("../" * len(Path(sort_path).parts)) + "claims/",
                        source_title_by_id=source_title_by_id,
                        source_preview_by_id=source_preview_by_id,
                    )
                    for record in sorted_records
                )
                if sorted_records
                else "<li>(none yet)</li>"
            )
            index_path = output_root / sort_path / "index.html"
            index_path.parent.mkdir(parents=True, exist_ok=True)
            _write_text_file(
                index_path,
                _render_space_layout(
                    title=f"{_space_display_name(context.space_name)} - Evidence by {sort_label.lower()}",
                    body=(
                        "<h1>Evidence</h1>\n"
                        "<p>Canonical evidence items authored by semantic extraction and validated for linking integrity.</p>\n"
                        + _render_order_controls(
                            label="Evidence order",
                            space_name=context.space_name,
                            modes=EVIDENCE_SORT_MODES,
                            current_sort_key=sort_key,
                            current_direction=direction,
                        )
                        + "<ul class=\"feed-list\">\n"
                        + index_rows
                        + "\n</ul>\n"
                    ),
                    context=context,
                    current_tab="evidence",
                    stylesheet_href=_relative_href(from_file=index_path, to_file=stylesheet_path),
                ),
                incremental=incremental,
            )
            generated_paths.append(index_path)
    for record in evidence_records:
        topic_rows = (
            "\n".join(
                (
                    "<li><a href=\"../topics/"
                    + escape(topic_id)
                    + ".html\">"
                    + escape(topic_title_by_id.get(topic_id, topic_id))
                    + "</a></li>"
                )
                for topic_id in record.topic_ids
            )
            if record.topic_ids
            else "<li>(No topic pages currently reference this evidence.)</li>"
        )
        source_row = (
            "<p><a href=\"../sources/"
            + escape(record.source_id)
            + ".html\">"
            + escape(source_title_by_id.get(record.source_id, record.source_id))
            + "</a></p>\n"
            if record.source_id
            else "<p>(No primary source link was stored for this evidence item.)</p>\n"
        )
        claim_rows = (
            "\n".join(
                "<li><a href=\"../claims/"
                + escape(claim_id)
                + ".html\">"
                + escape(
                    claim_option_title(
                        claim_id=claim_id,
                        claim_option_title_by_id=claim_option_title_by_id,
                    )
                )
                + "</a></li>"
                for claim_id in record.claim_ids
            )
            if record.claim_ids
            else "<li>(No linked claims were stored for this evidence item.)</li>"
        )
        page_ref_row = (
            "<p class=\"meta\">Page references: "
            + ", ".join(escape(value) for value in record.page_refs)
            + "</p>\n"
            if record.page_refs
            else ""
        )
        evidence_path = evidence_root / f"{record.evidence_id}.html"
        _write_text_file(
            evidence_path,
            _render_space_layout(
                title=record.title,
                body=(
                    f"<h1>{escape(record.title)}</h1>\n"
                    + "<section class=\"source-related-grid\">\n"
                    + "<article class=\"source-related-card\">\n"
                    + "<h2>Evidence Excerpt</h2>\n"
                    + f"<p>{escape(record.excerpt)}</p>\n"
                    + page_ref_row
                    + "<p class=\"meta\">Type: "
                    + escape(record.evidence_type)
                    + "</p>\n"
                    + "<p>"
                    + escape(record.overview)
                    + "</p>\n"
                    + "</article>\n"
                    + "<article class=\"source-related-card\">\n"
                    + "<h2>Linked Claims</h2>\n"
                    + "<ul class=\"source-related-list\">\n"
                    + claim_rows
                    + "\n</ul>\n"
                    + "</article>\n"
                    + "<article class=\"source-related-card\">\n"
                    + "<h2>Primary Source</h2>\n"
                    + source_row
                    + "</article>\n"
                    + "</section>\n"
                    + "<section class=\"source-related-card\">\n"
                    + "<h2>Topic Pages Using This Evidence</h2>\n"
                    + "<ul class=\"source-related-list\">\n"
                    + topic_rows
                    + "\n</ul>\n"
                    + "</section>\n"
                    + _render_page_comment_section(
                        page_payload={},
                        default_page_ref=f"evidence:{record.evidence_id}",
                        space_name=context.space_name,
                        show_empty_state=False,
                    )
                    + "<p><a href=\"index.html\">Back to evidence index</a></p>\n"
                ),
                context=context,
                current_tab=None,
                current_page=f"evidence:{record.evidence_id}",
                stylesheet_href=_relative_href(from_file=evidence_path, to_file=stylesheet_path),
            ),
            incremental=incremental,
        )
        generated_paths.append(evidence_path)

    return generated_paths


def _collect_claim_ids(*, projection: SpaceProjection) -> list[str]:
    claim_ids: set[str] = set()
    for topic in projection.topics:
        claim_ids.update(_collect_claim_ids_from_topic(topic=topic))
    return sorted(claim_ids)


def _claim_topic_usage_map(*, projection: SpaceProjection) -> dict[str, set[str]]:
    usage: dict[str, set[str]] = {}
    for topic in projection.topics:
        topic_id = str(topic.get("topic_id") or "").strip()
        if not topic_id:
            continue
        for claim_id in _collect_claim_ids_from_topic(topic=topic):
            usage.setdefault(claim_id, set()).add(topic_id)
    return usage


def _build_space_evidence_records(*, space_root: Path, projection: SpaceProjection) -> list[_EvidenceRecord]:
    known_claim_ids = set(_load_claim_records(space_root=space_root))
    topic_usage = _claim_topic_usage_map(projection=projection)
    evidence_root = space_root / "evidence"
    records: list[_EvidenceRecord] = []
    if not evidence_root.is_dir():
        return records
    for evidence_path in sorted(evidence_root.glob("evidence-*.json")):
        try:
            payload = json.loads(evidence_path.read_text())
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        evidence_id = str(payload.get("evidence_id") or "").strip()
        title = str(payload.get("title") or "").strip()
        excerpt = str(payload.get("excerpt") or "").strip()
        overview = str(payload.get("overview") or "").strip()
        evidence_type = str(payload.get("evidence_type") or "").strip()
        source_id = str(payload.get("source_id") or "").strip()
        if not evidence_id or not title or not excerpt:
            continue
        claim_ids = tuple(
            claim_id
            for claim_id in _normalize_string_array(payload.get("claim_ids"))
            if claim_id in known_claim_ids
        )
        if not claim_ids:
            continue
        topic_ids: set[str] = set()
        for claim_id in claim_ids:
            topic_ids.update(topic_usage.get(claim_id, set()))
        records.append(
            _EvidenceRecord(
                evidence_id=evidence_id,
                title=title,
                excerpt=excerpt,
                overview=overview,
                evidence_type=evidence_type,
                source_id=source_id,
                claim_ids=claim_ids,
                page_refs=tuple(_normalize_string_array(payload.get("page_refs"))),
                topic_ids=tuple(sorted(topic_ids)),
            )
        )
    return sorted(records, key=lambda item: item.evidence_id)


def _normalize_string_array(raw_value: object) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    normalized: list[str] = []
    for raw_item in raw_value:
        value = str(raw_item or "").strip()
        if value:
            normalized.append(value)
    return normalized


def _evidence_records_by_claim_id(
    evidence_records: list[_EvidenceRecord],
) -> dict[str, list[_EvidenceRecord]]:
    grouped: dict[str, list[_EvidenceRecord]] = {}
    for record in evidence_records:
        for claim_id in record.claim_ids:
            grouped.setdefault(claim_id, []).append(record)
    for records in grouped.values():
        records.sort(key=lambda item: item.evidence_id)
    return grouped


def _evidence_records_by_source_id(
    evidence_records: list[_EvidenceRecord],
) -> dict[str, list[_EvidenceRecord]]:
    grouped: dict[str, list[_EvidenceRecord]] = {}
    for record in evidence_records:
        if not record.source_id:
            continue
        grouped.setdefault(record.source_id, []).append(record)
    for records in grouped.values():
        records.sort(key=lambda item: item.evidence_id)
    return grouped


def _evidence_records_by_topic_id(
    evidence_records: list[_EvidenceRecord],
) -> dict[str, list[_EvidenceRecord]]:
    grouped: dict[str, list[_EvidenceRecord]] = {}
    for record in evidence_records:
        for topic_id in record.topic_ids:
            grouped.setdefault(topic_id, []).append(record)
    for records in grouped.values():
        records.sort(key=lambda item: item.evidence_id)
    return grouped


def _evidence_claim_links_html(
    claim_ids: tuple[str, ...],
    *,
    claim_option_title_by_id: dict[str, str],
    claim_href_prefix: str = "../claims/",
) -> str:
    if not claim_ids:
        return "(none)"
    links = [
        "<a class=\"source-evidence-claim-chip\" href=\""
        + escape(claim_href_prefix)
        + escape(claim_id)
        + ".html\">"
        + escape(
            claim_option_title(
                claim_id=claim_id,
                claim_option_title_by_id=claim_option_title_by_id,
            )
        )
        + "</a>"
        for claim_id in claim_ids
    ]
    return "<span class=\"source-evidence-claim-chips\">" + "".join(links) + "</span>"


def _load_claim_records(*, space_root: Path) -> dict[str, dict[str, Any]]:
    claims_dir = space_root / "claims"
    if not claims_dir.is_dir():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for claim_path in sorted(claims_dir.glob("claim-*.json")):
        try:
            payload = json.loads(claim_path.read_text())
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        claim_id = str(payload.get("claim_id") or "").strip()
        if not claim_id:
            continue
        records[claim_id] = payload
    return records


def _load_question_measurement_records(*, space_root: Path) -> dict[str, dict[str, Any]]:
    measurements_dir = space_root / "measurements"
    if not measurements_dir.is_dir():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for measurement_path in sorted(measurements_dir.glob("measurement-*.json")):
        try:
            payload = json.loads(measurement_path.read_text())
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        measurement_id = str(payload.get("measurement_id") or "").strip()
        if not measurement_id:
            continue
        records[measurement_id] = payload
    return records


def _claim_text(*, claim_id: str, claim_record: dict[str, Any]) -> str:
    text = str(claim_record.get("text") or "").strip()
    return text if text else claim_id


def _claim_added_at(*, claim_record: dict[str, Any], source_added_at: str) -> str:
    for key in ("added_at", "created_at", "updated_at"):
        value = str(claim_record.get(key) or "").strip()
        if value:
            return value
    return source_added_at.strip()


def _sorted_claim_index_items(
    items: list[dict[str, Any]],
    *,
    sort_key: str,
    direction: str,
) -> list[dict[str, Any]]:
    sorted_items = list(items)
    sorted_items.sort(key=lambda item: (str(item.get("title") or ""), str(item.get("claim_id") or "")))
    if sort_key == "score":
        sorted_items.sort(key=lambda item: int(item.get("score") or 0), reverse=direction == "desc")
        return sorted_items
    if sort_key == "date":
        if direction == "desc":
            sorted_items.sort(key=lambda item: str(item.get("added_at") or ""), reverse=True)
        else:
            sorted_items.sort(key=lambda item: (not str(item.get("added_at") or ""), str(item.get("added_at") or "")))
        return sorted_items
    if sort_key == "title" and direction == "desc":
        sorted_items.reverse()
    return sorted_items


def _format_claim_added_at_for_ui(value: str) -> str:
    raw = value.strip()
    if not raw:
        return "unknown"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}$", raw):
        parsed = datetime.strptime(raw, "%Y-%m-%d")
        return parsed.strftime("%b %d, %Y")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", raw):
        parsed = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
        return parsed.strftime("%b %d, %Y")
    return raw


def _parse_nonnegative_float(raw_value: object) -> float | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, bool):
        return None
    if isinstance(raw_value, (int, float)):
        value = float(raw_value)
    else:
        text = str(raw_value).strip()
        if not text:
            return None
        try:
            value = float(text)
        except ValueError:
            return None
    if not math.isfinite(value) or value < 0.0:
        return None
    return value


def _max_citation_count_for_claim(
    *,
    source_ids: tuple[str, ...] | list[str],
    source_citation_count_by_id: dict[str, float | None],
) -> float | None:
    values = [
        citation_count
        for source_id in source_ids
        for citation_count in (source_citation_count_by_id.get(source_id),)
        if citation_count is not None
    ]
    if not values:
        return None
    return max(values)


def _format_citation_count_for_ui(value: object) -> str:
    parsed = _parse_nonnegative_float(value)
    if parsed is None:
        return "unknown"
    if float(parsed).is_integer():
        return f"{int(parsed):,}"
    return f"{parsed:.1f}"


def _claim_display_title(
    *,
    claim_id: str,
    claim_record: dict[str, Any],
    max_length: int | None = 120,
) -> str:
    text = _claim_text(claim_id=claim_id, claim_record=claim_record)
    if text == claim_id:
        return claim_id
    raw_short_title = str(claim_record.get("short_title") or "")
    title = short_claim_option_label(raw_short_title, fallback_text=text)
    if not title:
        title = text
    if max_length is None or len(title) <= max_length:
        return title
    if max_length <= 3:
        return title[:max_length]
    truncated = title[: max_length - 3].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated + "..."


def _claim_primary_source_row(*, claim_source_id: str, source_title_by_id: dict[str, str]) -> str:
    if not claim_source_id:
        return "<p class=\"meta\">Primary source: unknown</p>\n"
    source_title = source_title_by_id.get(claim_source_id, claim_source_id)
    return (
        "<p class=\"meta\">Primary source: <a href=\"../sources/"
        + escape(claim_source_id)
        + ".html\">"
        + escape(source_title)
        + "</a></p>\n"
    )


def _claim_evidence_rows(
    *,
    claim_record: dict[str, Any],
    evidence_records: list[_EvidenceRecord] | None = None,
) -> list[str]:
    if evidence_records:
        rows: list[str] = []
        for record in evidence_records:
            rows.append(
                "<li><a href=\"../evidence/"
                + escape(record.evidence_id)
                + ".html\">"
                + escape(record.title)
                + "</a><p class=\"summary\">"
                + escape(truncate_text_for_ui(record.excerpt, max_length=220))
                + "</p></li>"
            )
        if rows:
            return rows
    return []


def _find_source_record(*, projection: SpaceProjection, source_id: str) -> dict[str, Any]:
    if not source_id:
        return {}
    for source in projection.sources:
        if not isinstance(source, dict):
            continue
        if str(source.get("source_id") or "").strip() == source_id:
            return source
    return {}


def _claim_usage_rows(
    *,
    claim_id: str,
    projection: SpaceProjection,
    source_title_by_id: dict[str, str],
    claim_source_id: str,
    include_kind_label: bool = True,
) -> tuple[list[str], dict[str, Any]]:
    rows: list[str] = []
    seen: set[tuple[str, str]] = set()
    topic_usage_count = 0
    source_usage_count = 0
    source_ids_used: set[str] = set()

    for topic in projection.topics:
        topic_id = str(topic.get("topic_id") or "").strip()
        if not topic_id:
            continue
        sections = topic.get("sections")
        if not isinstance(sections, list):
            continue
        used = False
        for section in sections:
            if not isinstance(section, dict):
                continue
            _, annotation_groups = extract_claim_annotations(str(section.get("body") or ""))
            if any(claim_id in group for group in annotation_groups):
                used = True
                break
        if not used:
            continue
        key = ("topic", topic_id)
        if key in seen:
            continue
        seen.add(key)
        topic_usage_count += 1
        if include_kind_label:
            rows.append(
                "<li><span class=\"meta\">topic</span> "
                + "<a href=\"../topics/"
                + escape(topic_id)
                + ".html\">"
                + escape(str(topic.get("title") or topic_id))
                + "</a><p class=\"summary\">"
                + escape(_topic_card_overview(topic))
                + "</p></li>"
            )
        else:
            rows.append(
                "<li class=\"claim-usage-chip claim-usage-chip-topic\">"
                + "<a href=\"../topics/"
                + escape(topic_id)
                + ".html\">"
                + escape(str(topic.get("title") or topic_id))
                + "</a></li>"
            )

    for source in projection.sources:
        source_id = str(source.get("source_id") or "").strip()
        if not source_id:
            continue
        source_dossier = source.get("source_dossier")
        used = False
        if isinstance(source_dossier, dict):
            sections = source_dossier.get("sections")
            if isinstance(sections, list):
                for section in sections:
                    if not isinstance(section, dict):
                        continue
                    claim_ids = section.get("grounding_claim_ids")
                    if isinstance(claim_ids, list) and claim_id in {str(value).strip() for value in claim_ids}:
                        used = True
                        break
        if not used and claim_source_id and claim_source_id == source_id:
            used = True
        if not used:
            continue
        key = ("source", source_id)
        if key in seen:
            continue
        seen.add(key)
        source_usage_count += 1
        source_ids_used.add(source_id)
        if include_kind_label:
            rows.append(
                "<li><span class=\"meta\">source</span> "
                + "<a href=\"../sources/"
                + escape(source_id)
                + ".html\">"
                + escape(source_title_by_id.get(source_id, source_id))
                + "</a><p class=\"summary\">"
                + escape(_source_card_overview(source))
                + "</p></li>"
            )
        else:
            rows.append(
                "<li class=\"claim-usage-chip claim-usage-chip-source\">"
                + "<a href=\"../sources/"
                + escape(source_id)
                + ".html\">"
                + escape(source_title_by_id.get(source_id, source_id))
                + "</a></li>"
            )

    rows.sort()
    return rows, {
        "topic_usage_count": topic_usage_count,
        "source_usage_count": source_usage_count,
        "total_usage_count": topic_usage_count + source_usage_count,
        "source_ids": tuple(sorted(source_ids_used)),
    }


def _claim_strength_stats(
    *,
    evidence_count: int,
    topic_usage_count: int,
    source_usage_count: int,
    citation_count_max: float | None,
) -> dict[str, Any]:
    evidence_factor = min(max(evidence_count, 0) / 3.0, 1.0)
    source_factor = min(max(source_usage_count, 0) / 2.0, 1.0)
    citation_factor_defaulted = citation_count_max is None
    if citation_factor_defaulted:
        citation_factor = 0.5
    else:
        citation_factor = min(max(math.log10(citation_count_max + 1.0) / 3.0, 0.0), 1.0)
    score = round(100.0 * (0.65 * evidence_factor + 0.20 * source_factor + 0.15 * citation_factor))
    if score >= 75:
        band = "high"
    elif score >= 45:
        band = "medium"
    else:
        band = "low"
    return {
        "score": score,
        "band": band,
        "formula": (
            "score = 100 * (0.65 * evidence_factor + 0.20 * source_factor + 0.15 * citation_factor), "
            "where evidence_factor=min(evidence_items/3,1), "
            "topic_usages are informational only and do not contribute to score, "
            "source_factor=min(source_usages/2,1), "
            "citation_factor=min(log10(max_citation_count+1)/3,1) when citation data exists; "
            "otherwise citation_factor=0.5"
        ),
        "evidence_count": max(evidence_count, 0),
        "evidence_factor": evidence_factor,
        "topic_usage_count": max(topic_usage_count, 0),
        "source_usage_count": max(source_usage_count, 0),
        "source_factor": source_factor,
        "citation_count_max": citation_count_max,
        "citation_factor": citation_factor,
        "citation_factor_defaulted": citation_factor_defaulted,
    }


def _render_claim_usage_summary_links(rows: list[str]) -> str:
    if not rows:
        return ""
    return (
        "<p class=\"meta\">Referenced pages</p>\n"
        + "<ul class=\"claim-card-usage-list claim-card-usage-list-primary\">\n"
        + "\n".join(rows)
        + "\n</ul>\n"
    )


def _claim_overview_text(
    *,
    claim_id: str,
    claim_text: str,
    claim_record: dict[str, Any],
    source_record: dict[str, Any],
    usage_stats: dict[str, int],
    strength: dict[str, Any],
    include_score_summary: bool,
) -> list[str]:
    claim_overview = str(claim_record.get("overview") or "").strip()
    if claim_overview:
        lead = claim_overview
    else:
        dossier_lead = _claim_dossier_grounding_summary(claim_id=claim_id, source_record=source_record)
        if dossier_lead:
            lead = dossier_lead
        else:
            lead = (
                "This claim can be read as the following statement: "
                f"{claim_text}"
            )

    usage_paragraph = (
        f"In this space, the claim is currently referenced by {usage_stats['topic_usage_count']} topic page(s) "
        f"and {usage_stats['source_usage_count']} source page(s)."
    )
    if include_score_summary:
        usage_paragraph += (
            f" Debug score metadata is {strength['score']} / 100 ({strength['band']}). "
            "Topic usage is shown for navigation context but is not part of the score."
        )
    return [lead, usage_paragraph]


def _claim_dossier_grounding_summary(*, claim_id: str, source_record: dict[str, Any]) -> str:
    source_dossier = source_record.get("source_dossier")
    if not isinstance(source_dossier, dict):
        return ""
    sections = source_dossier.get("sections")
    if not isinstance(sections, list):
        return ""

    matched_bodies: list[str] = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        grounding_ids = section.get("grounding_claim_ids")
        if not isinstance(grounding_ids, list):
            continue
        normalized_ids = {str(value).strip() for value in grounding_ids if str(value).strip()}
        if claim_id not in normalized_ids:
            continue
        body = str(section.get("body") or "").strip()
        if body:
            matched_bodies.append(body)

    if not matched_bodies:
        return ""

    # Reuse LLM-authored dossier prose where available to provide a richer claim overview.
    combined = " ".join(matched_bodies[:2]).strip()
    if len(combined) <= 900:
        return combined
    truncated = combined[:897].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated + "..."


def _space_search_entries(
    *,
    space_name: str,
    projection: SpaceProjection,
    questions: list[PreparedQuestion],
    persona_rows: list[dict[str, Any]],
    evidence_records: list[_EvidenceRecord],
) -> list[_SearchIndexEntry]:
    entries: list[_SearchIndexEntry] = []
    for source in sorted(projection.sources, key=lambda item: str(item["source_id"])):
        source_id = str(source["source_id"])
        title = _source_display_title(source)
        entries.append(
            _SearchIndexEntry(
                item_type="source",
                item_id=source_id,
                title=title,
                href=f"/spaces/{space_name}/site/sources/{source_id}.html",
                search_text=f"source {source_id} {title}",
            )
        )
    for topic in sorted(projection.topics, key=lambda item: str(item["topic_id"])):
        topic_id = str(topic["topic_id"])
        title = str(topic["title"])
        entries.append(
            _SearchIndexEntry(
                item_type="topic",
                item_id=topic_id,
                title=title,
                href=f"/spaces/{space_name}/site/topics/{topic_id}.html",
                search_text=f"topic {topic_id} {title}",
            )
        )
    for question in sorted(questions, key=lambda item: item.question_id):
        if question.status != "active":
            continue
        entries.append(
            _SearchIndexEntry(
                item_type="question",
                item_id=question.question_id,
                title=question.question,
                href=f"/spaces/{space_name}/site/questions/{question.question_id}.html",
                search_text=f"question {question.question_id} {question.question}",
            )
        )
    for row in sorted(persona_rows, key=lambda item: str(item["persona_id"])):
        persona_id = str(row["persona_id"])
        display_name = str(row.get("display_name") or "")
        full_name = str(row.get("full_name") or "")
        entries.append(
            _SearchIndexEntry(
                item_type="user",
                item_id=persona_id,
                title=display_name if display_name else persona_id,
                href=f"/spaces/{space_name}/site/users/persona-{persona_id}.html",
                search_text=f"user {persona_id} {display_name} {full_name}",
            )
        )
    for record in evidence_records:
        entries.append(
            _SearchIndexEntry(
                item_type="evidence",
                item_id=record.evidence_id,
                title=record.title,
                href=f"/spaces/{space_name}/site/evidence/{record.evidence_id}.html",
                search_text=(
                    f"evidence {record.evidence_id} {record.title} {record.excerpt} "
                    f"{' '.join(record.claim_ids)} {record.source_id} {record.evidence_type} {record.overview}"
                ),
            )
        )
    return entries


def _render_space_layout(
    *,
    title: str,
    body: str,
    context: _SpaceLayoutContext,
    current_tab: str | None,
    stylesheet_href: str,
    current_page: str | None = None,
    content_class: str = "content-card",
    wrap_body: bool = True,
) -> str:
    content_container = (
        "<section class=\""
        + escape(content_class)
        + "\">"
        + body
        + "</section>\n"
        if wrap_body
        else body + "\n"
    )
    return (
        "<!doctype html>\n"
        "<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>"
        + escape(title)
        + "</title>"
        + "<link rel=\"stylesheet\" href=\""
        + escape(stylesheet_href)
        + "\">"
        + "</head><body class=\"site-shell site-with-global-menubar\">\n"
        + _render_global_site_menubar(
            site_name=context.site_name,
            current_tab=current_tab,
            space_names=context.all_space_names,
            subspaces_by_space=context.site_subspaces_by_space,
            current_space_name=context.space_name,
            current_page=current_page,
        )
        + "<main class=\"site-main site-space-main\">\n"
        + "<header class=\"site-topbar\">"
        + "<form class=\"top-search\" action=\"/spaces/"
        + escape(context.space_name)
        + "/site/search/index.html\" method=\"get\">"
        + "<label class=\"top-search-label\" for=\"space-search-q\">Search</label> "
        + "<input class=\"top-search-input\" id=\"space-search-q\" type=\"search\" name=\"q\" placeholder=\"Search this space\"/></form>"
        + "</header>\n"
        + content_container
        + "\n</main>\n"
        + _render_global_site_menu_script()
        + "</body></html>\n"
    )


def _paginate(items: list[Any], page_size: int) -> list[list[Any]]:
    if not items:
        return [[]]
    return [items[index : index + page_size] for index in range(0, len(items), page_size)]


def _paginated_page_path(root: Path, *, page_number: int) -> Path:
    if page_number == 1:
        return root / "index.html"
    return root / "page" / str(page_number) / "index.html"


def _relative_href(*, from_file: Path, to_file: Path) -> str:
    return Path(os.path.relpath(to_file, start=from_file.parent)).as_posix()


def _rewrite_root_relative_links_for_file_mode(
    *,
    root: Path,
    site_path: Path,
    incremental: bool,
) -> None:
    for html_path in sorted(root.rglob("*.html")):
        content = html_path.read_text()
        rewritten = _rewrite_root_relative_urls(
            html=content,
            page_path=html_path,
            site_path=site_path,
        )
        _write_text_file(html_path, rewritten, incremental=incremental)


def _rewrite_root_relative_urls(*, html: str, page_path: Path, site_path: Path) -> str:
    def _replace(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        original_url = match.group("url")
        parsed = urlsplit(original_url)
        target_path = _resolve_site_local_target_path(path=parsed.path, site_path=site_path)
        if target_path is None:
            return match.group(0)
        relative_path = _relative_href(from_file=page_path, to_file=target_path)
        rewritten_url = relative_path
        if parsed.query:
            rewritten_url += f"?{parsed.query}"
        if parsed.fragment:
            rewritten_url += f"#{parsed.fragment}"
        return f'{prefix}{rewritten_url}"'

    return _ROOT_LOCAL_URL_ATTR_RE.sub(_replace, html)


def _resolve_site_local_target_path(*, path: str, site_path: Path) -> Path | None:
    if path.startswith("/site/") or path.startswith("/spaces/"):
        return site_path / path.lstrip("/")
    return None


def _render_pagination(
    *,
    page_number: int,
    page_count: int,
    mode: str,
    base_href: str,
) -> str:
    if page_count <= 1:
        return ""
    param_key = "feed_page" if mode == "feed" else "tab_page"
    links = []
    for number in range(1, page_count + 1):
        if number == 1:
            href = f"{base_href}/index.html?{param_key}={number}"
        else:
            href = f"{base_href}/page/{number}/index.html?{param_key}={number}"
        links.append(
            "<a class=\"page-link"
            + (" current" if number == page_number else "")
            + f"\" href=\"{escape(href)}\">{number}</a>"
        )
    return "<nav class=\"pagination\" aria-label=\"Pagination\">" + " ".join(links) + "</nav>\n"


def _write_site_users_pages(
    *,
    site_root: Path,
    site_name: str,
    persona_rows: list[dict[str, Any]],
    space_names: list[str],
    root_space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
    incremental: bool,
) -> None:
    site_stylesheet_path = site_root / "assets" / "site.css"
    rows_by_name: list[tuple[str, str]] = []
    for row in persona_rows:
        persona_id = str(row["persona_id"])
        rows_by_name.append(
            (
                str(row["display_name"]).casefold(),
                "<article class=\"user-card site-user-card\">"
                + "<img class=\"user-card-photo\" src=\"/spaces/"
                + escape(space_names[0] if space_names else "")
                + "/site/assets/persona_profiles/"
                + escape(persona_id)
                + ".jpg\" alt=\"Profile photo for "
                + escape(str(row["display_name"]))
                + "\" loading=\"lazy\" />"
                + "<span class=\"user-card-name\">"
                + escape(str(row["display_name"]))
                + "</span>"
                + "</article>",
            )
        )

    for mode in USER_SORT_MODES:
        sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
        for direction in ("desc", "asc"):
            sort_path = _sort_mode_path(mode=mode, direction=direction)
            users_root = site_root / sort_path
            users_root.mkdir(parents=True, exist_ok=True)
            rows = [
                row_html
                for _name, row_html in sorted(
                    rows_by_name,
                    key=lambda row: row[0],
                    reverse=direction == "desc",
                )
            ]
            pages = _paginate(rows, TAB_PAGE_SIZE)
            for page_number, page_rows in enumerate(pages, start=1):
                page_path = _paginated_page_path(users_root, page_number=page_number)
                body = (
                    f"<h1>{escape(site_name)} Users</h1>\n"
                    + _render_site_order_controls(
                        label="User order",
                        modes=USER_SORT_MODES,
                        current_sort_key=sort_key,
                        current_direction=direction,
                    )
                    + "<div class=\"user-card-grid\">\n"
                    + "\n".join(page_rows)
                    + "\n</div>\n"
                    + _render_pagination(
                        page_number=page_number,
                        page_count=len(pages),
                        mode="tab",
                        base_href=f"/site/{sort_path}",
                    )
                )
                _write_text_file(
                    page_path,
                    _render_site_layout(
                        title=f"{site_name} Users by {sort_label.lower()}",
                        site_name=site_name,
                        body=body,
                        current_tab="users",
                        stylesheet_href=_relative_href(from_file=page_path, to_file=site_stylesheet_path),
                        space_names=root_space_names,
                        subspaces_by_space=subspaces_by_space,
                    ),
                    incremental=incremental,
                )


def _write_site_feed_tab_pages(
    *,
    site_root: Path,
    site_name: str,
    entries: list[_FeedEntry],
    root_space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
    incremental: bool,
) -> None:
    site_stylesheet_path = site_root / "assets" / "site.css"
    for tab_name, item_type, heading in (
        ("sources", "source", "Sources"),
        ("topics", "topic", "Topics"),
    ):
        tab_entries = [entry for entry in entries if entry.item_type == item_type]
        modes = SOURCE_SORT_MODES if item_type == "source" else TOPIC_SORT_MODES
        for mode in modes:
            sort_key, sort_label, _desc_path, _asc_path, _default_direction = mode
            for direction in ("desc", "asc"):
                sort_path = _sort_mode_path(mode=mode, direction=direction)
                tab_root = site_root / sort_path
                tab_root.mkdir(parents=True, exist_ok=True)
                if item_type == "source":
                    sorted_entries = _sorted_source_feed_entries(
                        tab_entries,
                        sort_key=sort_key,
                        direction=direction,
                    )
                else:
                    sorted_entries = _sorted_topic_feed_entries(
                        tab_entries,
                        sort_key=sort_key,
                        direction=direction,
                    )
                pages = _paginate(sorted_entries, TAB_PAGE_SIZE)
                for page_number, page_entries in enumerate(pages, start=1):
                    page_path = _paginated_page_path(tab_root, page_number=page_number)
                    body = (
                        f"<h1>{escape(heading)}</h1>\n<p>{escape(site_name)}</p>\n"
                        + _render_site_order_controls(
                            label=f"{heading[:-1] if heading.endswith('s') else heading} order",
                            modes=modes,
                            current_sort_key=sort_key,
                            current_direction=direction,
                        )
                        + (
                            "<ul class=\"feed-list\">\n"
                            + "\n".join(_render_feed_row(entry) for entry in page_entries)
                            + "\n</ul>\n"
                            if page_entries
                            else f"<p>No {escape(heading.lower())} yet.</p>\n"
                        )
                        + _render_pagination(
                            page_number=page_number,
                            page_count=len(pages),
                            mode="tab",
                            base_href=f"/site/{sort_path}",
                        )
                    )
                    _write_text_file(
                        page_path,
                        _render_site_layout(
                            title=f"{site_name} {heading} by {sort_label.lower()}",
                            site_name=site_name,
                            body=body,
                            current_tab=tab_name,
                            stylesheet_href=_relative_href(
                                from_file=page_path,
                                to_file=site_stylesheet_path,
                            ),
                            space_names=root_space_names,
                            subspaces_by_space=subspaces_by_space,
                        ),
                        incremental=incremental,
                    )


def _render_site_root_index(
    *,
    site_name: str,
    space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
    latest_entries: list[_FeedEntry],
    stylesheet_href: str,
) -> str:
    rows = []
    for space_name in sorted(space_names):
        subspaces = subspaces_by_space.get(space_name, [])
        if subspaces:
            subspace_rows = "<ul>" + "".join(
                (
                    "<li><a href=\"/spaces/"
                    + escape(subspace_name)
                    + "/site/index.html\">"
                    + escape(_space_or_subspace_display_name(space_name=subspace_name, title=title))
                    + " ("
                    + escape(_space_display_name(subspace_name))
                    + ")</a></li>"
                )
                for subspace_name, title in subspaces
            ) + "</ul>"
        else:
            subspace_rows = ""
        rows.append(
            "<li><a href=\"/spaces/"
            + escape(space_name)
            + "/site/index.html\">"
            + escape(_space_display_name(space_name))
            + "</a>"
            + subspace_rows
            + "</li>"
        )
    latest_rows = "\n".join(_render_feed_row(entry) for entry in latest_entries)
    latest_section = (
        "<h2>Latest Across Spaces</h2>\n<ul class=\"feed-list\">\n"
        + latest_rows
        + "\n</ul>\n"
        + "<p><a href=\"/site/new/index.html\">Open full New feed</a></p>\n"
        if latest_entries
        else "<h2>Latest Across Spaces</h2>\n<p>No feed items yet.</p>\n"
    )
    return _render_site_layout(
        title=site_name,
        site_name=site_name,
        current_tab="spaces",
        stylesheet_href=stylesheet_href,
        space_names=space_names,
        subspaces_by_space=subspaces_by_space,
        body=(
            latest_section
            + "<h2>Spaces</h2>\n<ul class=\"feed-list\">\n"
            + "\n".join(rows)
            + "\n</ul>\n"
        ),
    )


def _render_site_new_page(
    *,
    site_name: str,
    space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
    page_entries: list[_FeedEntry],
    page_number: int,
    page_count: int,
    stylesheet_href: str,
    sort_key: str,
    sort_direction: str,
    sort_path: str,
) -> str:
    rows = "\n".join(_render_feed_row(entry) for entry in page_entries)
    return _render_site_layout(
        title="New",
        site_name=site_name,
        current_tab="new",
        stylesheet_href=stylesheet_href,
        space_names=space_names,
        subspaces_by_space=subspaces_by_space,
        body=(
            f"<h1>New</h1>\n<p>{escape(site_name)}</p>\n"
            + _render_site_order_controls(
                label="New order",
                modes=NEW_SORT_MODES,
                current_sort_key=sort_key,
                current_direction=sort_direction,
            )
            + "<ul class=\"feed-list\">\n"
            + rows
            + "\n</ul>\n"
            + _render_pagination(
                page_number=page_number,
                page_count=page_count,
                mode="feed",
                base_href=f"/site/{sort_path}",
            )
        ),
    )


def _render_site_layout(
    *,
    title: str,
    site_name: str,
    body: str,
    current_tab: str | None,
    stylesheet_href: str,
    space_names: list[str] | None = None,
    subspaces_by_space: dict[str, list[tuple[str, str | None]]] | None = None,
) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>"
        + escape(title)
        + "</title>"
        + "<link rel=\"stylesheet\" href=\""
        + escape(stylesheet_href)
        + "\">"
        + "</head><body class=\"site-shell site-root-shell\">\n"
        + _render_global_site_menubar(
            site_name=site_name,
            current_tab=current_tab,
            space_names=space_names or [],
            subspaces_by_space=subspaces_by_space or {},
        )
        + "<main class=\"site-main site-root-main\">"
        + "<section class=\"content-card site-root-content-card\">"
        + body
        + "</section>"
        + "</main>"
        + _render_global_site_menu_script()
        + "</body></html>\n"
    )


def _render_global_site_menubar(
    *,
    site_name: str,
    current_tab: str | None,
    space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
    current_space_name: str | None = None,
    current_page: str | None = None,
) -> str:
    nav_rows = _render_global_site_tab_rows(
        current_tab=current_tab,
        current_page=current_page,
        current_space_name=current_space_name,
    )
    return (
        "<header class=\"site-root-menubar\">"
        + "<div class=\"site-root-menubar-inner\">"
        + _render_site_home_link(site_name)
        + _render_site_space_nav(
            space_names=space_names,
            subspaces_by_space=subspaces_by_space,
            current_space_name=current_space_name,
        )
        + "<nav class=\"site-tabs\">"
        + " ".join(nav_rows)
        + "</nav>"
        + "</div>"
        + "</header>"
    )


def _render_global_site_tab_rows(
    *,
    current_tab: str | None,
    current_page: str | None,
    current_space_name: str | None,
) -> list[str]:
    if not current_space_name:
        return [
            "<a class=\"site-tab"
            + (" current" if current_tab == "new" else "")
            + "\" href=\"/site/new/index.html\">New</a>",
            "<a class=\"site-tab"
            + (" current" if current_tab == "spaces" else "")
            + "\" href=\"/site/index.html\">Spaces</a>",
            "<a class=\"site-tab"
            + (" current" if current_tab == "sources" else "")
            + "\" href=\"/site/sources/index.html\">Sources</a>",
            "<a class=\"site-tab"
            + (" current" if current_tab == "topics" else "")
            + "\" href=\"/site/topics/index.html\">Topics</a>",
            "<a class=\"site-tab"
            + (" current" if current_tab == "users" else "")
            + "\" href=\"/site/users/index.html\">Users</a>",
        ]

    resolved_current_tab = _resolve_local_space_current_tab(
        current_tab=current_tab,
        current_page=current_page,
    )
    local_rows = [
        ("new", "New", f"/spaces/{current_space_name}/site/new/index.html", None),
        ("home", "Home", f"/spaces/{current_space_name}/site/index.html", None),
        ("questions", "Questions", f"/spaces/{current_space_name}/site/questions/index.html", None),
        (
            "overview",
            "Overview",
            f"/spaces/{current_space_name}/site/overview/index.html",
            f"Overview for {current_space_name}",
        ),
        ("sources", "Sources", f"/spaces/{current_space_name}/site/sources/index.html", None),
        ("topics", "Topics", f"/spaces/{current_space_name}/site/topics/index.html", None),
        ("users", "Users", f"/spaces/{current_space_name}/site/users/index.html", None),
        ("evidence", "Evidence", f"/spaces/{current_space_name}/site/evidence/index.html", None),
        ("claims", "Claims", f"/spaces/{current_space_name}/site/claims/index.html", None),
    ]
    rows: list[str] = []
    for tab_key, label, href, aria_label in local_rows:
        link = (
            "<a class=\"site-tab"
            + (" current" if resolved_current_tab == tab_key else "")
            + "\" href=\""
            + escape(href)
            + "\""
        )
        if aria_label:
            link += " aria-label=\"" + escape(aria_label) + "\""
        link += ">" + escape(label) + "</a>"
        rows.append(link)
    return rows


def _resolve_local_space_current_tab(*, current_tab: str | None, current_page: str | None) -> str | None:
    if current_tab:
        return current_tab
    if current_page == "space_home":
        return "home"
    if current_page == "overview":
        return "overview"
    if not current_page:
        return None
    if current_page.startswith("question:"):
        return "questions"
    if current_page.startswith("source:"):
        return "sources"
    if current_page.startswith("topic:"):
        return "topics"
    if current_page.startswith("claim:"):
        return "claims"
    if current_page.startswith("evidence:"):
        return "evidence"
    return None


def _render_global_site_menu_script() -> str:
    return (
        "<script>\n"
        + "(function(){\n"
        + "  var nav=document.querySelector('.site-root-menubar .site-space-nav');\n"
        + "  if(!nav){return;}\n"
        + "  function items(){\n"
        + "    return Array.prototype.slice.call(nav.querySelectorAll('.site-space-nav-item'));\n"
        + "  }\n"
        + "  function closeAll(exceptItem){\n"
        + "    items().forEach(function(item){\n"
        + "      if(item!==exceptItem){item.removeAttribute('open');}\n"
        + "    });\n"
        + "  }\n"
        + "  nav.addEventListener('toggle', function(event){\n"
        + "    var item=event.target;\n"
        + "    if(!item||!item.classList||!item.classList.contains('site-space-nav-item')){return;}\n"
        + "    if(item.hasAttribute('open')){closeAll(item);}\n"
        + "  }, true);\n"
        + "  document.addEventListener('pointerdown', function(event){\n"
        + "    if(nav.contains(event.target)){return;}\n"
        + "    closeAll(null);\n"
        + "  });\n"
        + "  document.addEventListener('keydown', function(event){\n"
        + "    if(event.key==='Escape'){closeAll(null);}\n"
        + "  });\n"
        + "})();\n"
        + "</script>"
    )


def _render_site_home_link(site_name: str) -> str:
    return (
        "<a class=\"site-name site-home-link\" href=\"/site/index.html\">"
        + escape(site_name)
        + "</a>"
    )


def _render_site_space_nav(
    *,
    space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
    current_space_name: str | None = None,
) -> str:
    if not space_names:
        return ""
    current_top_level_space, current_subspace_name, current_subspace_title = _resolve_current_space_branch(
        space_names=space_names,
        subspaces_by_space=subspaces_by_space,
        current_space_name=current_space_name,
    )
    items: list[str] = []
    for space_name in sorted(space_names):
        display_name = _space_display_name(space_name)
        summary_label = display_name
        branch_is_current = space_name == current_top_level_space
        if branch_is_current and current_subspace_name and current_subspace_title is not None:
            summary_label = (
                display_name
                + " / "
                + _space_or_subspace_display_name(
                    space_name=current_subspace_name,
                    title=current_subspace_title,
                )
            )
        space_href = (
            "<a class=\"site-space-nav-link site-space-nav-parent"
            + (" current" if current_space_name == space_name else "")
            + "\" href=\"/spaces/"
            + escape(space_name)
            + "/site/index.html\">"
            + escape(display_name)
            + "</a>"
        )
        subspaces = subspaces_by_space.get(space_name, [])
        if subspaces:
            subspace_links = "".join(
                (
                    "<a class=\"site-space-nav-link"
                    + (" current" if current_space_name == subspace_name else "")
                    + "\" href=\"/spaces/"
                    + escape(subspace_name)
                    + "/site/index.html\">"
                    + escape(_space_or_subspace_display_name(space_name=subspace_name, title=title))
                    + "</a>"
                )
                for subspace_name, title in subspaces
            )
            items.append(
                "<details class=\"site-space-nav-item\">"
                + "<summary class=\"site-space-nav-summary"
                + (" current" if branch_is_current else "")
                + "\">"
                + escape(summary_label)
                + "</summary>"
                + "<div class=\"site-space-nav-menu\">"
                + space_href
                + subspace_links
                + "</div>"
                + "</details>"
            )
        else:
            items.append(space_href)
    return "<nav class=\"site-space-nav\" aria-label=\"Spaces\">" + "".join(items) + "</nav>"


def _resolve_current_space_branch(
    *,
    space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
    current_space_name: str | None,
) -> tuple[str | None, str | None, str | None]:
    if not current_space_name:
        return None, None, None
    for space_name in sorted(space_names):
        if current_space_name == space_name:
            return space_name, None, None
        for subspace_name, title in subspaces_by_space.get(space_name, []):
            if current_space_name == subspace_name:
                return space_name, subspace_name, title
    return None, None, None


def _render_feed_preview_thumb(entry: _FeedEntry) -> str:
    if entry.item_type != "source":
        return ""
    preview_href = entry.source_preview_href or _source_preview_site_href(entry.item_id)
    if not preview_href:
        return ""
    item_page_href = _feed_item_href(entry)
    return (
        "<a class=\"source-preview-feed-link\" href=\""
        + escape(item_page_href)
        + "\" aria-label=\"Open source: "
        + escape(entry.title)
        + "\">"
        + "<img class=\"source-preview-feed\" src=\""
        + escape(preview_href)
        + "\" alt=\"Preview for "
        + escape(entry.title)
        + "\" /></a> "
    )


def _source_preview_site_href(source_id: str, *, suffix: str = ".svg") -> str:
    return f"/site/assets/source_previews/{source_id}{suffix}"


def _source_preview_site_href_for_source(
    *,
    source: dict[str, Any],
    space_name: str,
    site_path: Path,
) -> str:
    source_id = str(source.get("source_id") or "")
    _, suffix = _resolve_front_page_image_source_path(
        source=source,
        space_name=space_name,
        site_path=site_path,
    )
    return _source_preview_site_href(source_id, suffix=suffix)


def _resolve_front_page_image_source_path(
    *,
    source: dict[str, Any],
    space_name: str,
    site_path: Path,
) -> tuple[Path | None, str]:
    if not _source_public_view_allowed(source):
        return None, ".svg"
    artifacts = source.get("artifacts")
    if not isinstance(artifacts, dict):
        return None, ".svg"
    front_page_image = artifacts.get("front_page_image")
    if not isinstance(front_page_image, str) or not front_page_image.strip():
        return None, ".svg"
    front_page_rel = Path(front_page_image.strip())
    if front_page_rel.is_absolute():
        return None, ".svg"
    suffix = front_page_rel.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return None, ".svg"
    space_root = (site_path / "spaces" / space_name).resolve()
    image_path = (space_root / front_page_rel).resolve()
    try:
        image_path.relative_to(space_root)
    except ValueError:
        return None, ".svg"
    if not image_path.is_file():
        return None, ".svg"
    return image_path, suffix


def _source_display_title(source: dict[str, Any]) -> str:
    source_semantic = source.get("source_semantic")
    semantic_display_title = source_semantic.get("display_title") if isinstance(source_semantic, dict) else None
    article_title = source_semantic.get("article_title") if isinstance(source_semantic, dict) else None
    source_display_title = source.get("display_title")
    source_title = source.get("title")
    candidates: list[object] = [semantic_display_title, article_title, source_display_title, source_title]
    return resolve_display_title(
        candidates=candidates,
        fallback=source.get("source_id"),
    )


def _source_file_href(*, source: dict[str, Any], space_name: str) -> str | None:
    if not _source_public_download_allowed(source):
        return None
    artifacts = source.get("artifacts")
    if not isinstance(artifacts, dict):
        return None
    source_file = artifacts.get("source_file")
    if not isinstance(source_file, str) or not source_file.strip():
        return None
    if Path(source_file).is_absolute():
        return None
    encoded_parts = [escape(part) for part in Path(source_file).parts if part and part != "."]
    if not encoded_parts:
        return None
    return f"/spaces/{escape(space_name)}/" + "/".join(encoded_parts)


def _render_source_preview_row(
    *,
    source: dict[str, Any],
    source_file_href: str | None,
    source_preview_href: str,
) -> str:
    if not _source_public_view_allowed(source):
        return (
            "<div class=\"source-preview-figure source-restricted-notice\">"
            "<p class=\"meta-badge\">Restricted source</p>"
            "<p class=\"summary\">Source file and extracted source text are hidden for this record.</p>"
            "</div>\n"
        )
    return (
        "<figure class=\"source-preview-figure\">"
        + "<a class=\"source-preview-link\" href=\""
        + escape(source_file_href if source_file_href else source_preview_href)
        + "\">"
        + "<img class=\"source-preview\" src=\""
        + escape(source_preview_href)
        + "\" alt=\"Preview for "
        + escape(_source_display_title(source))
        + "\" /></a>"
        + "</figure>\n"
    )


def _source_access_policy(source: dict[str, Any]) -> dict[str, Any]:
    raw = source.get("access_policy")
    if not isinstance(raw, dict):
        return {
            "restricted": False,
            "public_download": True,
            "public_source_view": True,
        }
    return raw


def _validate_source_access_policy(source: dict[str, Any]) -> None:
    raw = source.get("access_policy")
    if raw is None:
        return
    if not isinstance(raw, dict):
        raise ValueError(f"Source access_policy must be an object: {source.get('source_id')}")
    for key in ("public_download", "public_source_view"):
        if not isinstance(raw.get(key), bool):
            raise ValueError(
                f"Source access_policy.{key} must be boolean: {source.get('source_id')}"
            )


def _source_public_download_allowed(source: dict[str, Any]) -> bool:
    return _source_access_policy(source).get("public_download") is not False


def _source_public_view_allowed(source: dict[str, Any]) -> bool:
    return _source_access_policy(source).get("public_source_view") is not False


def _write_source_preview_assets(
    *,
    site_path: Path,
    preview_entries: dict[str, _SourcePreviewEntry],
    incremental: bool,
) -> None:
    previews_root = site_path / "site" / "assets" / "source_previews"
    previews_root.mkdir(parents=True, exist_ok=True)
    for source_id in sorted(preview_entries):
        entry = preview_entries[source_id]
        if entry.preview_image_path is not None:
            preview_path = previews_root / f"{entry.source_id}{entry.preview_suffix}"
            _write_binary_file(
                preview_path,
                entry.preview_image_path.read_bytes(),
                incremental=incremental,
            )
            continue
        preview_path = previews_root / f"{entry.source_id}.svg"
        _write_text_file(
            preview_path,
            _render_source_preview_svg(entry),
            incremental=incremental,
        )


def _render_source_preview_svg(entry: _SourcePreviewEntry) -> str:
    safe_title = escape(entry.title)
    safe_summary = escape(entry.summary or "No summary")
    safe_source_id = escape(entry.source_id)
    return (
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"480\" height=\"240\" viewBox=\"0 0 480 240\">"
        "<rect x=\"0\" y=\"0\" width=\"480\" height=\"240\" fill=\"#f6f3ea\"/>"
        "<rect x=\"16\" y=\"16\" width=\"448\" height=\"208\" rx=\"8\" fill=\"#ffffff\" stroke=\"#d9d2c4\"/>"
        "<text x=\"32\" y=\"56\" font-size=\"14\" font-family=\"Arial, sans-serif\" fill=\"#5f5a52\">Source preview</text>"
        f"<text x=\"32\" y=\"92\" font-size=\"20\" font-family=\"Arial, sans-serif\" fill=\"#1f1f1f\">{safe_title}</text>"
        f"<text x=\"32\" y=\"132\" font-size=\"13\" font-family=\"Arial, sans-serif\" fill=\"#4b4b4b\">{safe_summary}</text>"
        f"<text x=\"32\" y=\"198\" font-size=\"12\" font-family=\"Arial, sans-serif\" fill=\"#777\">{safe_source_id}</text>"
        "</svg>\n"
    )
