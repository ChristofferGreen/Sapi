"""Deterministic query artifact assembly helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
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
    answer = str(query_payload["answer"])
    files = {
        "diagram.mmd": (
            "flowchart TD\n"
            "  A[Question] --> B[Answer]\n"
            f"  B --> C[Claims Used: {len(claim_ids)}]\n"
            f"  B --> D[Summary: {answer}]\n"
        ),
        "diagram.svg": (
            "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"640\" height=\"160\">"
            "<rect width=\"100%\" height=\"100%\" fill=\"#f5f5f5\"/>"
            f"<text x=\"20\" y=\"40\">Mermaid placeholder for query {query_payload['query_id']}</text>"
            "</svg>\n"
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
    files = {
        "image-001.png": (
            "PNG_PLACEHOLDER\n"
            f"query_id={query_payload['query_id']}\n"
            f"claims_used={len(claim_ids)}\n"
        )
    }
    artifacts = [
        {
            "mode": "images",
            "file": "image-001.png",
            "title": "Deterministic query visualization",
            "alt_text": "Summary image generated from deterministic query artifacts",
            "claim_ids": claim_ids,
        }
    ]
    return files, artifacts


def _build_slides_artifacts(
    *,
    query_payload: Mapping[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    claim_ids = list(query_payload["claims_used"])
    files = {
        "deck.md": (
            "# Query Deck\n\n"
            f"- query_id: `{query_payload['query_id']}`\n"
            f"- claims_used: `{len(claim_ids)}`\n"
        ),
        "deck.html": (
            "<html><body>"
            f"<h1>Query Deck</h1><p>query_id={query_payload['query_id']}</p>"
            "</body></html>\n"
        ),
        "deck.pdf": (
            "PDF_PLACEHOLDER\n"
            f"query_id={query_payload['query_id']}\n"
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
    files = {
        "report.pdf": (
            "PDF_PLACEHOLDER\n"
            f"query_id={query_payload['query_id']}\n"
            f"answer={query_payload['answer']}\n"
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

