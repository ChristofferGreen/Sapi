"""MVP Slice A verification helpers (TODO-0260)."""

from __future__ import annotations

import json
from pathlib import Path


_BASE_REQUIRED_FIELDS = (
    "run_id",
    "flow_key",
    "semantic_flows",
    "semantic_flow_invocation_counts",
    "status",
    "started_at",
    "completed_at",
    "model_fingerprint",
    "provider_fingerprint",
    "reasoning_effort",
    "execution_mode",
    "llm_attempt_count",
    "toolchain_versions",
    "lint_error_count",
    "lint_warning_count",
    "lint_info_count",
)

_INGEST_REQUIRED_FIELDS = (
    "ingest_scope",
    "source_ids",
    "claims_changed",
    "relations_changed",
    "topic_pages_changed",
    "build_deferred",
    "deferred_build_reason",
    "force_mode",
    "rollback_skipped",
    "restricted_source_mode",
    "source_access_policy",
)

_QUERY_REQUIRED_FIELDS = (
    "query_id",
    "mode",
    "scope",
    "claims_used",
    "sources_used",
    "contradictions_considered",
    "manifest_path",
)


def parse_run_frontmatter(markdown: str) -> dict[str, object]:
    lines = markdown.splitlines()
    if len(lines) < 3 or lines[0] != "---":
        raise ValueError("Run markdown missing frontmatter start delimiter.")

    frontmatter: dict[str, object] = {}
    index = 1
    while index < len(lines) and lines[index] != "---":
        line = lines[index]
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line!r}")
        key, raw = line.split(":", 1)
        frontmatter[key.strip()] = json.loads(raw.strip())
        index += 1

    if index >= len(lines) or lines[index] != "---":
        raise ValueError("Run markdown missing frontmatter end delimiter.")
    return frontmatter


def load_run_frontmatter(*, space_root: Path, run_id: str) -> dict[str, object]:
    run_md_path = space_root / "runs" / run_id / "run.md"
    if not run_md_path.is_file():
        raise FileNotFoundError(f"Run record not found for run_id={run_id}: {run_md_path}")
    return parse_run_frontmatter(run_md_path.read_text())


def validate_ingest_run_frontmatter(frontmatter: dict[str, object]) -> list[str]:
    errors: list[str] = []
    _validate_base_frontmatter(frontmatter, errors=errors)
    _validate_required_fields(frontmatter, _INGEST_REQUIRED_FIELDS, errors=errors)
    _validate_expected_flow_key(frontmatter, expected_flow_key="ingest_pipeline", errors=errors)
    _validate_semantic_cardinality(
        frontmatter,
        expected_flows=("ingest_extraction", "topic_generation"),
        alternate_expected_flows=(("source_revision_detection", "ingest_extraction", "topic_generation"),),
        errors=errors,
    )
    return errors


def validate_query_run_frontmatter(frontmatter: dict[str, object]) -> list[str]:
    errors: list[str] = []
    _validate_base_frontmatter(frontmatter, errors=errors)
    _validate_required_fields(frontmatter, _QUERY_REQUIRED_FIELDS, errors=errors)
    _validate_expected_flow_key(frontmatter, expected_flow_key="query_pipeline", errors=errors)
    _validate_semantic_cardinality(
        frontmatter,
        expected_flows=("query_synthesis",),
        errors=errors,
    )
    return errors


def deferred_build_backlog_run_ids(*, space_root: Path) -> list[str]:
    runs_root = space_root / "runs"
    if not runs_root.is_dir():
        return []
    deferred: list[str] = []
    for run_dir in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        run_id = run_dir.name
        run_md_path = run_dir / "run.md"
        if not run_md_path.is_file():
            continue
        frontmatter = parse_run_frontmatter(run_md_path.read_text())
        if frontmatter.get("build_deferred") is True:
            deferred.append(run_id)
    return deferred


def _validate_base_frontmatter(frontmatter: dict[str, object], *, errors: list[str]) -> None:
    _validate_required_fields(frontmatter, _BASE_REQUIRED_FIELDS, errors=errors)


def _validate_required_fields(
    frontmatter: dict[str, object],
    required_fields: tuple[str, ...],
    *,
    errors: list[str],
) -> None:
    for key in required_fields:
        if key not in frontmatter:
            errors.append(f"Missing required frontmatter field: {key}")


def _validate_expected_flow_key(
    frontmatter: dict[str, object],
    *,
    expected_flow_key: str,
    errors: list[str],
) -> None:
    flow_key = frontmatter.get("flow_key")
    if flow_key != expected_flow_key:
        errors.append(f"flow_key must be {expected_flow_key!r}, got {flow_key!r}")


def _validate_semantic_cardinality(
    frontmatter: dict[str, object],
    *,
    expected_flows: tuple[str, ...],
    alternate_expected_flows: tuple[tuple[str, ...], ...] = (),
    errors: list[str],
) -> None:
    semantic_flows = frontmatter.get("semantic_flows")
    invocation_counts = frontmatter.get("semantic_flow_invocation_counts")
    if not isinstance(semantic_flows, list):
        errors.append("semantic_flows must be a list.")
        return
    actual_flows = tuple(str(flow) for flow in semantic_flows)
    expected_options = (expected_flows, *alternate_expected_flows)
    if actual_flows not in expected_options:
        errors.append(
            f"semantic_flows must match one of {[list(option) for option in expected_options]!r}, "
            f"got {semantic_flows!r}"
        )
    if not isinstance(invocation_counts, dict):
        errors.append("semantic_flow_invocation_counts must be an object.")
        return
    for flow in actual_flows:
        count = invocation_counts.get(flow)
        if not isinstance(count, int) or count < 1:
            errors.append(
                f"semantic_flow_invocation_counts[{flow!r}] must be a positive integer."
            )
