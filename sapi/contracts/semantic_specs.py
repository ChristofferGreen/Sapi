"""Generation-spec flow-map resolution and version pinning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping
import warnings


@dataclass(frozen=True)
class SemanticSpecMapEntry:
    flow_key: str
    spec_relpath: str
    schema_relpath: str
    output_json_path_template: str


@dataclass(frozen=True)
class SemanticSpecHeader:
    flow_key: str
    version: str
    schema_path: str
    output_json_path: str
    context_paths: list[str]


@dataclass(frozen=True)
class ResolvedSemanticSpec:
    flow_key: str
    version: str
    spec_path: Path
    schema_path: Path
    output_json_path_template: str
    context_paths: list[str]


@dataclass(frozen=True)
class SkillSemanticContract:
    """Optional semantic contract fields sourced from wrapper skill text."""

    schema_path: str | None = None
    output_json_path: str | None = None
    context_paths: list[str] | None = None


@dataclass(frozen=True)
class SemanticContractPrecedenceResult:
    """Resolved semantic contract with precedence diagnostics."""

    resolved_spec: ResolvedSemanticSpec
    conflict_fields: list[str]
    conflict_details: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ResolvedSemanticInvocationSpec:
    """Canonical semantic invocation envelope with resolved absolute paths."""

    flow_key: str
    version: str
    spec_path: Path
    schema_path: Path
    output_json_path: Path
    context_paths: list[Path]


FLOW_ALIAS_MAP: dict[str, str] = {
    "persona_comment_generation": "comment_section_generation",
}

FLOW_MAP: dict[str, SemanticSpecMapEntry] = {
    "ingest_extraction": SemanticSpecMapEntry(
        flow_key="ingest_extraction",
        spec_relpath="ai_flows/generation_specs/ingest_extraction.v1.md",
        schema_relpath="schemas/ingest_extraction.v1.schema.json",
        output_json_path_template="<space_root>/runs/<run_id>/semantic/ingest_extraction.json",
    ),
    "topic_generation": SemanticSpecMapEntry(
        flow_key="topic_generation",
        spec_relpath="ai_flows/generation_specs/topic_generation.v1.md",
        schema_relpath="schemas/topic_generation.v1.schema.json",
        output_json_path_template="<space_root>/runs/<run_id>/semantic/topic_generation.json",
    ),
    "query_synthesis": SemanticSpecMapEntry(
        flow_key="query_synthesis",
        spec_relpath="ai_flows/generation_specs/query_synthesis.v1.md",
        schema_relpath="schemas/query_synthesis.v1.schema.json",
        output_json_path_template="<space_root>/outputs/query/<query_id>/query.json",
    ),
    "comment_section_generation": SemanticSpecMapEntry(
        flow_key="comment_section_generation",
        spec_relpath="ai_flows/generation_specs/comment_section_generation.v1.md",
        schema_relpath="schemas/comment_section_generation.v1.schema.json",
        output_json_path_template=(
            "<space_root>/runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json"
        ),
    ),
    "persona_profile_generation": SemanticSpecMapEntry(
        flow_key="persona_profile_generation",
        spec_relpath="ai_flows/generation_specs/persona_profile_generation.v1.md",
        schema_relpath="schemas/persona_profile_generation.v1.schema.json",
        output_json_path_template="<space_root>/profiles/persona-<persona_id>.json",
    ),
}


def normalize_semantic_flow_key(flow_key: str) -> str:
    """Normalize compatibility aliases to canonical flow keys."""
    canonical_flow_key = FLOW_ALIAS_MAP.get(flow_key, flow_key)
    if canonical_flow_key != flow_key:
        warnings.warn(
            (
                f"Semantic flow key alias `{flow_key}` is deprecated; "
                f"use `{canonical_flow_key}`."
            ),
            DeprecationWarning,
            stacklevel=2,
        )
    return canonical_flow_key


def resolve_semantic_spec(flow_key: str, *, repo_root: Path) -> ResolvedSemanticSpec:
    """Resolve semantic spec only via the authoritative flow map."""
    canonical_flow_key = normalize_semantic_flow_key(flow_key)
    if canonical_flow_key not in FLOW_MAP:
        raise ValueError(f"Unknown semantic flow key: {flow_key}")

    entry = FLOW_MAP[canonical_flow_key]
    validate_map_entry_major_version(entry)

    spec_path = (repo_root / entry.spec_relpath).resolve()
    schema_path = (repo_root / entry.schema_relpath).resolve()
    if not spec_path.is_file():
        raise FileNotFoundError(f"Spec file not found for flow {canonical_flow_key}: {spec_path}")
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found for flow {canonical_flow_key}: {schema_path}")

    header = parse_spec_header(spec_path)
    _validate_spec_header_against_entry(header, entry)

    return ResolvedSemanticSpec(
        flow_key=canonical_flow_key,
        version=header.version,
        spec_path=spec_path,
        schema_path=schema_path,
        output_json_path_template=entry.output_json_path_template,
        context_paths=header.context_paths,
    )


def resolve_semantic_contract_with_precedence(
    flow_key: str,
    *,
    repo_root: Path,
    skill_contract: SkillSemanticContract | None = None,
    deterministic_schema_override: str | None = None,
) -> SemanticContractPrecedenceResult:
    """Resolve semantic contract from generation spec, ignoring conflicting skill text."""
    if deterministic_schema_override is not None:
        raise ValueError(
            "Deterministic render/build logic must not redefine semantic schemas outside generation spec/schema files."
        )

    resolved = resolve_semantic_spec(flow_key, repo_root=repo_root)
    if skill_contract is None:
        return SemanticContractPrecedenceResult(
            resolved_spec=resolved,
            conflict_fields=[],
            conflict_details={},
        )

    conflict_details: dict[str, dict[str, Any]] = {}
    if skill_contract.schema_path is not None and skill_contract.schema_path != str(
        resolved.schema_path.relative_to(repo_root.resolve())
    ):
        conflict_details["schema_path"] = {
            "authoritative": str(resolved.schema_path.relative_to(repo_root.resolve())),
            "skill": skill_contract.schema_path,
        }
    if skill_contract.output_json_path is not None and skill_contract.output_json_path != resolved.output_json_path_template:
        conflict_details["output_json_path"] = {
            "authoritative": resolved.output_json_path_template,
            "skill": skill_contract.output_json_path,
        }
    if skill_contract.context_paths is not None and skill_contract.context_paths != resolved.context_paths:
        conflict_details["context_paths"] = {
            "authoritative": resolved.context_paths,
            "skill": skill_contract.context_paths,
        }

    return SemanticContractPrecedenceResult(
        resolved_spec=resolved,
        conflict_fields=sorted(conflict_details.keys()),
        conflict_details=conflict_details,
    )


def resolve_semantic_invocation_spec(
    flow_key: str,
    *,
    repo_root: Path,
    path_tokens: Mapping[str, str | Path],
    skill_contract: SkillSemanticContract | None = None,
    deterministic_schema_override: str | None = None,
) -> ResolvedSemanticInvocationSpec:
    """Resolve canonical semantic invocation fields from generation spec contracts."""
    precedence = resolve_semantic_contract_with_precedence(
        flow_key,
        repo_root=repo_root,
        skill_contract=skill_contract,
        deterministic_schema_override=deterministic_schema_override,
    )
    resolved = precedence.resolved_spec
    output_json_path = _resolve_template_path(
        resolved.output_json_path_template,
        repo_root=repo_root,
        path_tokens=path_tokens,
    )
    context_paths = [
        _resolve_template_path(
            context_path,
            repo_root=repo_root,
            path_tokens=path_tokens,
        )
        for context_path in resolved.context_paths
    ]
    return ResolvedSemanticInvocationSpec(
        flow_key=resolved.flow_key,
        version=resolved.version,
        spec_path=resolved.spec_path,
        schema_path=resolved.schema_path,
        output_json_path=output_json_path,
        context_paths=context_paths,
    )


def validate_semantic_invocation_spec(
    flow_key: str,
    *,
    repo_root: Path,
    path_tokens: Mapping[str, str | Path],
    schema_path: Path,
    output_json_path: Path,
    context_paths: list[Path],
    skill_contract: SkillSemanticContract | None = None,
    deterministic_schema_override: str | None = None,
) -> None:
    """Validate invocation envelope matches canonical generation-spec contract."""
    canonical = resolve_semantic_invocation_spec(
        flow_key,
        repo_root=repo_root,
        path_tokens=path_tokens,
        skill_contract=skill_contract,
        deterministic_schema_override=deterministic_schema_override,
    )
    drift_fields: list[str] = []
    if schema_path.resolve() != canonical.schema_path.resolve():
        drift_fields.append("schema_path")
    if output_json_path.resolve() != canonical.output_json_path.resolve():
        drift_fields.append("output_json_path")
    normalized_context_paths = [path.resolve() for path in context_paths]
    canonical_context_paths = [path.resolve() for path in canonical.context_paths]
    if normalized_context_paths != canonical_context_paths:
        drift_fields.append("context_paths")
    if drift_fields:
        raise ValueError(
            "Semantic invocation envelope drifted from generation-spec contract: "
            + ", ".join(drift_fields)
        )


def validate_map_entry_major_version(entry: SemanticSpecMapEntry) -> None:
    """Ensure spec/schema major versions are pinned and matched in the flow map."""
    spec_major = _extract_major_from_spec_path(entry.spec_relpath)
    schema_major = _extract_major_from_schema_path(entry.schema_relpath)
    if spec_major != schema_major:
        raise ValueError(
            "Incompatible spec/schema major versions; add explicit major-version files and update flow map."
        )


def parse_spec_header(spec_path: Path) -> SemanticSpecHeader:
    """Parse the machine-readable header block from a generation spec."""
    content = spec_path.read_text()
    header_text, sep, _ = content.partition("\n---\n")
    if not sep:
        raise ValueError(f"Spec missing header/body separator: {spec_path}")

    flow_key = ""
    version = ""
    schema_path = ""
    output_json_path = ""
    context_paths: list[str] = []
    in_context_paths = False

    for raw_line in header_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if in_context_paths and stripped.startswith("- "):
            context_paths.append(stripped[2:].strip())
            continue
        in_context_paths = False

        if ":" not in stripped:
            raise ValueError(f"Malformed spec header line in {spec_path}: {raw_line}")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key == "flow_key":
            flow_key = value
        elif key == "version":
            version = value
        elif key == "schema_path":
            schema_path = value
        elif key == "output_json_path":
            output_json_path = value
        elif key == "context_paths":
            in_context_paths = True
        else:
            raise ValueError(f"Unexpected spec header key `{key}` in {spec_path}")

    if not flow_key or not version or not schema_path or not output_json_path:
        raise ValueError(f"Spec header missing required fields in {spec_path}")
    if not context_paths:
        raise ValueError(f"Spec header missing non-empty context_paths in {spec_path}")

    return SemanticSpecHeader(
        flow_key=flow_key,
        version=version,
        schema_path=schema_path,
        output_json_path=output_json_path,
        context_paths=context_paths,
    )


def _validate_spec_header_against_entry(header: SemanticSpecHeader, entry: SemanticSpecMapEntry) -> None:
    if header.flow_key != entry.flow_key:
        raise ValueError(
            f"Spec flow_key mismatch for {entry.flow_key}: header={header.flow_key}"
        )
    expected_major = _extract_major_from_spec_path(entry.spec_relpath)
    if header.version != f"v{expected_major}":
        raise ValueError(
            f"Spec version mismatch for {entry.flow_key}: header={header.version}"
        )
    if header.schema_path != entry.schema_relpath:
        raise ValueError(
            f"Spec schema_path mismatch for {entry.flow_key}: header={header.schema_path}"
        )
    if header.output_json_path != entry.output_json_path_template:
        raise ValueError(
            f"Spec output_json_path mismatch for {entry.flow_key}: header={header.output_json_path}"
        )


def _extract_major_from_spec_path(spec_relpath: str) -> int:
    marker = ".v"
    if marker not in spec_relpath:
        raise ValueError(f"Spec path missing major version marker: {spec_relpath}")
    tail = spec_relpath.rsplit(marker, 1)[1]
    major = tail.split(".", 1)[0]
    if not major.isdigit():
        raise ValueError(f"Spec path has invalid major version: {spec_relpath}")
    return int(major)


def _extract_major_from_schema_path(schema_relpath: str) -> int:
    marker = ".v"
    if marker not in schema_relpath:
        raise ValueError(f"Schema path missing major version marker: {schema_relpath}")
    tail = schema_relpath.rsplit(marker, 1)[1]
    major = tail.split(".", 1)[0]
    if not major.isdigit():
        raise ValueError(f"Schema path has invalid major version: {schema_relpath}")
    return int(major)


def _resolve_template_path(
    template: str,
    *,
    repo_root: Path,
    path_tokens: Mapping[str, str | Path],
) -> Path:
    token_pattern = re.compile(r"<([a-z_]+)>")
    missing_tokens = sorted(
        {
            token
            for token in token_pattern.findall(template)
            if token not in path_tokens
        }
    )
    if missing_tokens:
        raise ValueError(
            f"Missing path token(s) for template `{template}`: {', '.join(missing_tokens)}"
        )

    resolved_template = template
    for token in token_pattern.findall(template):
        token_value = path_tokens[token]
        replacement = str(token_value)
        resolved_template = resolved_template.replace(f"<{token}>", replacement)

    resolved_path = Path(resolved_template)
    if not resolved_path.is_absolute():
        resolved_path = repo_root / resolved_path
    return resolved_path.resolve()
