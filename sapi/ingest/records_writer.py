"""Source acquisition and source-record persistence helpers for ingest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from sapi.contracts.ids import make_source_id, slugify
from sapi.ingest.source_content import resolve_source_title


@dataclass(frozen=True)
class SourceIngestResult:
    source_id: str
    record_path: Path
    artifact_root: Path
    source_artifact_path: Path
    overview_markdown_path: Path


def ingest_source_artifacts_and_record(
    *,
    space_root: Path,
    source_path_or_url: str,
    source_title_override: str | None = None,
    source_media_type_override: str | None = None,
    source_type_override: str | None = None,
    source_family_id: str | None = None,
    canonical_identifier: str | None = None,
    source_date: str | None = None,
) -> SourceIngestResult:
    """Acquire one source input and persist managed artifacts + canonical source record."""
    raw_input = _require_non_empty(source_path_or_url, "source_path_or_url")
    source_input = _load_source_input(
        raw_input=raw_input,
        source_media_type_override=source_media_type_override,
        source_type_override=source_type_override,
    )

    title = resolve_source_title(
        source_title_override=source_title_override,
        source_metadata_title=None,
        in_source_title_line=None,
        source_locator=source_input.locator_for_title,
    )
    source_slug = slugify(title)
    source_id = make_source_id(
        slug=source_slug,
        canonical_payload=source_input.id_payload,
    )

    artifact_root_rel = Path("sources") / "artifacts" / source_id
    artifact_root = space_root / artifact_root_rel
    artifact_root.mkdir(parents=True, exist_ok=True)

    source_artifact_filename = _source_artifact_filename(
        media_type=source_input.media_type,
        locator=source_input.locator_for_filename,
    )
    source_artifact_path = artifact_root / source_artifact_filename
    source_artifact_path.write_bytes(source_input.body)

    overview_markdown_path = artifact_root / "overview.md"
    overview_markdown_path.write_text(_render_overview_markdown(title=title, source_input=source_input))

    record_payload = _build_source_record_payload(
        source_id=source_id,
        title=title,
        source_input=source_input,
        source_artifact_rel=(artifact_root_rel / source_artifact_filename),
        overview_markdown_rel=(artifact_root_rel / "overview.md"),
        source_family_id=source_family_id,
        canonical_identifier=canonical_identifier,
        source_date=source_date,
    )
    record_path = space_root / "sources" / "records" / f"{source_id}.json"
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record_payload, indent=2, sort_keys=True) + "\n")

    return SourceIngestResult(
        source_id=source_id,
        record_path=record_path,
        artifact_root=artifact_root,
        source_artifact_path=source_artifact_path,
        overview_markdown_path=overview_markdown_path,
    )


@dataclass(frozen=True)
class _LoadedSourceInput:
    body: bytes
    locator: str
    locator_for_title: str
    locator_for_filename: str
    source_kind: str
    media_type: str
    source_type: str
    id_payload: bytes


def _load_source_input(
    *,
    raw_input: str,
    source_media_type_override: str | None,
    source_type_override: str | None,
) -> _LoadedSourceInput:
    parsed = urlparse(raw_input)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        body, media_type = _read_url(raw_input)
        media_type = source_media_type_override or media_type or "application/octet-stream"
        source_type = source_type_override or "url"
        id_payload = body + b"\n" + raw_input.encode("utf-8")
        return _LoadedSourceInput(
            body=body,
            locator=raw_input,
            locator_for_title=raw_input,
            locator_for_filename=parsed.path or raw_input,
            source_kind="url",
            media_type=media_type,
            source_type=source_type,
            id_payload=id_payload,
        )

    source_file = Path(raw_input).expanduser()
    if not source_file.is_absolute():
        source_file = (Path.cwd() / source_file).resolve()
    else:
        source_file = source_file.resolve()
    if not source_file.is_file():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    body = source_file.read_bytes()
    media_type = source_media_type_override or _guess_media_type_from_suffix(source_file.suffix)
    source_type = source_type_override or "file"
    file_locator = source_file.name
    id_payload = body + b"\n" + file_locator.encode("utf-8")
    return _LoadedSourceInput(
        body=body,
        locator=file_locator,
        locator_for_title=file_locator,
        locator_for_filename=file_locator,
        source_kind="file",
        media_type=media_type,
        source_type=source_type,
        id_payload=id_payload,
    )


def _build_source_record_payload(
    *,
    source_id: str,
    title: str,
    source_input: _LoadedSourceInput,
    source_artifact_rel: Path,
    overview_markdown_rel: Path,
    source_family_id: str | None,
    canonical_identifier: str | None,
    source_date: str | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": "source_record_v1",
        "source_id": source_id,
        "title": title,
        "date": source_date,
        "ingested_at": _utc_now_rfc3339(),
        "source_locator": source_input.locator,
        "source_kind": source_input.source_kind,
        "source_type": source_input.source_type,
        "source_media_type": source_input.media_type,
        "artifact_root": str(source_artifact_rel.parent),
        "artifacts": {
            "source_file": str(source_artifact_rel),
            "overview_markdown": str(overview_markdown_rel),
            "front_page_image": None,
        },
    }
    if source_family_id is not None:
        record["source_family_id"] = source_family_id
    if canonical_identifier is not None:
        record["canonical_identifier"] = canonical_identifier
    return record


def _read_url(url: str) -> tuple[bytes, str | None]:
    request = Request(url, headers={"User-Agent": "SapiIngest/1.0"})
    with urlopen(request, timeout=30) as response:
        body = response.read()
        header_value = response.headers.get("Content-Type")
    media_type: str | None = None
    if header_value:
        media_type = header_value.split(";", 1)[0].strip().lower()
    return body, media_type


def _source_artifact_filename(*, media_type: str, locator: str) -> str:
    media_type_normalized = media_type.strip().lower()
    if media_type_normalized == "application/pdf":
        return "source.pdf"

    suffix = Path(locator).suffix.lower()
    if suffix == ".pdf":
        return "source.pdf"
    if suffix and _is_safe_suffix(suffix):
        return f"source{suffix}"
    return "source.bin"


def _is_safe_suffix(suffix: str) -> bool:
    if not suffix.startswith("."):
        return False
    body = suffix[1:]
    return bool(body) and len(body) <= 10 and body.isalnum() and body == body.lower()


def _guess_media_type_from_suffix(suffix: str) -> str:
    suffix_normalized = suffix.lower()
    if suffix_normalized == ".pdf":
        return "application/pdf"
    if suffix_normalized in {".md", ".markdown"}:
        return "text/markdown"
    if suffix_normalized in {".txt", ".text"}:
        return "text/plain"
    if suffix_normalized in {".json"}:
        return "application/json"
    return "application/octet-stream"


def _render_overview_markdown(*, title: str, source_input: _LoadedSourceInput) -> str:
    fingerprint = hashlib.sha256(source_input.body).hexdigest()
    return (
        f"# {title}\n\n"
        f"- source_id candidate derived from content fingerprint\n"
        f"- source_kind: {source_input.source_kind}\n"
        f"- source_locator: {source_input.locator}\n"
        f"- media_type: {source_input.media_type}\n"
        f"- content_sha256: {fingerprint}\n"
    )


def _require_non_empty(value: str | None, field_name: str) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _utc_now_rfc3339() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
