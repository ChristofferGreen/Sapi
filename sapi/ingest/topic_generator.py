"""Topic-generation semantic flow execution and canonical topic persistence."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from sapi.contracts.ids import make_topic_id, slugify
from sapi.contracts.schemas import load_json_schema
from sapi.contracts.semantic_specs import resolve_semantic_invocation_spec
from sapi.llm.client import LlmClient, SemanticRepairContext
from sapi.llm.semantic_executor import (
    DEFAULT_MAX_REPAIR_LOOPS,
    SemanticSpec,
    TraceContext,
    run_semantic_flow,
)


@dataclass(frozen=True)
class TopicCanonicalWrite:
    topic_id: str
    topic_path: Path
    source_ids: list[str]
    claim_ids: list[str]


@dataclass(frozen=True)
class TopicGenerationPersistResult:
    run_id: str
    source_id: str
    semantic_output_path: Path
    topics: list[TopicCanonicalWrite]

    @property
    def topic_ids(self) -> list[str]:
        return [row.topic_id for row in self.topics]

    @property
    def topic_paths(self) -> list[Path]:
        return [row.topic_path for row in self.topics]


def derive_default_topic_id_for_source(*, space_root: Path, source_id: str) -> str:
    """Derive a deterministic topic id from a source record (legacy helper)."""
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
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> TopicGenerationPersistResult:
    """Run topic_generation semantic flow and persist 0..n canonical topic JSON files."""
    repo_root = Path(__file__).resolve().parents[2]
    resolved = resolve_semantic_invocation_spec(
        "topic_generation",
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

    try:
        normalized_topics = _normalize_topic_batch(
            raw_topics=semantic_output.get("topics"),
            source_id=source_id,
        )
    except ValueError as exc:
        semantic_output, _ = run_semantic_flow(
            spec=_to_runtime_spec(resolved),
            llm_client=llm_client,
            max_repair_loops=max_repair_loops,
            initial_repair_context=_build_topic_normalization_repair_context(
                semantic_output=semantic_output,
                source_id=source_id,
                schema_path=resolved.schema_path,
                normalization_error=exc,
            ),
            trace_ctx=trace_ctx,
        )
        try:
            normalized_topics = _normalize_topic_batch(
                raw_topics=semantic_output.get("topics"),
                source_id=source_id,
            )
        except ValueError as repaired_exc:
            raise ValueError(
                "topic_generation returned invalid topic JSON after repair "
                f"(section/body contract violation): {repaired_exc}"
            ) from repaired_exc
    topic_writes: list[TopicCanonicalWrite] = []
    for topic_payload in normalized_topics:
        topic_id = str(topic_payload["topic_id"])
        topic_path = space_root / "topics" / f"{topic_id}.json"
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        topic_path.write_text(json.dumps(topic_payload, indent=2, sort_keys=True) + "\n")
        topic_writes.append(
            TopicCanonicalWrite(
                topic_id=topic_id,
                topic_path=topic_path,
                source_ids=list(topic_payload["source_ids"]),
                claim_ids=list(topic_payload["claim_ids"]),
            )
        )

    return TopicGenerationPersistResult(
        run_id=run_id,
        source_id=source_id,
        semantic_output_path=resolved.output_json_path,
        topics=topic_writes,
    )


def _build_topic_normalization_repair_context(
    *,
    semantic_output: dict[str, Any],
    source_id: str,
    schema_path: Path,
    normalization_error: ValueError,
) -> SemanticRepairContext:
    validation_errors = _derive_topic_contract_validation_errors(
        raw_topics=semantic_output.get("topics"),
        source_id=source_id,
    )
    if not validation_errors:
        validation_errors.append(
            {
                "path": "/topics",
                "message": (
                    "Section/body contract violation: topic output must include at least one "
                    "section with a non-empty `body` (or alias `content`/`summary`)."
                ),
                "validator": "section_body_contract",
                "validator_value": "requires_non_empty_section_body",
            }
        )
    validation_errors.append(
        {
            "path": "/topics",
            "message": f"Normalization error: {normalization_error}",
            "validator": "post_schema_contract",
            "validator_value": "topic_generation_normalizer",
        }
    )
    return SemanticRepairContext(
        previous_invalid_json=json.dumps(semantic_output, indent=2, sort_keys=True),
        validation_errors=validation_errors,
        schema=load_json_schema(schema_path),
        require_complete_replacement_json=True,
    )


def _derive_topic_contract_validation_errors(*, raw_topics: Any, source_id: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not isinstance(raw_topics, list):
        return errors
    for topic_index, raw_topic in enumerate(raw_topics):
        if not isinstance(raw_topic, dict):
            continue
        sections = raw_topic.get("sections")
        if not isinstance(sections, list):
            errors.append(
                {
                    "path": f"/topics/{topic_index}/sections",
                    "message": "topics[*].sections must be an array.",
                    "validator": "type",
                    "validator_value": "array",
                }
            )
            continue
        non_empty_section_count = 0
        for section_index, section in enumerate(sections):
            if not isinstance(section, dict):
                errors.append(
                    {
                        "path": f"/topics/{topic_index}/sections/{section_index}",
                        "message": "Each section must be an object.",
                        "validator": "type",
                        "validator_value": "object",
                    }
                )
                continue
            body_candidate = section.get("body")
            content_candidate = section.get("content")
            summary_candidate = section.get("summary")
            has_text = any(
                isinstance(candidate, str) and candidate.strip()
                for candidate in (body_candidate, content_candidate, summary_candidate)
            )
            if has_text:
                non_empty_section_count += 1
                continue
            errors.append(
                {
                    "path": f"/topics/{topic_index}/sections/{section_index}",
                    "message": (
                        "Section/body contract violation: each section must include non-empty "
                        "`body` (or alias `content`/`summary`)."
                    ),
                    "validator": "section_body_contract",
                    "validator_value": "non_empty_body",
                }
            )
        if non_empty_section_count == 0:
            errors.append(
                {
                    "path": f"/topics/{topic_index}/sections",
                    "message": (
                        "Section/body contract violation: each topic requires at least one "
                        "section with non-empty body text."
                    ),
                    "validator": "section_body_contract",
                    "validator_value": "at_least_one_non_empty_body",
                }
            )
        source_ids = raw_topic.get("source_ids")
        if isinstance(source_ids, list):
            normalized_source_ids = [
                value.strip()
                for value in source_ids
                if isinstance(value, str) and value.strip()
            ]
            if source_id not in normalized_source_ids:
                errors.append(
                    {
                        "path": f"/topics/{topic_index}/source_ids",
                        "message": "topics[*].source_ids must include the ingested source_id.",
                        "validator": "contains",
                        "validator_value": source_id,
                    }
                )
            if len(set(normalized_source_ids)) < 2:
                errors.append(
                    {
                        "path": f"/topics/{topic_index}/source_ids",
                        "message": (
                            "topics[*].source_ids must include at least two distinct source IDs, "
                            "or emit topics=[] when no cross-source concept exists."
                        ),
                        "validator": "minItems",
                        "validator_value": 2,
                    }
                )
    return errors


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


def _normalize_topic_batch(*, raw_topics: Any, source_id: str) -> list[dict[str, Any]]:
    if not isinstance(raw_topics, list):
        raise ValueError("topic_generation semantic output requires `topics` as an array.")
    by_topic_id: dict[str, dict[str, Any]] = {}
    for raw_topic in raw_topics:
        topic_payload = _normalize_topic_payload(raw_topic=raw_topic, source_id=source_id)
        topic_id = str(topic_payload["topic_id"])
        if topic_id not in by_topic_id:
            by_topic_id[topic_id] = topic_payload
            continue
        by_topic_id[topic_id] = _merge_topic_payload(
            base=by_topic_id[topic_id],
            incoming=topic_payload,
        )
    return list(by_topic_id.values())


def _normalize_topic_payload(*, raw_topic: Any, source_id: str) -> dict[str, Any]:
    if not isinstance(raw_topic, dict):
        raise ValueError("topic_generation semantic output topics entries must be objects.")
    title = _require_non_empty_string(raw_topic.get("title"), field_name="title")
    structure_type = _require_non_empty_string(raw_topic.get("structure_type"), field_name="structure_type")
    sections = _normalize_topic_sections(raw_topic.get("sections"))
    claim_ids = _require_string_list(raw_topic.get("claim_ids"), field_name="claim_ids")
    source_ids = _require_string_list(raw_topic.get("source_ids"), field_name="source_ids")
    source_ids = _dedupe_ordered_strings(source_ids)
    if source_id not in source_ids:
        raise ValueError(
            "topic_generation semantic output topics[*].source_ids must include ingested source_id."
        )
    if len(source_ids) < 2:
        raise ValueError(
            "topic_generation semantic output topics[*].source_ids must include at least two "
            "distinct sources; emit `topics=[]` when no cross-source concepts are available."
        )
    claim_ids = _dedupe_ordered_strings(claim_ids)
    raw_topic_id = raw_topic.get("topic_id")
    topic_id = (
        _require_non_empty_string(raw_topic_id, field_name="topic_id")
        if raw_topic_id is not None
        else _derive_topic_id(title=title, source_ids=source_ids)
    )
    return {
        "topic_id": topic_id,
        "title": title,
        "structure_type": structure_type,
        "sections": sections,
        "claim_ids": claim_ids,
        "source_ids": source_ids,
    }


def _merge_topic_payload(*, base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged_claim_ids = _dedupe_ordered_strings(
        [*base["claim_ids"], *incoming["claim_ids"]],
    )
    merged_source_ids = _dedupe_ordered_strings(
        [*base["source_ids"], *incoming["source_ids"]],
    )
    merged_sections = _dedupe_sections([*base["sections"], *incoming["sections"]])
    return {
        "topic_id": base["topic_id"],
        "title": base["title"],
        "structure_type": base["structure_type"],
        "sections": merged_sections,
        "claim_ids": merged_claim_ids,
        "source_ids": merged_source_ids,
    }


def _derive_topic_id(*, title: str, source_ids: list[str]) -> str:
    topic_slug = slugify(title)
    canonical_payload = json.dumps(
        {
            "title": title.strip(),
            "source_ids": sorted(source_ids),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return make_topic_id(slug=topic_slug, canonical_payload=canonical_payload)


def _require_non_empty_string(raw: Any, *, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"topic_generation semantic output requires non-empty `{field_name}`.")
    return raw.strip()


def _require_string_list(raw: Any, *, field_name: str) -> list[str]:
    if not isinstance(raw, list):
        raise ValueError(f"topic_generation semantic output requires `{field_name}` as an array.")
    normalized: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} entries must be non-empty strings.")
        normalized.append(item.strip())
    return normalized


def _dedupe_ordered_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _dedupe_sections(values: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    ordered: list[dict[str, str]] = []
    for row in values:
        key = (row["heading"], row["body"])
        if key in seen:
            continue
        seen.add(key)
        ordered.append(row)
    return ordered


def _normalize_topic_sections(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise ValueError("topic_generation semantic output requires `sections` as an array.")
    normalized: list[dict[str, str]] = []
    for index, section in enumerate(raw, start=1):
        if not isinstance(section, dict):
            continue
        heading_raw = section.get("heading")
        if not isinstance(heading_raw, str) or not heading_raw.strip():
            heading_raw = section.get("title")
        if not isinstance(heading_raw, str) or not heading_raw.strip():
            heading_raw = section.get("name")
        heading = (
            heading_raw.strip()
            if isinstance(heading_raw, str) and heading_raw.strip()
            else f"Section {index}"
        )
        body_raw = section.get("body")
        if not isinstance(body_raw, str) or not body_raw.strip():
            alt = section.get("content")
            if isinstance(alt, str) and alt.strip():
                body_raw = alt
        if not isinstance(body_raw, str) or not body_raw.strip():
            alt = section.get("summary")
            if isinstance(alt, str) and alt.strip():
                body_raw = alt
        if not isinstance(body_raw, str) or not body_raw.strip():
            continue
        normalized.append({"heading": heading, "body": body_raw.strip()})
    if not normalized:
        raise ValueError("topic_generation semantic output requires at least one section with non-empty body.")
    return normalized
