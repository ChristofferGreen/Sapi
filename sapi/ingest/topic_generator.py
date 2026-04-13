"""Topic-generation semantic flow execution and canonical topic persistence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from sapi.contracts.ids import make_topic_id, slugify
from sapi.contracts.semantic_specs import resolve_semantic_invocation_spec
from sapi.llm.client import LlmClient
from sapi.llm.semantic_executor import (
    DEFAULT_MAX_REPAIR_LOOPS,
    SemanticSpec,
    TraceContext,
    run_semantic_flow,
)


@dataclass(frozen=True)
class TopicGenerationPersistResult:
    run_id: str
    topic_id: str
    topic_path: Path
    source_id: str
    claim_ids: list[str]


def derive_default_topic_id_for_source(*, space_root: Path, source_id: str) -> str:
    source_record = _load_source_record(space_root=space_root, source_id=source_id)
    title = source_record.get("title")
    topic_slug_source = title if isinstance(title, str) and title.strip() else source_id
    topic_slug = slugify(topic_slug_source)
    canonical_payload = json.dumps(
        {
            "source_id": source_id,
            "topic_slug_source": topic_slug_source,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return make_topic_id(slug=topic_slug, canonical_payload=canonical_payload)


def run_topic_generation_and_persist_canonical(
    *,
    space_root: Path,
    source_id: str,
    run_id: str,
    llm_client: LlmClient,
    topic_id: str | None = None,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> TopicGenerationPersistResult:
    """Run topic_generation semantic flow and persist canonical topic JSON."""
    canonical_topic_id = topic_id or derive_default_topic_id_for_source(
        space_root=space_root,
        source_id=source_id,
    )
    repo_root = Path(__file__).resolve().parents[2]
    resolved = resolve_semantic_invocation_spec(
        "topic_generation",
        repo_root=repo_root,
        path_tokens={
            "space_root": space_root,
            "topic_id": canonical_topic_id,
        },
    )
    semantic_output, _ = run_semantic_flow(
        spec=_to_runtime_spec(resolved),
        llm_client=llm_client,
        max_repair_loops=max_repair_loops,
        trace_ctx=trace_ctx,
    )

    generated_topic_id = semantic_output.get("topic_id")
    if not isinstance(generated_topic_id, str) or not generated_topic_id.strip():
        raise ValueError("topic_generation semantic output requires non-empty `topic_id`.")
    if generated_topic_id.strip() != canonical_topic_id:
        raise ValueError(
            "topic_generation semantic output topic_id must match canonical output path topic_id."
        )

    claim_ids = _require_string_list(semantic_output.get("claim_ids"), field_name="claim_ids")
    source_ids = _require_string_list(semantic_output.get("source_ids"), field_name="source_ids")
    if source_id not in source_ids:
        raise ValueError("topic_generation semantic output source_ids must include source_id.")
    title = semantic_output.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("topic_generation semantic output requires non-empty `title`.")
    structure_type = semantic_output.get("structure_type")
    if not isinstance(structure_type, str) or not structure_type.strip():
        raise ValueError("topic_generation semantic output requires non-empty `structure_type`.")
    semantic_output["sections"] = _normalize_topic_sections(semantic_output.get("sections"))
    semantic_output["title"] = title.strip()
    semantic_output["structure_type"] = structure_type.strip()
    resolved.output_json_path.write_text(json.dumps(semantic_output, indent=2, sort_keys=True) + "\n")

    return TopicGenerationPersistResult(
        run_id=run_id,
        topic_id=canonical_topic_id,
        topic_path=resolved.output_json_path,
        source_id=source_id,
        claim_ids=claim_ids,
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


def _load_source_record(*, space_root: Path, source_id: str) -> dict[str, Any]:
    source_record_path = space_root / "sources" / "records" / f"{source_id}.json"
    if not source_record_path.is_file():
        raise FileNotFoundError(f"Canonical source record missing for source_id {source_id}.")
    payload = json.loads(source_record_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Source record must contain a JSON object: {source_record_path}")
    return payload


def _require_string_list(raw: Any, *, field_name: str) -> list[str]:
    if not isinstance(raw, list):
        raise ValueError(f"topic_generation semantic output requires `{field_name}` as an array.")
    normalized: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings.")
        normalized.append(item.strip())
    return normalized


def _normalize_topic_sections(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise ValueError("topic_generation semantic output requires `sections` as an array.")
    normalized: list[dict[str, str]] = []
    for index, section in enumerate(raw, start=1):
        if not isinstance(section, dict):
            continue
        heading_raw = section.get("heading")
        heading = heading_raw.strip() if isinstance(heading_raw, str) and heading_raw.strip() else f"Section {index}"
        body_raw = section.get("body")
        if not isinstance(body_raw, str) or not body_raw.strip():
            alt = section.get("content")
            if isinstance(alt, str) and alt.strip():
                body_raw = alt
        if not isinstance(body_raw, str) or not body_raw.strip():
            continue
        normalized.append({"heading": heading, "body": body_raw.strip()})
    if not normalized:
        raise ValueError("topic_generation semantic output requires at least one section with non-empty body.")
    return normalized
