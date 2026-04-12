"""Deterministic site-builder and site-root New-index projection functions."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html import escape
from pathlib import Path

from sapi.build.projection import SpaceProjection, load_space_projection


@dataclass(frozen=True)
class BuildResult:
    """Summary of one deterministic space build invocation."""

    space_name: str
    output_root: Path
    generated_files: list[Path]
    content_hashes: dict[str, str]


def build_space_site(space_root: Path, *, incremental: bool) -> BuildResult:
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
        _write_topic_pages(output_root=output_root, projection=projection, incremental=incremental)
    )

    index_path = output_root / "index.html"
    _write_text_file(
        index_path,
        _render_space_index(space_name=space_name, projection=projection),
        incremental=incremental,
    )
    generated_files.append(index_path)

    content_hashes = {str(path.relative_to(output_root)): _sha256(path) for path in sorted(generated_files)}
    return BuildResult(
        space_name=space_name,
        output_root=output_root,
        generated_files=sorted(generated_files),
        content_hashes=content_hashes,
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
) -> list[Path]:
    topics_dir = output_root / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for topic in sorted(projection.topics, key=lambda item: item["topic_id"]):
        topic_path = topics_dir / f"{topic['topic_id']}.html"
        _write_text_file(topic_path, _render_topic_page(topic), incremental=incremental)
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


def _render_topic_page(topic: dict[str, object]) -> str:
    sections = topic["sections"]
    assert isinstance(sections, list)
    section_rows = "\n".join(
        f"<section><h2>{escape(str(section['heading']))}</h2><p>{escape(str(section['body']))}</p></section>"
        for section in sections
    )
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>"
        + escape(str(topic["title"]))
        + "</title></head><body>\n"
        + f"<h1>{escape(str(topic['title']))}</h1>\n"
        + section_rows
        + "\n</body></html>\n"
    )


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
