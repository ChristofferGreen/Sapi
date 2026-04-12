"""Deterministic site-builder and site-root New-index projection functions."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html import escape
from pathlib import Path
import re

from sapi.build.projection import SpaceProjection, load_space_projection
from sapi.lint.lint_engine import LintSummary, default_lint_summary

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


@dataclass(frozen=True)
class BuildResult:
    """Summary of one deterministic space build invocation."""

    space_name: str
    output_root: Path
    generated_files: list[Path]
    content_hashes: dict[str, str]
    lint_summary: LintSummary


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

    generated_files: list[Path] = []
    generated_files.extend(
        _write_source_pages(output_root=output_root, projection=projection, incremental=incremental)
    )
    generated_files.extend(
        _write_topic_pages(
            output_root=output_root,
            projection=projection,
            incremental=incremental,
            site_presentation_mode=site_presentation_mode,
        )
    )

    index_path = output_root / "index.html"
    _write_text_file(
        index_path,
        _render_space_index(space_name=space_name, projection=projection),
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
    entries: list[tuple[str, str, str, str, str]] = []
    for space_root in sorted(spaces_root.glob("*")):
        if not space_root.is_dir():
            continue
        projection = load_space_projection(space_root)
        for source in projection.sources:
            entries.append(
                (
                    str(source.get("ingested_at") or source.get("date") or ""),
                    space_root.name,
                    "source",
                    source["source_id"],
                    source["title"],
                )
            )
        for topic in projection.topics:
            entries.append(
                (
                    str(topic.get("updated_at") or topic.get("created_at") or ""),
                    space_root.name,
                    "topic",
                    topic["topic_id"],
                    topic["title"],
                )
            )

    entries.sort(key=lambda row: (row[0], row[1], row[2], row[3]), reverse=True)
    new_root = site_path / "site" / "new"
    new_root.mkdir(parents=True, exist_ok=True)
    index_path = new_root / "index.html"
    _write_text_file(index_path, _render_site_new_index(entries), incremental=incremental)
    return index_path


def _write_source_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    incremental: bool,
) -> list[Path]:
    sources_dir = output_root / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source in sorted(projection.sources, key=lambda item: item["source_id"]):
        source_path = sources_dir / f"{source['source_id']}.html"
        _write_text_file(source_path, _render_source_page(source), incremental=incremental)
        written.append(source_path)
    return written


def _write_topic_pages(
    *,
    output_root: Path,
    projection: SpaceProjection,
    incremental: bool,
    site_presentation_mode: str,
) -> list[Path]:
    topics_dir = output_root / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for topic in sorted(projection.topics, key=lambda item: item["topic_id"]):
        topic_path = topics_dir / f"{topic['topic_id']}.html"
        _write_text_file(
            topic_path,
            _render_topic_page(topic, site_presentation_mode=site_presentation_mode),
            incremental=incremental,
        )
        written.append(topic_path)
    return written


def _render_space_index(*, space_name: str, projection: SpaceProjection) -> str:
    source_rows = "\n".join(
        f"<li><a href=\"./sources/{escape(source['source_id'])}.html\">{escape(source['title'])}</a></li>"
        for source in sorted(projection.sources, key=lambda item: item["source_id"])
    )
    topic_rows = "\n".join(
        f"<li><a href=\"./topics/{escape(topic['topic_id'])}.html\">{escape(topic['title'])}</a></li>"
        for topic in sorted(projection.topics, key=lambda item: item["topic_id"])
    )
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(space_name)
        + " - Space Home</title></head><body>\n"
        + f"<h1>{escape(space_name)}</h1>\n"
        + "<h2>Sources</h2>\n<ul>\n"
        + source_rows
        + "\n</ul>\n"
        + "<h2>Topics</h2>\n<ul>\n"
        + topic_rows
        + "\n</ul>\n"
        + "</body></html>\n"
    )


def _render_source_page(source: dict[str, object]) -> str:
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(str(source["title"]))
        + "</title></head><body>\n"
        + f"<h1>{escape(str(source['title']))}</h1>\n"
        + f"<p>source_id: {escape(str(source['source_id']))}</p>\n"
        + "</body></html>\n"
    )


def _render_topic_page(topic: dict[str, object], *, site_presentation_mode: str) -> str:
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
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(str(topic["title"]))
        + "</title></head><body>\n"
        + f"<h1>{escape(str(topic['title']))}</h1>\n"
        + (
            "<p class=\"topic-structure\" "
            f"data-structure-type=\"{escape(structure_type)}\">Structure: {escape(structure_type)}</p>\n"
        )
        + parent_link_row
        + section_rows
        + "\n</body></html>\n"
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


def _render_site_new_index(entries: list[tuple[str, str, str, str, str]]) -> str:
    rows = "\n".join(
        (
            "<li>"
            + f"{escape(timestamp or 'unknown')} | {escape(space_name)} | {escape(item_type)} | "
            + f"<a href=\"../spaces/{escape(space_name)}/{escape(item_type)}s/{escape(item_id)}.html\">"
            + escape(title)
            + "</a></li>"
        )
        for timestamp, space_name, item_type, item_id, title in entries
    )
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>New</title></head><body>\n"
        "<h1>New</h1>\n<ul>\n"
        + rows
        + "\n</ul>\n"
        + "</body></html>\n"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text_file(path: Path, content: str, *, incremental: bool) -> None:
    if incremental and path.is_file() and path.read_text() == content:
        return
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
