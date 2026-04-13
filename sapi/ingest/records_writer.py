"""Source acquisition and source-record persistence helpers for ingest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from sapi.contracts.ids import ISO_DATE_RE, RFC3339_UTC_RE
from sapi.contracts.ids import make_claim_id, make_source_id, slugify
from sapi.contracts.semantic_specs import resolve_semantic_invocation_spec
from sapi.ingest.relation_store import write_relation
from sapi.ingest.source_content import resolve_source_title
from sapi.llm.client import LlmClient
from sapi.llm.semantic_executor import (
    DEFAULT_MAX_REPAIR_LOOPS,
    SemanticSpec,
    TraceContext,
    run_semantic_flow,
)

_ALLOWED_ARTICLE_KINDS: set[str] = {
    "empirical",
    "theoretical",
    "review",
    "meta_analysis",
    "editorial",
}
_ALLOWED_CITATION_CONFIDENCE: set[str] = {"unknown", "low", "medium", "high"}
_CLAIM_ID_RE = re.compile(r"^claim-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}$")
_HTML_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_MARKDOWN_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class IngestExtractionPersistResult:
    run_id: str
    semantic_output_path: Path
    claim_paths: list[Path]
    relation_paths: list[Path]
    source_record_path: Path


def run_ingest_extraction_and_persist_canonical(
    *,
    space_root: Path,
    source_id: str,
    run_id: str,
    llm_client: LlmClient,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> IngestExtractionPersistResult:
    """Run ingest_extraction semantic flow and persist canonical claim/relation writes."""
    repo_root = Path(__file__).resolve().parents[2]
    resolved = resolve_semantic_invocation_spec(
        "ingest_extraction",
        repo_root=repo_root,
        path_tokens={
            "space_root": space_root,
            "run_id": run_id,
        },
    )
    semantic_output, _ = run_semantic_flow(
        spec=_to_runtime_spec(resolved),
        llm_client=llm_client,
        max_repair_loops=max_repair_loops,
        trace_ctx=trace_ctx,
    )

    claims = semantic_output.get("claims")
    if not isinstance(claims, list):
        raise ValueError("ingest_extraction semantic output requires `claims` as an array.")
    relations = semantic_output.get("relations")
    if not isinstance(relations, list):
        raise ValueError("ingest_extraction semantic output requires `relations` as an array.")

    claim_paths, claim_ref_map = _write_claim_records(
        space_root=space_root,
        source_id=source_id,
        claims=claims,
    )
    relation_paths = _write_relation_records(
        space_root=space_root,
        relations=relations,
        claim_ref_map=claim_ref_map,
    )
    source_record_path = _update_source_record_with_ingest_extraction_fields(
        space_root=space_root,
        source_id=source_id,
        semantic_output=semantic_output,
    )

    return IngestExtractionPersistResult(
        run_id=run_id,
        semantic_output_path=resolved.output_json_path,
        claim_paths=claim_paths,
        relation_paths=relation_paths,
        source_record_path=source_record_path,
    )


def _to_runtime_spec(resolved: Any) -> SemanticSpec:
    return SemanticSpec(
        flow_key=resolved.flow_key,
        version=resolved.version,
        schema_path=resolved.schema_path,
        output_json_path=resolved.output_json_path,
        context_paths=resolved.context_paths,
        spec_path=resolved.spec_path,
    )


def _write_claim_records(
    *,
    space_root: Path,
    source_id: str,
    claims: list[Any],
) -> tuple[list[Path], dict[str, str]]:
    claim_paths: list[Path] = []
    claim_ref_map: dict[str, str] = {}

    for index, raw_claim in enumerate(claims):
        claim_payload, claim_id, claim_refs = _normalize_claim_payload(
            raw_claim=raw_claim,
            source_id=source_id,
            index=index,
        )
        claim_path = space_root / "claims" / f"{claim_id}.json"
        claim_path.parent.mkdir(parents=True, exist_ok=True)
        claim_path.write_text(json.dumps(claim_payload, indent=2, sort_keys=True) + "\n")
        claim_paths.append(claim_path)

        for claim_ref in claim_refs:
            claim_ref_map[claim_ref] = claim_id
        claim_ref_map[claim_id] = claim_id

    return claim_paths, claim_ref_map


def _normalize_claim_payload(
    *,
    raw_claim: Any,
    source_id: str,
    index: int,
) -> tuple[dict[str, Any], str, set[str]]:
    if isinstance(raw_claim, str):
        claim_text = _require_non_empty(raw_claim, "claims[].text")
        raw_claim_dict: dict[str, Any] = {}
    elif isinstance(raw_claim, dict):
        raw_claim_dict = dict(raw_claim)
        claim_text = _resolve_claim_text(raw_claim_dict)
    else:
        raise TypeError("claims[] items must be strings or objects.")

    provided_claim_id = raw_claim_dict.get("claim_id")
    claim_id = _resolve_claim_id(
        provided_claim_id=provided_claim_id,
        claim_text=claim_text,
        source_id=source_id,
        index=index,
    )
    evidence_excerpts = _normalize_evidence_excerpts(raw_claim_dict.get("evidence_excerpts"))
    if not evidence_excerpts:
        evidence_excerpts = _normalize_evidence_excerpts(raw_claim_dict.get("evidence"))

    claim_payload = {
        "schema_version": "claim_record_v1",
        "claim_id": claim_id,
        "source_id": source_id,
        "text": claim_text,
        "evidence_excerpts": evidence_excerpts,
    }

    claim_refs: set[str] = {str(index), f"#{index}"}
    claim_key = raw_claim_dict.get("claim_key")
    if isinstance(claim_key, str) and claim_key.strip():
        claim_refs.add(claim_key.strip())
    if isinstance(provided_claim_id, str) and provided_claim_id.strip():
        claim_refs.add(provided_claim_id.strip())

    return claim_payload, claim_id, claim_refs


def _resolve_claim_text(raw_claim_dict: dict[str, Any]) -> str:
    for key in ("text", "statement", "claim", "content", "summary", "description"):
        value = raw_claim_dict.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for value in raw_claim_dict.values():
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError("claims[] objects must include non-empty `text`, `statement`, or `claim`.")


def _resolve_claim_id(
    *,
    provided_claim_id: Any,
    claim_text: str,
    source_id: str,
    index: int,
) -> str:
    if isinstance(provided_claim_id, str) and provided_claim_id.strip():
        claim_id = provided_claim_id.strip()
        if _CLAIM_ID_RE.fullmatch(claim_id):
            return claim_id

    slug = slugify(claim_text)
    if len(slug) > 80:
        slug = slug[:80].rstrip("-")
    if not slug:
        slug = "claim"
    canonical_payload = json.dumps(
        {
            "source_id": source_id,
            "text": claim_text,
            "position": index,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return make_claim_id(slug=slug, canonical_payload=canonical_payload)


def _normalize_evidence_excerpts(raw_value: Any) -> list[str]:
    if raw_value is None:
        return []
    if not isinstance(raw_value, list):
        raise TypeError("evidence_excerpts/evidence must be arrays when provided.")
    normalized: list[str] = []
    for raw_item in raw_value:
        if isinstance(raw_item, str):
            text = raw_item.strip()
            if text:
                normalized.append(text)
            continue
        if isinstance(raw_item, dict):
            for key in ("excerpt", "quote", "text", "content"):
                excerpt = raw_item.get(key)
                if isinstance(excerpt, str) and excerpt.strip():
                    normalized.append(excerpt.strip())
                    break
            else:
                raise TypeError(
                    "evidence items must be strings or objects with non-empty "
                    "`excerpt`/`quote`/`text`/`content`."
                )
            continue
        raise TypeError(
            "evidence items must be strings or objects with non-empty "
            "`excerpt`/`quote`/`text`/`content`."
        )
    return normalized


def _write_relation_records(
    *,
    space_root: Path,
    relations: list[Any],
    claim_ref_map: dict[str, str],
) -> list[Path]:
    relation_paths: list[Path] = []
    for raw_relation in relations:
        if not isinstance(raw_relation, dict):
            raise TypeError("relations[] items must be JSON objects.")
        try:
            relation_payload = dict(raw_relation)
            relation_payload["relation_type"] = _normalize_relation_type_alias(relation_payload.get("relation_type"))
            relation_payload["src_claim_id"] = _resolve_relation_claim_endpoint(
                relation=relation_payload,
                endpoint_key="src_claim_id",
                endpoint_ref_key="src_claim_ref",
                claim_ref_map=claim_ref_map,
                alternate_keys=("source_claim_id", "source_claim_ref", "source_claim"),
            )
            relation_payload["dst_claim_id"] = _resolve_relation_claim_endpoint(
                relation=relation_payload,
                endpoint_key="dst_claim_id",
                endpoint_ref_key="dst_claim_ref",
                claim_ref_map=claim_ref_map,
                alternate_keys=("target_claim_id", "target_claim_ref", "target_claim"),
            )
            relation_path = write_relation(relation_payload, space_root)
            relation_paths.append(relation_path)
        except (TypeError, ValueError):
            continue
    return relation_paths


def _resolve_relation_claim_endpoint(
    *,
    relation: dict[str, Any],
    endpoint_key: str,
    endpoint_ref_key: str,
    claim_ref_map: dict[str, str],
    alternate_keys: tuple[str, ...] = (),
) -> str:
    candidate_keys = (endpoint_key, endpoint_ref_key, *alternate_keys)
    raw = None
    for candidate_key in candidate_keys:
        candidate_value = relation.get(candidate_key)
        if candidate_value is not None:
            raw = candidate_value
            break
    if not isinstance(raw, str) or not raw.strip():
        key_hint = "`, `".join(candidate_keys)
        raise ValueError(f"relations[] requires one of `{key_hint}`.")
    claim_ref = raw.strip()
    if claim_ref not in claim_ref_map:
        raise ValueError(f"relations[] references unknown claim: {claim_ref}")
    return claim_ref_map[claim_ref]


def _normalize_relation_type_alias(raw: Any) -> Any:
    if not isinstance(raw, str):
        return raw
    normalized = raw.strip()
    alias_map = {
        "supported_by": "supports",
        "support": "supports",
        "implies": "supports",
        "entails": "supports",
        "explains": "supports",
        "because_of": "derived_from",
        "contradicts": "contradictory",
        "contradiction": "contradictory",
        "derivedfrom": "derived_from",
        "derived_from": "derived_from",
        "defines_components": "derived_from",
        "refutes": "falsifies",
    }
    lowered = normalized.lower()
    if lowered in alias_map:
        return alias_map[lowered]
    if lowered in {"supports", "derived_from", "falsifies", "contradictory", "similar"}:
        return lowered
    return "supports"


def _update_source_record_with_ingest_extraction_fields(
    *,
    space_root: Path,
    source_id: str,
    semantic_output: dict[str, Any],
) -> Path:
    source_record_path = space_root / "sources" / "records" / f"{source_id}.json"
    if not source_record_path.is_file():
        raise FileNotFoundError(f"Canonical source record missing for source_id {source_id}.")

    source_record = json.loads(source_record_path.read_text())
    if not isinstance(source_record, dict):
        raise ValueError(f"Source record must be a JSON object: {source_record_path}")

    source_semantic = semantic_output.get("source")
    if not isinstance(source_semantic, dict):
        raise ValueError("ingest_extraction semantic output requires `source` as a JSON object.")
    source_record["source_semantic"] = source_semantic
    source_record["source_date_inference"] = semantic_output.get("source_date_inference")
    source_record["summary"] = semantic_output.get("summary")
    source_record["warnings"] = semantic_output.get("warnings")
    source_record_path.write_text(json.dumps(source_record, indent=2, sort_keys=True) + "\n")
    return source_record_path


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
    article_kind: str | None = None,
    citation_count: int | float | None = None,
    citation_count_as_of: str | None = None,
    citation_count_provider: str | None = None,
    citation_count_confidence: str | None = None,
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
        source_metadata_title=source_input.source_metadata_title,
        in_source_title_line=source_input.in_source_title_line,
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
        article_kind=article_kind,
        citation_count=citation_count,
        citation_count_as_of=citation_count_as_of,
        citation_count_provider=citation_count_provider,
        citation_count_confidence=citation_count_confidence,
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
    source_metadata_title: str | None
    in_source_title_line: str | None


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
        source_metadata_title, in_source_title_line = _extract_title_hints(
            body=body,
            media_type=media_type,
            locator=raw_input,
        )
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
            source_metadata_title=source_metadata_title,
            in_source_title_line=in_source_title_line,
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
    source_metadata_title, in_source_title_line = _extract_title_hints(
        body=body,
        media_type=media_type,
        locator=file_locator,
    )
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
        source_metadata_title=source_metadata_title,
        in_source_title_line=in_source_title_line,
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
    article_kind: str | None,
    citation_count: int | float | None,
    citation_count_as_of: str | None,
    citation_count_provider: str | None,
    citation_count_confidence: str | None,
) -> dict[str, Any]:
    metadata_extensions = _resolve_source_metadata_extensions(
        article_kind=article_kind,
        citation_count=citation_count,
        citation_count_as_of=citation_count_as_of,
        citation_count_provider=citation_count_provider,
        citation_count_confidence=citation_count_confidence,
    )

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
        **metadata_extensions,
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


def _extract_title_hints(
    *,
    body: bytes,
    media_type: str,
    locator: str,
) -> tuple[str | None, str | None]:
    normalized_media_type = media_type.strip().lower()
    suffix = Path(locator).suffix.lower()
    is_text_like = (
        normalized_media_type.startswith("text/")
        or normalized_media_type in {"application/json", "application/xml"}
        or suffix in {".md", ".markdown", ".txt", ".html", ".htm"}
    )
    if not is_text_like:
        return None, None

    decoded = body.decode("utf-8", errors="ignore")
    if not decoded.strip():
        return None, None

    source_metadata_title = _extract_metadata_title(decoded, suffix=suffix, media_type=normalized_media_type)
    in_source_title_line = _extract_in_source_title_line(decoded)
    return source_metadata_title, in_source_title_line


def _extract_metadata_title(raw_text: str, *, suffix: str, media_type: str) -> str | None:
    is_html = suffix in {".html", ".htm"} or media_type in {"text/html", "application/xhtml+xml"}
    if not is_html:
        return None
    match = _HTML_TITLE_RE.search(raw_text)
    if match is None:
        return None
    return _normalize_candidate_title(match.group(1))


def _extract_in_source_title_line(raw_text: str) -> str | None:
    first_plausible_line: str | None = None
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        h1_match = _MARKDOWN_H1_RE.match(line)
        if h1_match is not None:
            return _normalize_candidate_title(h1_match.group(1))
        if first_plausible_line is None and _is_plausible_title_line(line):
            first_plausible_line = line
    if first_plausible_line is None:
        return None
    return _normalize_candidate_title(first_plausible_line)


def _is_plausible_title_line(line: str) -> bool:
    if line.startswith(("#", "-", "*", ">", "```")):
        return False
    if "<" in line and ">" in line:
        return False
    if len(line) > 200:
        return False
    return True


def _normalize_candidate_title(raw_title: str) -> str | None:
    normalized = _SPACE_RE.sub(" ", raw_title).strip()
    if not normalized:
        return None
    return normalized[:200]


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


def _resolve_source_metadata_extensions(
    *,
    article_kind: str | None,
    citation_count: int | float | None,
    citation_count_as_of: str | None,
    citation_count_provider: str | None,
    citation_count_confidence: str | None,
) -> dict[str, Any]:
    return {
        "article_kind": _normalize_article_kind(article_kind),
        "citation_count": _normalize_citation_count(citation_count),
        "citation_count_as_of": _normalize_citation_count_as_of(citation_count_as_of),
        "citation_count_provider": _normalize_citation_count_provider(citation_count_provider),
        "citation_count_confidence": _normalize_citation_count_confidence(citation_count_confidence),
    }


def _normalize_article_kind(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = _require_non_empty(raw, "article_kind")
    if value not in _ALLOWED_ARTICLE_KINDS:
        raise ValueError(
            "article_kind must be one of: " + ", ".join(sorted(_ALLOWED_ARTICLE_KINDS))
        )
    return value


def _normalize_citation_count(raw: int | float | None) -> int | float | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise ValueError("citation_count must be a number or null.")
    if not isinstance(raw, (int, float)):
        raise ValueError("citation_count must be a number or null.")
    if raw < 0:
        raise ValueError("citation_count must be >= 0 when provided.")
    return raw


def _normalize_citation_count_as_of(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = _require_non_empty(raw, "citation_count_as_of")
    if ISO_DATE_RE.fullmatch(value) or RFC3339_UTC_RE.fullmatch(value):
        return value
    raise ValueError("citation_count_as_of must be ISO date or RFC3339 UTC timestamp.")


def _normalize_citation_count_provider(raw: str | None) -> str:
    if raw is None:
        return "unknown"
    return _require_non_empty(raw, "citation_count_provider")


def _normalize_citation_count_confidence(raw: str | None) -> str:
    if raw is None:
        return "unknown"
    value = _require_non_empty(raw, "citation_count_confidence")
    if value not in _ALLOWED_CITATION_CONFIDENCE:
        raise ValueError(
            "citation_count_confidence must be one of: "
            + ", ".join(sorted(_ALLOWED_CITATION_CONFIDENCE))
        )
    return value
