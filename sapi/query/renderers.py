"""Deterministic query artifact assembly helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html import escape as escape_html
import re
from typing import Any, Mapping


@dataclass(frozen=True)
class RenderedQueryArtifacts:
    files: dict[str, str]
    manifest: dict[str, Any]


def build_query_artifacts(
    *,
    output_mode: str,
    query_payload: Mapping[str, Any],
    question: str,
) -> RenderedQueryArtifacts | None:
    if output_mode == "markdown":
        return None

    if output_mode == "mermaid":
        files, artifacts = _build_mermaid_artifacts(query_payload=query_payload)
    elif output_mode == "images":
        files, artifacts = _build_images_artifacts(query_payload=query_payload)
    elif output_mode == "slides":
        files, artifacts = _build_slides_artifacts(query_payload=query_payload)
    elif output_mode == "pdf":
        files, artifacts = _build_pdf_artifacts(query_payload=query_payload)
    else:
        raise ValueError(f"Unsupported query output mode for artifact assembly: {output_mode}")

    artifact_hashes = _build_artifact_hashes(files)
    manifest = {
        "query_id": query_payload["query_id"],
        "mode": output_mode,
        "run_id": query_payload["run_id"],
        "question": question,
        "claims_used": list(query_payload["claims_used"]),
        "sources_used": list(query_payload["sources_used"]),
        "artifacts": artifacts,
        "artifact_hashes": artifact_hashes,
    }
    return RenderedQueryArtifacts(files=files, manifest=manifest)


def _build_mermaid_artifacts(
    *,
    query_payload: Mapping[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    claim_ids = list(query_payload["claims_used"])
    source_ids = list(query_payload["sources_used"])
    answer = str(query_payload["answer"])
    summary = _single_line(answer)
    files = {
        "diagram.mmd": (
            "flowchart TD\n"
            f"  A[\"Answer: {_mermaid_label(summary)}\"]\n"
            f"  A --> B[\"Claims used: {len(claim_ids)}\"]\n"
            f"  A --> C[\"Sources used: {len(source_ids)}\"]\n"
        ),
        "diagram.svg": _render_answer_svg(
            title="Query answer",
            answer=answer,
            claims_used=len(claim_ids),
            sources_used=len(source_ids),
        ),
    }
    artifacts = [
        {"mode": "mermaid", "file": "diagram.mmd", "claim_ids": claim_ids},
        {"mode": "mermaid", "file": "diagram.svg", "claim_ids": claim_ids},
    ]
    return files, artifacts


def _build_images_artifacts(
    *,
    query_payload: Mapping[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    claim_ids = list(query_payload["claims_used"])
    source_ids = list(query_payload["sources_used"])
    answer = str(query_payload["answer"])
    files = {
        "image-001.svg": _render_answer_svg(
            title="Query answer image",
            answer=answer,
            claims_used=len(claim_ids),
            sources_used=len(source_ids),
        )
    }
    artifacts = [
        {
            "mode": "images",
            "file": "image-001.svg",
            "title": "Query answer",
            "alt_text": _single_line(answer),
            "mime_type": "image/svg+xml",
            "claim_ids": claim_ids,
        }
    ]
    return files, artifacts


def _build_slides_artifacts(
    *,
    query_payload: Mapping[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    claim_ids = list(query_payload["claims_used"])
    source_ids = list(query_payload["sources_used"])
    answer = str(query_payload["answer"])
    files = {
        "deck.md": (
            "# Query Deck\n\n"
            "## Answer\n\n"
            f"{answer}\n\n"
            "## Evidence Coverage\n\n"
            f"- Claims used: `{len(claim_ids)}`\n"
            f"- Sources used: `{len(source_ids)}`\n"
        ),
        "deck.html": (
            "<!doctype html><html><head><meta charset=\"utf-8\"><title>Query Deck</title></head><body>"
            "<h1>Query Deck</h1>"
            f"<section><h2>Answer</h2><p>{escape_html(answer)}</p></section>"
            "<section><h2>Evidence Coverage</h2>"
            f"<p>Claims used: {len(claim_ids)}; Sources used: {len(source_ids)}</p></section>"
            "</body></html>\n"
        ),
        "deck.pdf": _render_text_pdf(
            title="Query Deck",
            lines=[
                "Query Deck",
                "",
                "Answer",
                answer,
                "",
                f"Claims used: {len(claim_ids)}",
                f"Sources used: {len(source_ids)}",
            ],
        ),
    }
    artifacts = [
        {
            "mode": "slides",
            "deck_md": "deck.md",
            "deck_html": "deck.html",
            "deck_pdf": "deck.pdf",
            "slides": [{"index": 1, "claim_ids": claim_ids}],
        }
    ]
    return files, artifacts


def _build_pdf_artifacts(
    *,
    query_payload: Mapping[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    claim_ids = list(query_payload["claims_used"])
    source_ids = list(query_payload["sources_used"])
    answer = str(query_payload["answer"])
    files = {
        "report.pdf": _render_text_pdf(
            title="Query Report",
            lines=[
                "Query Report",
                "",
                "Answer",
                answer,
                "",
                f"Claims used: {len(claim_ids)}",
                f"Sources used: {len(source_ids)}",
            ],
        )
    }
    artifacts = [
        {
            "mode": "pdf",
            "file": "report.pdf",
            "mime_type": "application/pdf",
            "claim_ids": claim_ids,
        }
    ]
    return files, artifacts


def _build_artifact_hashes(files: Mapping[str, str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative_path in sorted(files.keys()):
        payload = files[relative_path].encode("utf-8")
        hashes[relative_path] = hashlib.sha256(payload).hexdigest()
    return hashes


def _single_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _mermaid_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _wrap_words(text: str, *, line_length: int = 78, max_lines: int | None = None) -> list[str]:
    words = _single_line(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= line_length:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if max_lines is not None and len(lines) >= max_lines:
            break
    if current and (max_lines is None or len(lines) < max_lines):
        lines.append(current)
    return lines or [""]


def _render_answer_svg(
    *,
    title: str,
    answer: str,
    claims_used: int,
    sources_used: int,
) -> str:
    answer_lines = _wrap_words(answer, line_length=84, max_lines=8)
    line_rows = "\n".join(
        f'<text x="32" y="{96 + index * 24}" class="answer">{escape_html(line)}</text>'
        for index, line in enumerate(answer_lines)
    )
    height = max(220, 136 + len(answer_lines) * 24)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}" '
        'viewBox="0 0 960 '
        f'{height}" role="img" aria-label="{escape_html(_single_line(answer))}">\n'
        "  <style>"
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#111827}"
        ".title{font-size:26px;font-weight:700}.meta{font-size:16px;fill:#4b5563}"
        ".answer{font-size:18px}"
        "</style>\n"
        f'  <rect width="960" height="{height}" rx="0" fill="#ffffff"/>\n'
        f'  <text x="32" y="46" class="title">{escape_html(title)}</text>\n'
        f'  <text x="32" y="74" class="meta">Claims used: {claims_used}; Sources used: {sources_used}</text>\n'
        f"{line_rows}\n"
        "</svg>\n"
    )


def _render_text_pdf(*, title: str, lines: list[str]) -> str:
    wrapped_lines: list[str] = []
    for line in lines:
        wrapped_lines.extend(_wrap_words(line, line_length=86) if line else [""])
    text_ops = ["BT", "/F1 11 Tf", "50 760 Td", "14 TL"]
    for index, line in enumerate(wrapped_lines[:48]):
        if index:
            text_ops.append("T*")
        text_ops.append(f"<{_pdf_text_hex(line)}> Tj")
    text_ops.append("ET")
    stream = "\n".join(text_ops) + "\n"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream.encode('ascii'))} >>\nstream\n{stream}endstream",
        f"<< /Title <{_pdf_text_hex(title)}> >>",
    ]
    parts = ["%PDF-1.4\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part.encode("ascii")) for part in parts))
        parts.append(f"{index} 0 obj\n{obj}\nendobj\n")
    xref_offset = sum(len(part.encode("ascii")) for part in parts)
    parts.append(f"xref\n0 {len(objects) + 1}\n")
    parts.append("0000000000 65535 f \n")
    for offset in offsets[1:]:
        parts.append(f"{offset:010d} 00000 n \n")
    parts.append(
        "trailer\n"
        f"<< /Size {len(objects) + 1} /Root 1 0 R /Info 6 0 R >>\n"
        "startxref\n"
        f"{xref_offset}\n"
        "%%EOF\n"
    )
    return "".join(parts)


def _pdf_text_hex(value: str) -> str:
    return "FEFF" + value.encode("utf-16-be", errors="replace").hex().upper()
