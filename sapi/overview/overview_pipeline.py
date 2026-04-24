"""Overview-synthesis context assembly, validation, and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from sapi.contracts.ids import make_overview_id
from sapi.core.site_scope import load_subspaces_metadata


_CANONICAL_SECTION_SPECS: tuple[tuple[str, str], ...] = (
    ("topic_framing", "Topic framing"),
    ("key_themes", "Key themes"),
    ("agreement_and_disagreement", "Agreement and disagreement"),
    ("methods_and_evidence", "Methods and evidence"),
    ("open_questions", "Open questions"),
)


@dataclass(frozen=True)
class OverviewScope:
    overview_id: str
    scope_kind: str
    space_name: str
    scope_name: str
    title: str | None
    parent_space_name: str | None


@dataclass(frozen=True)
class OverviewInputs:
    source_records: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    topics: list[dict[str, Any]]
    source_ids: list[str]
    claim_ids: list[str]
    relation_ids: list[str]
    topic_ids: list[str]
    input_signature: str


def resolve_overview_scope(*, site_path: Path, space_name: str) -> OverviewScope:
    spaces_root = site_path / "spaces"
    for candidate_root in sorted(path for path in spaces_root.iterdir() if path.is_dir()):
        if candidate_root.name == space_name:
            continue
        try:
            metadata = load_subspaces_metadata(space_root=candidate_root)
        except FileNotFoundError:
            continue
        for entry in metadata.subspaces:
            if entry.space_name != space_name:
                continue
            return OverviewScope(
                overview_id=make_overview_id(scope_kind="subspace", scope_name=space_name),
                scope_kind="subspace",
                space_name=space_name,
                scope_name=space_name,
                title=entry.title,
                parent_space_name=candidate_root.name,
            )

    return OverviewScope(
        overview_id=make_overview_id(scope_kind="space", scope_name=space_name),
        scope_kind="space",
        space_name=space_name,
        scope_name=space_name,
        title=None,
        parent_space_name=None,
    )


def load_overview_inputs(*, space_root: Path, scope: OverviewScope) -> OverviewInputs:
    source_records = _load_json_rows(space_root / "sources" / "records", id_key="source_id")
    claims = _load_json_rows(space_root / "claims", id_key="claim_id")
    relations = _load_json_rows(space_root / "relations", id_key="relation_id")
    topics = _load_json_rows(space_root / "topics", id_key="topic_id")
    input_signature = _compute_input_signature(
        space_root=space_root,
        scope=scope,
        source_records=source_records,
        claims=claims,
        relations=relations,
        topics=topics,
    )
    return OverviewInputs(
        source_records=source_records,
        claims=claims,
        relations=relations,
        topics=topics,
        source_ids=[str(row["source_id"]) for row in source_records],
        claim_ids=[str(row["claim_id"]) for row in claims],
        relation_ids=[str(row["relation_id"]) for row in relations],
        topic_ids=[str(row["topic_id"]) for row in topics],
        input_signature=input_signature,
    )


def build_overview_context_payload(
    *,
    scope: OverviewScope,
    inputs: OverviewInputs,
    generated_at: str | None = None,
) -> dict[str, object]:
    warnings = list(_context_warnings(inputs=inputs))
    return {
        "schema_version": "space_overview_context_v1",
        "metadata": {
            "overview_id": scope.overview_id,
            "scope_kind": scope.scope_kind,
            "space_name": scope.space_name,
            "scope_name": scope.scope_name,
            "scope_title": scope.title,
            "parent_space_name": scope.parent_space_name,
        },
        "freshness": {
            "generated_at": generated_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input_signature": inputs.input_signature,
            "source_record_count": len(inputs.source_records),
            "claim_count": len(inputs.claims),
            "relation_count": len(inputs.relations),
            "topic_count": len(inputs.topics),
        },
        "warnings": warnings,
        "source_records": inputs.source_records,
        "claims": inputs.claims,
        "relations": inputs.relations,
        "topics": inputs.topics,
    }


def validate_overview_semantic_payload(
    *,
    payload: dict[str, Any],
    scope: OverviewScope,
    inputs: OverviewInputs,
) -> None:
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("space_overview_generation semantic payload must include object metadata.")

    _require_metadata_match(metadata=metadata, field_name="overview_id", expected=scope.overview_id)
    _require_metadata_match(metadata=metadata, field_name="scope_kind", expected=scope.scope_kind)
    _require_metadata_match(metadata=metadata, field_name="space_name", expected=scope.space_name)
    _require_metadata_match(metadata=metadata, field_name="scope_name", expected=scope.scope_name)

    sections = payload.get("sections")
    if not isinstance(sections, list):
        raise ValueError("space_overview_generation semantic payload sections must be a list.")

    references = payload.get("references")
    if not isinstance(references, dict):
        raise ValueError("space_overview_generation semantic payload references must be an object.")

    reference_source_ids = _normalize_string_list(references.get("source_ids"))
    reference_claim_ids = _normalize_string_list(references.get("claim_ids"))
    citation_anchors = references.get("citation_anchors")
    if not isinstance(citation_anchors, list):
        raise ValueError("references.citation_anchors must be a list.")

    known_source_ids = set(inputs.source_ids)
    known_claim_ids = set(inputs.claim_ids)
    _require_subset(reference_source_ids, known_source_ids, "references.source_ids")
    _require_subset(reference_claim_ids, known_claim_ids, "references.claim_ids")

    anchor_ids: set[str] = set()
    for idx, row in enumerate(citation_anchors):
        if not isinstance(row, dict):
            raise ValueError(f"references.citation_anchors[{idx}] must be an object.")
        anchor_id = _require_non_empty_string(row.get("anchor_id"), f"references.citation_anchors[{idx}].anchor_id")
        if anchor_id in anchor_ids:
            raise ValueError(f"Duplicate citation anchor_id in references.citation_anchors: {anchor_id}")
        anchor_ids.add(anchor_id)

        anchor_source_id = _require_non_empty_string(
            row.get("source_id"),
            f"references.citation_anchors[{idx}].source_id",
        )
        if anchor_source_id not in known_source_ids:
            raise ValueError(
                "references.citation_anchors contains unresolved source_id: "
                f"{anchor_source_id}"
            )
        anchor_claim_ids = _normalize_string_list(row.get("claim_ids"))
        _require_subset(
            anchor_claim_ids,
            known_claim_ids,
            f"references.citation_anchors[{idx}].claim_ids",
        )

    has_source_context = bool(inputs.source_ids)
    has_claim_context = bool(inputs.claim_ids)
    if has_source_context and not reference_source_ids:
        raise ValueError(
            "space_overview_generation semantic payload must cite canonical source_ids when source records exist."
        )
    if has_source_context and not anchor_ids:
        raise ValueError(
            "space_overview_generation semantic payload must include citation anchors when source records exist."
        )
    if has_claim_context and not reference_claim_ids:
        raise ValueError(
            "space_overview_generation semantic payload must cite canonical claim_ids when claims exist."
        )

    expected_section_ids = {section_id for section_id, _heading in _CANONICAL_SECTION_SPECS}
    seen_section_ids: set[str] = set()
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"sections[{idx}] must be an object.")
        section_id = _require_non_empty_string(section.get("section_id"), f"sections[{idx}].section_id")
        if section_id not in expected_section_ids:
            raise ValueError(f"Unknown overview section_id: {section_id}")
        if section_id in seen_section_ids:
            raise ValueError(f"Duplicate overview section_id: {section_id}")
        seen_section_ids.add(section_id)

        _require_subset(
            _normalize_string_list(section.get("source_ids")),
            known_source_ids,
            f"sections[{idx}].source_ids",
        )
        _require_subset(
            _normalize_string_list(section.get("claim_ids")),
            known_claim_ids,
            f"sections[{idx}].claim_ids",
        )
        section_anchor_ids = _normalize_string_list(section.get("citation_anchor_ids"))
        _require_subset(
            section_anchor_ids,
            anchor_ids,
            f"sections[{idx}].citation_anchor_ids",
        )
        if has_source_context and not section_anchor_ids:
            raise ValueError(
                "space_overview_generation semantic payload must provide citation_anchor_ids for each section when source records exist."
            )

    if seen_section_ids != expected_section_ids:
        missing = sorted(expected_section_ids - seen_section_ids)
        extra = sorted(seen_section_ids - expected_section_ids)
        raise ValueError(
            "space_overview_generation semantic payload section coverage mismatch: "
            f"missing={missing}, extra={extra}"
        )


def render_overview_article_markdown(payload: dict[str, Any]) -> str:
    metadata = payload["metadata"]
    freshness = payload["freshness"]
    references = payload["references"]

    title = str(metadata["title"]).strip()
    summary = str(metadata["summary"]).strip()
    lines = [f"# {title}", "", summary, ""]
    for section_id, default_heading in _CANONICAL_SECTION_SPECS:
        section = _section_by_id(payload["sections"], section_id)
        heading = str(section.get("heading") or default_heading).strip()
        body = str(section.get("body") or "").strip()
        lines.extend([f"## {heading}", "", body or "(no content)", ""])
        lines.extend(
            [
                f"Sources: {_render_id_list(section.get('source_ids'))}",
                f"Claims: {_render_id_list(section.get('claim_ids'))}",
                f"Citation anchors: {_render_id_list(section.get('citation_anchor_ids'))}",
                "",
            ]
        )

    lines.extend(["## References", ""])
    citation_anchors = references.get("citation_anchors", [])
    if citation_anchors:
        for row in citation_anchors:
            lines.append(
                "- "
                + str(row["label"]).strip()
                + f" {row['source_id']}"
                + _render_claim_suffix(row.get("claim_ids"))
                + _render_locator_suffix(row.get("locator"))
            )
    else:
        lines.append("- No citation anchors are available for this overview yet.")
    lines.extend(
        [
            "",
            "## Freshness",
            "",
            f"- Generated at: {freshness['generated_at']}",
            f"- Input signature: {freshness['input_signature']}",
            f"- Source records: {freshness['source_record_count']}",
            f"- Claims: {freshness['claim_count']}",
            f"- Relations: {freshness['relation_count']}",
            f"- Topics: {freshness['topic_count']}",
        ]
    )
    warnings = payload.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            if isinstance(warning, str) and warning.strip():
                lines.append(f"- {warning.strip()}")
    return "\n".join(lines).strip() + "\n"


def _context_warnings(*, inputs: OverviewInputs) -> tuple[str, ...]:
    warnings: list[str] = []
    if not inputs.source_records:
        warnings.append("No ingested source records are available for this scope yet.")
    if not inputs.claims:
        warnings.append("No canonical claims are available for this scope yet.")
    if not inputs.topics:
        warnings.append("No canonical topic pages are available for this scope yet.")
    return tuple(warnings)


def _compute_input_signature(
    *,
    space_root: Path,
    scope: OverviewScope,
    source_records: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    topics: list[dict[str, Any]],
) -> str:
    hasher = hashlib.sha256()
    hasher.update(scope.overview_id.encode("utf-8"))
    hasher.update(str(space_root.resolve()).encode("utf-8"))
    for bucket in (source_records, claims, relations, topics):
        for row in bucket:
            hasher.update(json.dumps(row, indent=2, sort_keys=True).encode("utf-8"))
    return "sha256:" + hasher.hexdigest()


def _load_json_rows(root: Path, *, id_key: str) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        parsed = json.loads(path.read_text())
        if not isinstance(parsed, dict):
            raise ValueError(f"Canonical overview input must be a JSON object: {path}")
        raw_id = parsed.get(id_key)
        if not isinstance(raw_id, str) or not raw_id.strip():
            raise ValueError(f"{path} is missing required `{id_key}` string.")
        rows.append(parsed)
    return sorted(rows, key=lambda row: str(row[id_key]))


def _normalize_string_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    values: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            values.append(item.strip())
    return values


def _require_subset(values: list[str], allowed: set[str], field_name: str) -> None:
    missing = sorted(value for value in values if value not in allowed)
    if missing:
        raise ValueError(f"{field_name} contains unresolved canonical IDs: {missing}")


def _require_metadata_match(*, metadata: dict[str, Any], field_name: str, expected: str) -> None:
    actual = _require_non_empty_string(metadata.get(field_name), f"metadata.{field_name}")
    if actual != expected:
        raise ValueError(
            "space_overview_generation semantic payload metadata mismatch: "
            f"{field_name} expected {expected!r}, got {actual!r}."
        )


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _section_by_id(sections: object, section_id: str) -> dict[str, Any]:
    if not isinstance(sections, list):
        raise ValueError("sections must be a list.")
    for row in sections:
        if isinstance(row, dict) and row.get("section_id") == section_id:
            return row
    raise ValueError(f"Missing overview section: {section_id}")


def _render_id_list(raw: object) -> str:
    values = _normalize_string_list(raw)
    return ", ".join(values) if values else "(none)"


def _render_claim_suffix(raw: object) -> str:
    claim_ids = _normalize_string_list(raw)
    if not claim_ids:
        return ""
    return f" ({', '.join(claim_ids)})"


def _render_locator_suffix(raw: object) -> str:
    if not isinstance(raw, str) or not raw.strip():
        return ""
    return f"; locator: {raw.strip()}"
