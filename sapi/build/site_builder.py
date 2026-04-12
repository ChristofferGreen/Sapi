"""Deterministic site-builder and site-root New-index projection functions."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html import escape
from pathlib import Path
import re
from typing import Any

from sapi.build.projection import SpaceProjection, load_space_projection
from sapi.core.site_scope import load_site_scope, load_subspaces_metadata
from sapi.lint.lint_engine import LintSummary, default_lint_summary
from sapi.profiles.persona_catalog import load_seeded_persona_catalog

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


@dataclass(frozen=True)
class _SourcePreviewEntry:
    source_id: str
    title: str
    summary: str


@dataclass(frozen=True)
class _SearchIndexEntry:
    item_type: str
    item_id: str
    title: str
    href: str
    search_text: str


@dataclass(frozen=True)
class _SpaceLayoutContext:
    site_name: str
    space_name: str
    all_space_names: list[str]
    subspaces: list[tuple[str, str | None]]
    topics: list[dict[str, Any]]
    tabs: tuple[str, ...]


def build_space_site(
    space_root: Path,
    *,
    incremental: bool,
    site_presentation_mode: str = "public",
) -> BuildResult:
    """Build deterministic space HTML from canonical JSON artifacts only."""
    projection = load_space_projection(space_root)
    space_name = space_root.name
    output_root = space_root / "site"
    output_root.mkdir(parents=True, exist_ok=True)
    site_path = space_root.parent.parent
    context = _build_layout_context(space_root=space_root, projection=projection, site_path=site_path)
    persona_rows = _load_persona_rows()
    run_ids = _load_run_ids(space_root)

    generated_files: list[Path] = []
    generated_files.extend(
        _write_source_pages(
            output_root=output_root,
            projection=projection,
            incremental=incremental,
            context=context,
        )
    )
    generated_files.extend(
        _write_topic_pages(
            output_root=output_root,
            projection=projection,
            incremental=incremental,
            site_presentation_mode=site_presentation_mode,
            context=context,
        )
    )
    generated_files.extend(
        _write_space_tab_pages(
            output_root=output_root,
            projection=projection,
            context=context,
            persona_rows=persona_rows,
            run_ids=run_ids,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_user_profile_pages(
            output_root=output_root,
            context=context,
            persona_rows=persona_rows,
            incremental=incremental,
        )
    )
    generated_files.extend(
        _write_space_search_page(
            output_root=output_root,
            projection=projection,
            context=context,
            run_ids=run_ids,
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
        ),
        incremental=incremental,
    )
    generated_files.append(index_path)

    content_hashes = {str(path.relative_to(output_root)): _sha256(path) for path in sorted(generated_files)}
    lint_summary = default_lint_summary(issues=projection.lint_issues)
    return BuildResult(
        space_name=space_name,
        output_root=output_root,
        generated_files=sorted(generated_files),
        content_hashes=content_hashes,
        lint_summary=lint_summary,
    )


def refresh_site_new_index(site_path: Path, *, incremental: bool) -> Path:
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
        entries.extend(_space_feed_entries(space_name=space_name, projection=projection))
        for source in projection.sources:
            source_id = str(source["source_id"])
            if source_id in preview_entries:
                continue
            preview_entries[source_id] = _SourcePreviewEntry(
                source_id=source_id,
                title=str(source["title"]),
                summary=_compact_summary(str(source.get("summary") or source.get("context") or "")),
            )
        subspaces_by_space[space_name] = _load_subspaces(space_root)

    _sort_feed_entries(entries)

    site_name = _resolve_site_name(site_path)
    site_root = site_path / "site"
    site_root.mkdir(parents=True, exist_ok=True)
    _write_text_file(
        site_root / "index.html",
        _render_site_root_index(
            site_name=site_name,
            space_names=space_names,
            subspaces_by_space=subspaces_by_space,
        ),
        incremental=incremental,
    )

    persona_rows = _load_persona_rows()
    _write_site_users_pages(
        site_root=site_root,
        site_name=site_name,
        persona_rows=persona_rows,
        space_names=space_names,
        incremental=incremental,
    )
    _write_source_preview_assets(
        site_path=site_path,
        preview_entries=preview_entries,
        incremental=incremental,
    )

    new_root = site_root / "new"
    new_root.mkdir(parents=True, exist_ok=True)
    pages = _paginate(entries, TAB_PAGE_SIZE)
    for page_number, page_entries in enumerate(pages, start=1):
        page_path = _paginated_page_path(new_root, page_number=page_number)
        _write_text_file(
            page_path,
            _render_site_new_page(
                site_name=site_name,
                page_entries=page_entries,
                page_number=page_number,
                page_count=len(pages),
            ),
            incremental=incremental,
        )
    return _paginated_page_path(new_root, page_number=1)


def _write_source_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    incremental: bool,
    context: _SpaceLayoutContext,
) -> list[Path]:
    sources_dir = output_root / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source in sorted(projection.sources, key=lambda item: item["source_id"]):
        source_path = sources_dir / f"{source['source_id']}.html"
        source_summary = _compact_summary(str(source.get("summary") or source.get("context") or ""))
        source_file_href = _source_file_href(source=source, space_name=context.space_name)
        source_preview_href = _source_preview_site_href(str(source["source_id"]))
        source_preview_row = (
            "<a class=\"source-preview-link\" href=\""
            + escape(source_file_href if source_file_href else "#")
            + "\">"
            + "<img class=\"source-preview\" src=\""
            + escape(source_preview_href)
            + "\" alt=\"Preview for "
            + escape(str(source["title"]))
            + "\" /></a>\n"
        )
        source_file_row = (
            "<p class=\"source-file-link\">"
            + (
                f"<a href=\"{escape(source_file_href)}\">Open source PDF</a>"
                if source_file_href
                else "Source file unavailable"
            )
            + "</p>\n"
        )
        body = (
            f"<h1>{escape(str(source['title']))}</h1>\n"
            + (f"<p class=\"source-summary\">{escape(source_summary)}</p>\n" if source_summary else "")
            + source_preview_row
            + source_file_row
            + f"<p>source_id: {escape(str(source['source_id']))}</p>\n"
            + _render_page_comment_section(
                page_payload=source,
                default_page_ref=f"source:{source['source_id']}",
            )
        )
        _write_text_file(
            source_path,
            _render_space_layout(
                title=str(source["title"]),
                body=body,
                context=context,
                current_tab="sources",
            ),
            incremental=incremental,
        )
        written.append(source_path)
    return written


def _write_topic_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    incremental: bool,
    site_presentation_mode: str,
    context: _SpaceLayoutContext,
) -> list[Path]:
    topics_dir = output_root / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for topic in sorted(projection.topics, key=lambda item: item["topic_id"]):
        topic_path = topics_dir / f"{topic['topic_id']}.html"
        _write_text_file(
            topic_path,
            _render_topic_page(
                topic,
                site_presentation_mode=site_presentation_mode,
                context=context,
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
) -> str:
    source_rows = "\n".join(
        f"<li><a href=\"./sources/{escape(source['source_id'])}.html\">{escape(source['title'])}</a></li>"
        for source in sorted(projection.sources, key=lambda item: item["source_id"])
    )
    topic_rows = "\n".join(
        f"<li><a href=\"./topics/{escape(topic['topic_id'])}.html\">{escape(topic['title'])}</a></li>"
        for topic in sorted(projection.topics, key=lambda item: item["topic_id"])
    )
    body = (
        f"<h1>{escape(space_name)}</h1>\n"
        "<h2>Sources</h2>\n<ul>\n"
        + source_rows
        + "\n</ul>\n"
        + "<h2>Topics</h2>\n<ul>\n"
        + topic_rows
        + "\n</ul>\n"
    )
    return _render_space_layout(
        title=f"{space_name} - Space Home",
        body=body,
        context=context,
        current_tab=None,
        current_page="space_home",
    )


def _render_topic_page(
    topic: dict[str, object],
    *,
    site_presentation_mode: str,
    context: _SpaceLayoutContext,
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
        )
        for index, section in enumerate(sections, start=1)
    )
    parent_link_row = _render_pinned_parent_link(topic)
    body = (
        f"<h1>{escape(str(topic['title']))}</h1>\n"
        + (
            "<p class=\"topic-structure\" "
            f"data-structure-type=\"{escape(structure_type)}\">Structure: {escape(structure_type)}</p>\n"
        )
        + parent_link_row
        + section_rows
        + _render_page_comment_section(
            page_payload=topic,
            default_page_ref=f"topic:{topic['topic_id']}",
        )
    )
    return _render_space_layout(
        title=str(topic["title"]),
        body=body,
        context=context,
        current_tab="topics",
        current_page=f"topic:{topic['topic_id']}",
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


def _render_page_comment_section(*, page_payload: dict[str, object], default_page_ref: str) -> str:
    comment_section = page_payload.get("comment_section")
    if not isinstance(comment_section, dict):
        return ""
    comments = comment_section.get("comments")
    if not isinstance(comments, list):
        return ""
    page_ref = str(comment_section.get("page_ref") or default_page_ref)
    rows: list[str] = []
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        comment_uid = str(comment.get("comment_uid") or "").strip()
        if not comment_uid:
            continue
        persona_id = str(comment.get("persona_id") or "").strip()
        comment_no = str(comment.get("comment_no") or "")
        body = str(comment.get("body") or "")
        parent_uid_raw = comment.get("parent_comment_uid")
        parent_uid = str(parent_uid_raw).strip() if isinstance(parent_uid_raw, str) else ""
        social_vote = _resolve_comment_social_vote(page_ref=page_ref, comment=comment)
        permalink = str(comment.get("permalink") or f"#{comment_uid}")
        thread_state_key = str(comment.get("thread_state_key") or comment_uid)
        thread_expansion_key = str(comment.get("thread_expansion_key") or comment_uid)
        rows.append(
            (
                f"<article class=\"comment-row\" id=\"{escape(comment_uid)}\" "
                f"data-thread-state-key=\"{escape(thread_state_key)}\" "
                f"data-thread-expansion-key=\"{escape(thread_expansion_key)}\">"
                f"<header><a class=\"comment-permalink\" href=\"{escape(permalink)}\">Permalink</a> "
                f"<span class=\"comment-no\">{escape(comment_no)}</span> "
                f"<span class=\"comment-persona\">{escape(persona_id)}</span></header>"
                f"<p class=\"comment-body\">{escape(body)}</p>"
                + (
                    f"<p class=\"comment-parent\">Replying to {escape(parent_uid)}</p>"
                    if parent_uid
                    else ""
                )
                + (
                    "<p class=\"comment-score\" "
                    f"data-upvotes=\"{social_vote['upvotes']}\" "
                    f"data-downvotes=\"{social_vote['downvotes']}\" "
                    f"data-score=\"{social_vote['score']}\">"
                    f"upvotes={social_vote['upvotes']} downvotes={social_vote['downvotes']} "
                    f"score={social_vote['score']}</p>"
                )
                + "</article>"
            )
        )

    moderator_rows = _render_moderator_outcomes(comment_section=comment_section)
    if not rows and not moderator_rows:
        return ""
    return (
        "<section class=\"comment-thread\">"
        "<h2>Comment Thread</h2>"
        + "".join(rows)
        + moderator_rows
        + "</section>"
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
    comment_uid = str(comment.get("comment_uid") or "").strip()
    persona_id = str(comment.get("persona_id") or "").strip()
    body = str(comment.get("body") or "")
    turn = comment.get("turn")
    position = "social"
    if isinstance(turn, dict) and isinstance(turn.get("position"), str) and turn.get("position"):
        position = str(turn["position"]).strip()
    seed = f"{page_ref}|{comment_uid}|{persona_id}|{position}|{body[:120]}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    upvotes = int(digest[:8], 16) % 31 + 5
    downvotes = int(digest[8:16], 16) % 21
    if position in {"support", "synthesis"}:
        upvotes += 4
    elif position in {"challenge", "rebuttal"}:
        downvotes += 4
    return {"upvotes": upvotes, "downvotes": downvotes, "score": upvotes - downvotes}


def _render_moderator_outcomes(*, comment_section: dict[str, object]) -> str:
    outcomes = comment_section.get("moderator_outcomes")
    if not isinstance(outcomes, dict):
        return ""
    moderator_check = str(outcomes.get("moderator_check") or "").strip()
    guardrail_checks = outcomes.get("guardrail_checks")
    outcome_sections = outcomes.get("outcome_sections")
    rows: list[str] = []
    if moderator_check:
        rows.append(f"<p class=\"moderator-check\">{escape(moderator_check)}</p>")
    if isinstance(guardrail_checks, dict):
        rows.append("<ul class=\"moderator-guardrails\">")
        for key in ("claim_citation", "anti_repetition", "strongest_opposing_point_ack"):
            check_row = guardrail_checks.get(key)
            if not isinstance(check_row, dict):
                continue
            passed = int(check_row.get("passed", 0))
            failed = int(check_row.get("failed", 0))
            rows.append(
                f"<li data-check-key=\"{escape(key)}\">{escape(key)}: passed={passed} failed={failed}</li>"
            )
        rows.append("</ul>")
    if isinstance(outcome_sections, dict):
        for section_key in ("Consensus", "Open Disagreements", "Missing Evidence Priorities"):
            section_rows = outcome_sections.get(section_key)
            rows.append(f"<h3>{escape(section_key)}</h3>")
            if isinstance(section_rows, list) and section_rows:
                rows.append("<ul>")
                for row in section_rows:
                    rows.append(f"<li>{escape(str(row))}</li>")
                rows.append("</ul>")
            else:
                rows.append("<p>(none)</p>")
    return "".join(rows)


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
) -> str:
    heading = escape(str(section["heading"]))
    body = str(section["body"])
    clean_body, annotation_groups = _extract_claim_annotations(body)
    rows = [
        "<section>",
        f"<h2>{heading}</h2>",
        f"<p class=\"topic-section-body\">{escape(clean_body)}</p>",
    ]
    if annotation_groups:
        rows.append(_render_claim_annotation_links(annotation_groups, section_index=section_index))
        rows.append(
            _render_claim_annotation_details(
                annotation_groups,
                section_index=section_index,
                site_presentation_mode=site_presentation_mode,
            )
        )
    rows.append("</section>")
    return "".join(rows)


def _extract_claim_annotations(body: str) -> tuple[str, list[list[str]]]:
    pattern = re.compile(r"\[\[claims:([^\]]+)\]\]")
    annotation_groups: list[list[str]] = []
    for match in pattern.finditer(body):
        refs = [token.strip() for token in match.group(1).split(",") if token.strip()]
        if refs:
            annotation_groups.append(refs)
    clean_body = pattern.sub("", body)
    clean_body = re.sub(r"\s{2,}", " ", clean_body).strip()
    return clean_body, annotation_groups


def _render_claim_annotation_links(annotation_groups: list[list[str]], *, section_index: int) -> str:
    rows = []
    for annotation_index, _ in enumerate(annotation_groups, start=1):
        details_id = f"claim-details-s{section_index}-a{annotation_index}"
        rows.append(
            f"<a class=\"claim-details-link\" href=\"#{details_id}\">Claim details {annotation_index}</a>"
        )
    return "<p class=\"claim-details-links\">" + " ".join(rows) + "</p>"


def _render_claim_annotation_details(
    annotation_groups: list[list[str]],
    *,
    section_index: int,
    site_presentation_mode: str,
) -> str:
    details_rows: list[str] = []
    for annotation_index, claim_ids in enumerate(annotation_groups, start=1):
        details_id = f"claim-details-s{section_index}-a{annotation_index}"
        claim_link_rows = []
        fallback_rows = []
        for claim_index, claim_id in enumerate(claim_ids, start=1):
            href = f"../claims/{claim_id}.html"
            if site_presentation_mode == "debug":
                claim_link_rows.append(
                    "<li class=\"claim-details-item debug\" "
                    f"data-claim-id=\"{escape(claim_id)}\" "
                    f"data-claim-href=\"{escape(href)}\">"
                    f"<a href=\"{escape(href)}\">{escape(claim_id)}</a></li>"
                )
                fallback_rows.append(f"<li><a href=\"{escape(href)}\">{escape(claim_id)}</a></li>")
            else:
                claim_link_rows.append(
                    "<li class=\"claim-details-item\">"
                    f"<a href=\"{escape(href)}\">Claim reference {claim_index}</a></li>"
                )
                fallback_rows.append(
                    f"<li><a href=\"{escape(href)}\">Claim reference {claim_index}</a></li>"
                )
        details_rows.append(
            (
                f"<details id=\"{details_id}\" class=\"claim-details\">"
                "<summary>Claim details</summary>"
                "<ul class=\"claim-details-list\">"
                + "".join(claim_link_rows)
                + "</ul>"
                "<noscript><ul class=\"claim-details-fallback\">"
                + "".join(fallback_rows)
                + "</ul></noscript>"
                "</details>"
            )
        )
    return "".join(details_rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text_file(path: Path, content: str, *, incremental: bool) -> None:
    if incremental and path.is_file() and path.read_text() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


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
    return _SpaceLayoutContext(
        site_name=_resolve_site_name(site_path),
        space_name=space_root.name,
        all_space_names=_discover_site_spaces(site_path),
        subspaces=_load_subspaces(space_root),
        topics=sorted(projection.topics, key=lambda item: str(item.get("topic_id", ""))),
        tabs=tuple(_resolve_space_tabs(space_root)),
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
    return sorted(path.name for path in spaces_root.iterdir() if path.is_dir())


def _load_subspaces(space_root: Path) -> list[tuple[str, str | None]]:
    try:
        metadata = load_subspaces_metadata(space_root=space_root)
    except FileNotFoundError:
        return []
    return sorted((entry.space_name, entry.title) for entry in metadata.subspaces)


def _load_run_ids(space_root: Path) -> list[str]:
    runs_root = space_root / "runs"
    if not runs_root.exists():
        return []
    run_ids: list[str] = []
    for candidate in sorted(runs_root.glob("*")):
        if not candidate.is_dir():
            continue
        if (candidate / "run.md").is_file():
            run_ids.append(candidate.name)
    return run_ids


def _resolve_space_tabs(space_root: Path) -> list[str]:
    tabs = ["new", "sources", "topics", "users"]
    if _load_run_ids(space_root):
        tabs.append("runs")
    return tabs


def _load_persona_rows() -> list[dict[str, Any]]:
    repo_root = Path(__file__).resolve().parents[2]
    rows = load_seeded_persona_catalog(repo_root=repo_root)
    return sorted(rows, key=lambda row: str(row["persona_id"]))


def _space_feed_entries(*, space_name: str, projection: SpaceProjection) -> list[_FeedEntry]:
    entries: list[_FeedEntry] = []
    for source in projection.sources:
        entries.append(
            _FeedEntry(
                timestamp=str(source.get("ingested_at") or source.get("date") or ""),
                space_name=space_name,
                item_type="source",
                item_id=str(source["source_id"]),
                title=str(source["title"]),
                summary=_compact_summary(str(source.get("summary") or source.get("context") or "")),
            )
        )
    for topic in projection.topics:
        summary = ""
        if isinstance(topic.get("summary"), str):
            summary = topic["summary"]
        else:
            sections = topic.get("sections")
            if isinstance(sections, list) and sections:
                first = sections[0]
                if isinstance(first, dict) and isinstance(first.get("body"), str):
                    summary = first["body"]
        entries.append(
            _FeedEntry(
                timestamp=str(topic.get("updated_at") or topic.get("created_at") or ""),
                space_name=space_name,
                item_type="topic",
                item_id=str(topic["topic_id"]),
                title=str(topic["title"]),
                summary=_compact_summary(summary),
            )
        )
    return entries


def _sort_feed_entries(entries: list[_FeedEntry]) -> None:
    entries.sort(key=lambda item: (item.space_name, item.item_type, item.item_id))
    entries.sort(key=lambda item: item.timestamp, reverse=True)


def _compact_summary(text: str, *, limit: int = 120) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return ""
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _write_space_tab_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    persona_rows: list[dict[str, Any]],
    run_ids: list[str],
    incremental: bool,
) -> list[Path]:
    written: list[Path] = []
    feed_entries = _space_feed_entries(space_name=context.space_name, projection=projection)
    _sort_feed_entries(feed_entries)

    tab_rows: dict[str, list[str]] = {
        "new": [
            (
                "<li>"
                + _render_feed_preview_thumb(entry)
                + f"<span class=\"meta\">{escape(entry.timestamp or 'unknown')} | {escape(entry.item_type)}</span> "
                + f"<a href=\"/spaces/{escape(entry.space_name)}/site/{escape(entry.item_type)}s/{escape(entry.item_id)}.html\">"
                + escape(entry.title)
                + "</a>"
                + (f"<p class=\"summary\">{escape(entry.summary)}</p>" if entry.summary else "")
                + "</li>"
            )
            for entry in feed_entries
        ],
        "sources": [
            (
                f"<li><a href=\"/spaces/{escape(context.space_name)}/site/sources/{escape(str(source['source_id']))}.html\">"
                + escape(str(source["title"]))
                + "</a></li>"
            )
            for source in sorted(projection.sources, key=lambda item: str(item["source_id"]))
        ],
        "topics": [
            (
                f"<li><a href=\"/spaces/{escape(context.space_name)}/site/topics/{escape(str(topic['topic_id']))}.html\">"
                + escape(str(topic["title"]))
                + "</a></li>"
            )
            for topic in sorted(projection.topics, key=lambda item: str(item["topic_id"]))
        ],
        "users": [
            (
                f"<li><a href=\"/spaces/{escape(context.space_name)}/site/users/persona-{escape(str(row['persona_id']))}.html\">"
                + escape(str(row["display_name"]))
                + "</a></li>"
            )
            for row in persona_rows
        ],
    }
    if "runs" in context.tabs:
        tab_rows["runs"] = [
            f"<li><a href=\"/spaces/{escape(context.space_name)}/runs/{escape(run_id)}/run.md\">{escape(run_id)}</a></li>"
            for run_id in sorted(run_ids, reverse=True)
        ]

    for tab_key in context.tabs:
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
            body = (
                f"<h1>{escape(tab_title)}</h1>\n"
                + f"<p class=\"tab-page-size\" data-tab-page-size=\"{TAB_PAGE_SIZE}\">Page size: {TAB_PAGE_SIZE}</p>\n"
                + "<ul>\n"
                + "\n".join(page_rows)
                + "\n</ul>\n"
                + pagination
            )
            _write_text_file(
                page_path,
                _render_space_layout(
                    title=f"{context.space_name} - {tab_title}",
                    body=body,
                    context=context,
                    current_tab=tab_key,
                ),
                incremental=incremental,
            )
            written.append(page_path)
    return written


def _write_space_user_profile_pages(
    *,
    output_root: Path,
    context: _SpaceLayoutContext,
    persona_rows: list[dict[str, Any]],
    incremental: bool,
) -> list[Path]:
    users_root = output_root / "users"
    users_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for row in persona_rows:
        persona_id = str(row["persona_id"])
        path = users_root / f"persona-{persona_id}.html"
        body = (
            f"<h1>{escape(str(row['display_name']))}</h1>\n"
            + f"<p>persona_id: {escape(persona_id)}</p>\n"
            + "<p>Space-scoped profile page for this persona.</p>\n"
        )
        _write_text_file(
            path,
            _render_space_layout(
                title=f"{context.space_name} - persona-{persona_id}",
                body=body,
                context=context,
                current_tab="users",
            ),
            incremental=incremental,
        )
        written.append(path)
    return written


def _write_space_search_page(
    *,
    output_root: Path,
    projection: SpaceProjection,
    context: _SpaceLayoutContext,
    run_ids: list[str],
    incremental: bool,
) -> list[Path]:
    search_root = output_root / "search"
    search_root.mkdir(parents=True, exist_ok=True)
    search_path = search_root / "index.html"
    entries = _space_search_entries(
        space_name=context.space_name,
        projection=projection,
        run_ids=run_ids,
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
        + "<ul class=\"search-index\">\n"
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
            title=f"{context.space_name} - Search",
            body=body,
            context=context,
            current_tab=None,
        ),
        incremental=incremental,
    )
    return [search_path]


def _space_search_entries(
    *,
    space_name: str,
    projection: SpaceProjection,
    run_ids: list[str],
) -> list[_SearchIndexEntry]:
    entries: list[_SearchIndexEntry] = []
    for source in sorted(projection.sources, key=lambda item: str(item["source_id"])):
        source_id = str(source["source_id"])
        title = str(source["title"])
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
    for run_id in sorted(run_ids, reverse=True):
        entries.append(
            _SearchIndexEntry(
                item_type="run",
                item_id=run_id,
                title=run_id,
                href=f"/spaces/{space_name}/runs/{run_id}/run.md",
                search_text=f"run {run_id}",
            )
        )
    return entries


def _render_space_layout(
    *,
    title: str,
    body: str,
    context: _SpaceLayoutContext,
    current_tab: str | None,
    current_page: str | None = None,
) -> str:
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(title)
        + "</title></head><body>\n"
        + "<form class=\"top-search\" style=\"position:relative;z-index:1\" action=\"/spaces/"
        + escape(context.space_name)
        + "/site/search/index.html\" method=\"get\">"
        + "<label for=\"space-search-q\">Search</label> "
        + "<input id=\"space-search-q\" type=\"search\" name=\"q\"/></form>\n"
        + _render_space_sidebar(context=context, current_page=current_page)
        + "<main>\n"
        + _render_space_tabs(context=context, current_tab=current_tab)
        + body
        + "\n</main>\n"
        + "</body></html>\n"
    )


def _render_space_sidebar(*, context: _SpaceLayoutContext, current_page: str | None) -> str:
    space_rows = "\n".join(
        (
            "<li><a"
            + (" class=\"current\"" if space_name == context.space_name else "")
            + f" href=\"/spaces/{escape(space_name)}/site/index.html\">{escape(space_name)}</a></li>"
        )
        for space_name in context.all_space_names
    )
    if context.subspaces:
        subspace_rows = "\n".join(
            (
                f"<li><a href=\"/spaces/{escape(subspace_name)}/site/index.html\">"
                + escape(title if title else subspace_name)
                + "</a></li>"
            )
            for subspace_name, title in context.subspaces
        )
    else:
        subspace_rows = "<li><span>None</span></li>"
    topic_rows = "\n".join(
        (
            "<li><a"
            + (" class=\"current\"" if current_page == f"topic:{topic['topic_id']}" else "")
            + f" href=\"/spaces/{escape(context.space_name)}/site/topics/{escape(str(topic['topic_id']))}.html\">"
            + escape(str(topic["title"]))
            + "</a></li>"
        )
        for topic in context.topics
    )
    return (
        "<aside class=\"sidebar\" style=\"position:relative;z-index:2\">\n"
        + f"<p class=\"site-name\">{escape(context.site_name)}</p>\n"
        + f"<p class=\"space-name\">{escape(context.space_name)}</p>\n"
        + "<nav>\n"
        + "<ul><li><a"
        + (" class=\"current\"" if current_page == "space_home" else "")
        + f" href=\"/spaces/{escape(context.space_name)}/site/index.html\">Space Home</a></li></ul>\n"
        + "<details class=\"sidebar-spaces\" open><summary>Spaces</summary><ul>\n"
        + space_rows
        + "\n</ul></details>\n"
        + "<details class=\"sidebar-subspaces\" open><summary>Subspaces</summary><ul>\n"
        + subspace_rows
        + "\n</ul></details>\n"
        + "<details class=\"sidebar-topics\" open><summary>Topics</summary><ul>\n"
        + topic_rows
        + "\n</ul></details>\n"
        + "</nav>\n"
        + "</aside>\n"
    )


def _render_space_tabs(*, context: _SpaceLayoutContext, current_tab: str | None) -> str:
    tab_labels = {
        "new": "New",
        "sources": "Sources",
        "topics": "Topics",
        "users": "Users",
        "runs": "Runs",
    }
    rows = []
    for tab_key in context.tabs:
        label = tab_labels.get(tab_key, tab_key.capitalize())
        rows.append(
            "<a class=\"tab"
            + (" current" if current_tab == tab_key else "")
            + f"\" href=\"/spaces/{escape(context.space_name)}/site/{escape(tab_key)}/index.html\">"
            + escape(label)
            + "</a>"
        )
    rows.append(
        "<a class=\"claims-secondary\" href=\"/spaces/"
        + escape(context.space_name)
        + "/site/claims/index.html\">Claims</a>"
    )
    return "<nav class=\"tabs\" aria-label=\"Primary tabs\">" + " ".join(rows) + "</nav>\n"


def _paginate(items: list[Any], page_size: int) -> list[list[Any]]:
    if not items:
        return [[]]
    return [items[index : index + page_size] for index in range(0, len(items), page_size)]


def _paginated_page_path(root: Path, *, page_number: int) -> Path:
    if page_number == 1:
        return root / "index.html"
    return root / "page" / str(page_number) / "index.html"


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
    incremental: bool,
) -> None:
    users_root = site_root / "users"
    users_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for row in persona_rows:
        persona_id = str(row["persona_id"])
        space_links = " ".join(
            (
                f"<a href=\"/spaces/{escape(space_name)}/site/users/persona-{escape(persona_id)}.html\">"
                + escape(space_name)
                + "</a>"
            )
            for space_name in sorted(space_names)
        )
        rows.append(
            "<li>"
            + escape(str(row["display_name"]))
            + f" ({escape(persona_id)})"
            + (f"<div class=\"space-scoped-links\">{space_links}</div>" if space_links else "")
            + "</li>"
        )

    pages = _paginate(rows, TAB_PAGE_SIZE)
    for page_number, page_rows in enumerate(pages, start=1):
        page_path = _paginated_page_path(users_root, page_number=page_number)
        body = (
            f"<h1>{escape(site_name)} Users</h1>\n"
            + "<ul>\n"
            + "\n".join(page_rows)
            + "\n</ul>\n"
            + _render_pagination(
                page_number=page_number,
                page_count=len(pages),
                mode="tab",
                base_href="/site/users",
            )
        )
        _write_text_file(
            page_path,
            "<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>"
            + escape(site_name)
            + " Users</title></head><body>\n"
            + "<nav class=\"site-tabs\"><a href=\"/site/new/index.html\">New</a> "
            + "<a class=\"current\" href=\"/site/users/index.html\">Users</a></nav>\n"
            + body
            + "\n</body></html>\n",
            incremental=incremental,
        )


def _render_site_root_index(
    *,
    site_name: str,
    space_names: list[str],
    subspaces_by_space: dict[str, list[tuple[str, str | None]]],
) -> str:
    rows = []
    for space_name in sorted(space_names):
        subspaces = subspaces_by_space.get(space_name, [])
        if subspaces:
            subspace_rows = "<ul>" + "".join(
                (
                    "<li>"
                    + escape(title if title else subspace_name)
                    + " ("
                    + escape(subspace_name)
                    + ")</li>"
                )
                for subspace_name, title in subspaces
            ) + "</ul>"
        else:
            subspace_rows = ""
        rows.append(
            "<li><a href=\"/spaces/"
            + escape(space_name)
            + "/site/index.html\">"
            + escape(space_name)
            + "</a>"
            + subspace_rows
            + "</li>"
        )
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(site_name)
        + "</title></head><body>\n"
        + f"<h1>{escape(site_name)}</h1>\n"
        + "<nav class=\"site-tabs\"><a href=\"/site/new/index.html\">New</a> "
        + "<a href=\"/site/users/index.html\">Users</a></nav>\n"
        + "<h2>Spaces</h2>\n<ul>\n"
        + "\n".join(rows)
        + "\n</ul>\n"
        + "</body></html>\n"
    )


def _render_site_new_page(
    *,
    site_name: str,
    page_entries: list[_FeedEntry],
    page_number: int,
    page_count: int,
) -> str:
    rows = "\n".join(
        (
            "<li>"
            + _render_feed_preview_thumb(entry)
            + f"<span class=\"meta\">{escape(entry.timestamp or 'unknown')} | {escape(entry.space_name)} | "
            + f"{escape(entry.item_type)}</span> "
            + f"<a href=\"/spaces/{escape(entry.space_name)}/site/{escape(entry.item_type)}s/{escape(entry.item_id)}.html\">"
            + escape(entry.title)
            + "</a>"
            + (f"<p class=\"summary\">{escape(entry.summary)}</p>" if entry.summary else "")
            + "</li>"
        )
        for entry in page_entries
    )
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>New</title></head><body>\n"
        + "<nav class=\"site-tabs\"><a class=\"current\" href=\"/site/new/index.html\">New</a> "
        + "<a href=\"/site/users/index.html\">Users</a></nav>\n"
        + f"<h1>New</h1>\n<p>{escape(site_name)}</p>\n<ul>\n"
        + rows
        + "\n</ul>\n"
        + _render_pagination(
            page_number=page_number,
            page_count=page_count,
            mode="feed",
            base_href="/site/new",
        )
        + "</body></html>\n"
    )


def _render_feed_preview_thumb(entry: _FeedEntry) -> str:
    if entry.item_type != "source":
        return ""
    source_page_href = (
        f"/spaces/{entry.space_name}/site/sources/{entry.item_id}.html"
    )
    return (
        "<a class=\"source-preview-feed-link\" href=\""
        + escape(source_page_href)
        + "\">"
        + "<img class=\"source-preview-feed\" src=\""
        + escape(_source_preview_site_href(entry.item_id))
        + "\" alt=\"Preview for "
        + escape(entry.title)
        + "\" /></a> "
    )


def _source_preview_site_href(source_id: str) -> str:
    return f"/site/assets/source_previews/{source_id}.svg"


def _source_file_href(*, source: dict[str, Any], space_name: str) -> str | None:
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
