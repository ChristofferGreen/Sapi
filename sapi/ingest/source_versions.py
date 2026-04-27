"""Source revision-family helpers for ingest."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from sapi.contracts.ids import slugify
from sapi.core.display_titles import resolve_display_title
from sapi.core.pipeline_runtime import write_json_with_transaction
from sapi.core.transactions import ArtifactTransaction
from sapi.llm.client import LlmClient
from sapi.llm.semantic_executor import (
    DEFAULT_MAX_REPAIR_LOOPS,
    SemanticSpec,
    TraceContext,
    build_semantic_spec_from_contract,
    run_semantic_flow,
)


_SOURCE_ID_RE = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12,}$")
_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class SourceRevisionCandidate:
    source_id: str
    score: float
    reasons: tuple[str, ...]
    record: dict[str, Any]


@dataclass(frozen=True)
class SourceRevisionDetectionResult:
    payload: dict[str, Any]
    attempt_count: int
    semantic_output_path: Path


@dataclass(frozen=True)
class SourceRevisionLinkResult:
    source_family_id: str
    latest_source_id: str
    manifest_path: Path
    source_record_paths: tuple[Path, ...]
    revision_count: int


def validate_explicit_revision_target(*, space_root: Path, revises_source_id: str) -> None:
    """Fail fast when an explicit revision target is not a source in this space."""
    source_id = _normalize_source_id(revises_source_id, field_name="revises_source_id")
    _load_source_record(space_root=space_root, source_id=source_id)


def select_source_revision_candidates(
    *,
    space_root: Path,
    new_source_id: str,
    limit: int = 8,
) -> list[SourceRevisionCandidate]:
    """Return a deterministic shortlist for the LLM prompt; never decide revisions."""
    if limit <= 0:
        raise ValueError("limit must be positive.")
    new_record = _load_source_record(space_root=space_root, source_id=new_source_id)
    candidates: list[SourceRevisionCandidate] = []
    for record_path in sorted((space_root / "sources" / "records").glob("source-*.json")):
        record = _load_json_object(record_path)
        candidate_id = str(record.get("source_id") or record_path.stem)
        if candidate_id == new_source_id:
            continue
        score, reasons = _score_revision_candidate(new_record=new_record, candidate_record=record)
        if score <= 0:
            continue
        candidates.append(
            SourceRevisionCandidate(
                source_id=candidate_id,
                score=score,
                reasons=tuple(reasons),
                record=record,
            )
        )
    return sorted(candidates, key=lambda item: (-item.score, item.source_id))[:limit]


def build_source_revision_detection_context(
    *,
    space_root: Path,
    new_source_id: str,
    candidates: list[SourceRevisionCandidate],
) -> dict[str, Any]:
    """Build live LLM task context for source revision detection."""
    new_record = _load_source_record(space_root=space_root, source_id=new_source_id)
    return {
        "new_source": _source_context_summary(space_root=space_root, record=new_record),
        "candidate_sources": [
            {
                **_source_context_summary(space_root=space_root, record=candidate.record),
                "candidate_score": candidate.score,
                "candidate_reasons": list(candidate.reasons),
            }
            for candidate in candidates
        ],
        "revision_policy": {
            "deterministic_candidate_scores_are_prompt_shortlisting_only": True,
            "link_only_when_decision_revision_and_certainty_true": True,
            "uncertain_or_negative_decisions_keep_new_source_independent": True,
            "default_reading_order": [
                "source.md",
                "source_extraction.json",
                "source file only if markdown is insufficient or degraded",
            ],
        },
    }


def run_source_revision_detection(
    *,
    space_root: Path,
    source_id: str,
    run_id: str,
    llm_client: LlmClient,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> SourceRevisionDetectionResult:
    """Run the source_revision_detection semantic flow and return validated JSON."""
    spec = build_semantic_spec_from_contract(
        "source_revision_detection",
        repo_root=Path(__file__).resolve().parents[2],
        path_tokens={
            "space_root": space_root,
            "run_id": run_id,
            "source_id": source_id,
        },
    )
    semantic_output, attempt_count = run_semantic_flow(
        spec=SemanticSpec(
            flow_key=spec.flow_key,
            version=spec.version,
            schema_path=spec.schema_path,
            output_json_path=spec.output_json_path,
            context_paths=spec.context_paths,
            spec_path=spec.spec_path,
        ),
        llm_client=llm_client,
        max_repair_loops=max_repair_loops,
        trace_ctx=trace_ctx,
    )
    return SourceRevisionDetectionResult(
        payload=semantic_output,
        attempt_count=attempt_count,
        semantic_output_path=spec.output_json_path,
    )


def is_certain_revision_decision(
    *,
    payload: dict[str, Any],
    candidate_source_ids: set[str],
) -> bool:
    """Return true only for a certain revision decision targeting a provided candidate."""
    matched_source_id = payload.get("matched_source_id")
    return (
        payload.get("decision") == "revision"
        and payload.get("certainty") is True
        and isinstance(matched_source_id, str)
        and matched_source_id in candidate_source_ids
    )


def apply_source_revision_link(
    *,
    space_root: Path,
    new_source_id: str,
    revises_source_id: str,
    transaction: ArtifactTransaction,
    link_context: dict[str, Any],
) -> SourceRevisionLinkResult:
    """Link a new source into a revision family and write source records/manifest."""
    new_source_id = _normalize_source_id(new_source_id, field_name="new_source_id")
    revises_source_id = _normalize_source_id(revises_source_id, field_name="revises_source_id")
    if new_source_id == revises_source_id:
        raise ValueError("`--revises-source-id` cannot target the source currently being ingested.")

    new_record = _load_source_record(space_root=space_root, source_id=new_source_id)
    predecessor_record = _load_source_record(space_root=space_root, source_id=revises_source_id)
    family_id = _resolve_revision_family_id(
        new_record=new_record,
        predecessor_record=predecessor_record,
    )
    family_records = _load_family_records(
        space_root=space_root,
        source_family_id=family_id,
        required_records=[predecessor_record, new_record],
    )
    updated_records = _revision_order_with_new_latest(
        records=family_records,
        new_source_id=new_source_id,
    )
    for index, record in enumerate(updated_records, start=1):
        source_id = str(record["source_id"])
        previous_id = str(updated_records[index - 2]["source_id"]) if index > 1 else None
        next_id = str(updated_records[index]["source_id"]) if index < len(updated_records) else None
        record["source_family_id"] = family_id
        record["source_revision"] = {
            "source_family_id": family_id,
            "revision_index": index,
            "is_latest": next_id is None,
            "supersedes_source_id": previous_id,
            "superseded_by_source_id": next_id,
        }
        if source_id == new_source_id:
            record["source_revision"]["link_context"] = dict(link_context)
        record_path = _source_record_path(space_root=space_root, source_id=source_id)
        write_json_with_transaction(record_path, record, transaction=transaction)

    manifest_path = _source_revision_manifest_path(space_root=space_root, source_family_id=family_id)
    manifest = _build_revision_manifest(
        source_family_id=family_id,
        records=updated_records,
    )
    write_json_with_transaction(manifest_path, manifest, transaction=transaction)
    return SourceRevisionLinkResult(
        source_family_id=family_id,
        latest_source_id=str(updated_records[-1]["source_id"]),
        manifest_path=manifest_path,
        source_record_paths=tuple(
            _source_record_path(space_root=space_root, source_id=str(record["source_id"]))
            for record in updated_records
        ),
        revision_count=len(updated_records),
    )


def refresh_source_revision_manifest_for_source(
    *,
    space_root: Path,
    source_id: str,
    transaction: ArtifactTransaction,
) -> SourceRevisionLinkResult | None:
    """Rebuild a revision manifest after semantic extraction improves source titles."""
    record = _load_source_record(space_root=space_root, source_id=source_id)
    family_id = _source_family_id(record)
    if not family_id:
        return None
    records = _revision_order_with_new_latest(
        records=_load_family_records(
            space_root=space_root,
            source_family_id=family_id,
            required_records=[record],
        ),
        new_source_id=str(record["source_id"]),
    )
    manifest_path = _source_revision_manifest_path(space_root=space_root, source_family_id=family_id)
    write_json_with_transaction(
        manifest_path,
        _build_revision_manifest(source_family_id=family_id, records=records),
        transaction=transaction,
    )
    return SourceRevisionLinkResult(
        source_family_id=family_id,
        latest_source_id=str(records[-1]["source_id"]),
        manifest_path=manifest_path,
        source_record_paths=tuple(
            _source_record_path(space_root=space_root, source_id=str(item["source_id"]))
            for item in records
        ),
        revision_count=len(records),
    )


def _score_revision_candidate(
    *,
    new_record: dict[str, Any],
    candidate_record: dict[str, Any],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    new_identifier = _normalized_string(new_record.get("canonical_identifier"))
    candidate_identifier = _normalized_string(candidate_record.get("canonical_identifier"))
    if new_identifier and candidate_identifier and new_identifier == candidate_identifier:
        score += 100.0
        reasons.append("matching canonical_identifier")

    new_family_id = _source_family_id(new_record)
    candidate_family_id = _source_family_id(candidate_record)
    if new_family_id and candidate_family_id and new_family_id == candidate_family_id:
        score += 80.0
        reasons.append("matching source_family_id")

    new_title = _display_title(new_record)
    candidate_title = _display_title(candidate_record)
    if new_title.casefold() == candidate_title.casefold():
        score += 30.0
        reasons.append("matching display title")
    overlap = _token_overlap(new_title, candidate_title)
    if overlap > 0:
        score += overlap * 20.0
        reasons.append("title token overlap")

    new_locator_stem = slugify(Path(str(new_record.get("source_locator") or "")).stem)
    candidate_locator_stem = slugify(Path(str(candidate_record.get("source_locator") or "")).stem)
    if new_locator_stem and candidate_locator_stem and new_locator_stem == candidate_locator_stem:
        score += 15.0
        reasons.append("matching locator stem")
    return score, reasons


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(_TOKEN_RE.findall(left.casefold()))
    right_tokens = set(_TOKEN_RE.findall(right.casefold()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _source_context_summary(*, space_root: Path, record: dict[str, Any]) -> dict[str, Any]:
    artifacts = record.get("artifacts")
    artifact_map = artifacts if isinstance(artifacts, dict) else {}
    return {
        "source_id": record.get("source_id"),
        "title": record.get("title"),
        "display_title": _display_title(record),
        "date": record.get("date"),
        "ingested_at": record.get("ingested_at"),
        "source_family_id": _source_family_id(record),
        "canonical_identifier": record.get("canonical_identifier"),
        "source_locator": record.get("source_locator"),
        "analysis_policy": record.get("analysis_policy"),
        "source_extraction": record.get("source_extraction"),
        "source_markdown_path": _absolute_artifact_path(
            space_root=space_root,
            raw_path=artifact_map.get("source_markdown"),
        ),
        "source_extraction_path": _absolute_artifact_path(
            space_root=space_root,
            raw_path=artifact_map.get("source_extraction"),
        ),
        "source_file_path": _absolute_artifact_path(
            space_root=space_root,
            raw_path=artifact_map.get("source_file"),
        ),
    }


def _absolute_artifact_path(*, space_root: Path, raw_path: Any) -> str | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    if path.is_absolute():
        return None
    return str((space_root / path).resolve())


def _revision_order_with_new_latest(
    *,
    records: list[dict[str, Any]],
    new_source_id: str,
) -> list[dict[str, Any]]:
    unique_records: dict[str, dict[str, Any]] = {}
    for record in records:
        source_id = str(record.get("source_id") or "")
        if source_id:
            unique_records[source_id] = dict(record)
    if new_source_id not in unique_records:
        raise ValueError(f"New source record missing from revision family: {new_source_id}")
    new_record = unique_records.pop(new_source_id)
    ordered_existing = sorted(unique_records.values(), key=_revision_sort_key)
    return [*ordered_existing, new_record]


def _revision_sort_key(record: dict[str, Any]) -> tuple[int, str, str]:
    revision = record.get("source_revision")
    revision_index = revision.get("revision_index") if isinstance(revision, dict) else None
    if isinstance(revision_index, int) and revision_index > 0:
        index = revision_index
    else:
        index = 1_000_000
    return (
        index,
        str(record.get("ingested_at") or record.get("date") or ""),
        str(record.get("source_id") or ""),
    )


def _build_revision_manifest(
    *,
    source_family_id: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_source_id = str(records[-1]["source_id"])
    return {
        "schema_version": "source_revision_family_v1",
        "source_family_id": source_family_id,
        "latest_source_id": latest_source_id,
        "revisions": [
            {
                "source_id": record.get("source_id"),
                "title": record.get("title"),
                "display_title": _display_title(record),
                "date": record.get("date"),
                "ingested_at": record.get("ingested_at"),
                "revision_index": _revision_index(record),
                "is_latest": record.get("source_id") == latest_source_id,
                "artifact_sha256": _artifact_sha256(record),
            }
            for record in records
        ],
    }


def _revision_index(record: dict[str, Any]) -> int | None:
    revision = record.get("source_revision")
    if not isinstance(revision, dict):
        return None
    raw = revision.get("revision_index")
    return raw if isinstance(raw, int) else None


def _artifact_sha256(record: dict[str, Any]) -> str | None:
    extraction = record.get("source_extraction")
    if not isinstance(extraction, dict):
        return None
    raw = extraction.get("input_sha256")
    return raw if isinstance(raw, str) and raw.strip() else None


def _load_family_records(
    *,
    space_root: Path,
    source_family_id: str,
    required_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for record in required_records:
        source_id = str(record.get("source_id") or "")
        if source_id:
            records[source_id] = dict(record)
    for record_path in sorted((space_root / "sources" / "records").glob("source-*.json")):
        record = _load_json_object(record_path)
        if _source_family_id(record) != source_family_id:
            continue
        source_id = str(record.get("source_id") or record_path.stem)
        records[source_id] = record
    return sorted(records.values(), key=_revision_sort_key)


def _resolve_revision_family_id(
    *,
    new_record: dict[str, Any],
    predecessor_record: dict[str, Any],
) -> str:
    predecessor_family = _source_family_id(predecessor_record)
    if predecessor_family:
        return predecessor_family
    new_family = _source_family_id(new_record)
    if new_family:
        return new_family
    predecessor_id = str(predecessor_record.get("source_id") or "source")
    return "source-family-" + slugify(predecessor_id.removeprefix("source-"))


def _source_family_id(record: dict[str, Any]) -> str | None:
    raw = record.get("source_family_id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    revision = record.get("source_revision")
    if isinstance(revision, dict):
        raw = revision.get("source_family_id")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _display_title(record: dict[str, Any]) -> str:
    semantic = record.get("source_semantic")
    semantic_display_title = semantic.get("display_title") if isinstance(semantic, dict) else None
    article_title = semantic.get("article_title") if isinstance(semantic, dict) else None
    return resolve_display_title(
        candidates=[
            semantic_display_title,
            article_title,
            record.get("display_title"),
            record.get("title"),
        ],
        fallback=record.get("source_id"),
    )


def _normalized_string(raw: Any) -> str | None:
    if not isinstance(raw, str):
        return None
    normalized = " ".join(raw.split()).casefold()
    return normalized or None


def _load_source_record(*, space_root: Path, source_id: str) -> dict[str, Any]:
    source_id = _normalize_source_id(source_id, field_name="source_id")
    path = _source_record_path(space_root=space_root, source_id=source_id)
    if not path.is_file():
        raise FileNotFoundError(f"Source revision target not found in this space: {source_id}")
    record = _load_json_object(path)
    record_source_id = record.get("source_id")
    if record_source_id != source_id:
        raise ValueError(f"Source record `{path}` has mismatched source_id `{record_source_id}`.")
    return record


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _normalize_source_id(raw: str, *, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field_name} must be a non-empty source id.")
    source_id = raw.strip()
    if not _SOURCE_ID_RE.fullmatch(source_id):
        raise ValueError(f"{field_name} must be a canonical source id.")
    return source_id


def _source_record_path(*, space_root: Path, source_id: str) -> Path:
    return space_root / "sources" / "records" / f"{source_id}.json"


def _source_revision_manifest_path(*, space_root: Path, source_family_id: str) -> Path:
    filename = re.sub(r"[^a-zA-Z0-9._-]+", "-", source_family_id.strip()).strip(".-").lower()
    if not filename:
        raise ValueError("source_family_id produced an empty revision manifest filename.")
    return space_root / "sources" / "versions" / f"{filename}.json"
