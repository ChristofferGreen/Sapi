"""Deterministic comment-quality benchmark scoring and manifest helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from sapi.contracts.ids import format_timestamp_rfc3339_utc
from sapi.contracts.schemas import load_json_schema, require_valid_json_instance


QUALITY_DIMENSIONS: tuple[str, ...] = (
    "persona_consistency",
    "novelty",
    "relevance",
    "argument_quality",
    "human_likeness",
)

_BENCHMARK_PATH = Path("sapi/benchmarks/comment_quality_benchmark_v1.json")
_BENCHMARK_SCHEMA_PATH = Path("schemas/comment_section_quality_benchmark_v1.schema.json")
_MANIFEST_SCHEMA_PATH = Path("schemas/comment_section_quality_eval_manifest_v1.schema.json")
_MANIFEST_SCHEMA_VERSION = "comment_section_quality_eval_manifest_v1"
_ARGUMENTATIVE_POSITIONS = {"support", "challenge", "rebuttal", "synthesis"}


@dataclass(frozen=True)
class CommentQualityBenchmark:
    """Loaded benchmark configuration for deterministic comment-quality scoring."""

    schema_version: str
    benchmark_id: str
    dimensions: tuple[str, ...]
    overall_min: float
    dimension_mins: dict[str, float]
    benchmark_path: Path


def load_comment_quality_benchmark(*, repo_root: Path) -> CommentQualityBenchmark:
    """Load and validate the canonical comment-quality benchmark artifact."""
    benchmark_path = repo_root / _BENCHMARK_PATH
    schema_path = repo_root / _BENCHMARK_SCHEMA_PATH

    payload = json.loads(benchmark_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("Comment quality benchmark must be a JSON object.")

    schema = load_json_schema(schema_path)
    require_valid_json_instance(payload, schema)

    dimensions = tuple(str(item) for item in payload["dimensions"])
    thresholds = payload["thresholds"]
    assert isinstance(thresholds, dict)
    dimension_mins_raw = thresholds["dimension_mins"]
    assert isinstance(dimension_mins_raw, dict)
    dimension_mins = {str(key): float(value) for key, value in dimension_mins_raw.items()}
    return CommentQualityBenchmark(
        schema_version=str(payload["schema_version"]),
        benchmark_id=str(payload["benchmark_id"]),
        dimensions=dimensions,
        overall_min=float(thresholds["overall_min"]),
        dimension_mins=dimension_mins,
        benchmark_path=benchmark_path,
    )


def build_comment_quality_manifest(
    *,
    repo_root: Path,
    space_root: Path,
    comments_by_page: dict[str, list[dict[str, object]]],
    snapshot_path: Path | None,
    as_of: datetime | None = None,
) -> tuple[Path, dict[str, object]]:
    """Build a validated comment-quality manifest and canonical output path."""
    benchmark = load_comment_quality_benchmark(repo_root=repo_root)
    row_scores = _score_rows(
        comments_by_page=comments_by_page,
        dimensions=benchmark.dimensions,
    )
    aggregates = _compute_aggregates(row_scores=row_scores, dimensions=benchmark.dimensions)
    thresholds = {
        "overall_min": round(benchmark.overall_min, 4),
        "dimension_mins": {
            dimension: round(float(benchmark.dimension_mins[dimension]), 4)
            for dimension in benchmark.dimensions
        },
    }
    fail_reasons = _compute_fail_reasons(
        row_count=len(row_scores),
        overall=aggregates["overall"],
        dimension_scores=aggregates["dimensions"],
        overall_min=thresholds["overall_min"],
        dimension_mins=thresholds["dimension_mins"],
        dimensions=benchmark.dimensions,
    )
    passed = not fail_reasons
    evaluation_id = _make_evaluation_id(
        dimensions=benchmark.dimensions,
        row_scores=row_scores,
        aggregates=aggregates,
        thresholds=thresholds,
        fail_reasons=fail_reasons,
    )
    manifest_payload: dict[str, object] = {
        "schema_version": _MANIFEST_SCHEMA_VERSION,
        "evaluation_id": evaluation_id,
        "as_of": format_timestamp_rfc3339_utc((as_of or datetime.now(UTC)).astimezone(UTC)),
        "snapshot_path": _as_space_relative_path(path=snapshot_path, space_root=space_root),
        "benchmark_path": str(_BENCHMARK_PATH),
        "row_count": len(row_scores),
        "dimensions": list(benchmark.dimensions),
        "row_scores": row_scores,
        "aggregates": aggregates,
        "thresholds": thresholds,
        "pass": passed,
        "fail_reasons": fail_reasons,
    }

    manifest_schema = load_json_schema(repo_root / _MANIFEST_SCHEMA_PATH)
    require_valid_json_instance(manifest_payload, manifest_schema)

    manifest_path = (
        space_root
        / "outputs"
        / "comment_quality"
        / evaluation_id
        / "manifest.json"
    )
    return manifest_path, manifest_payload


def _score_rows(
    *,
    comments_by_page: dict[str, list[dict[str, object]]],
    dimensions: tuple[str, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    body_keys: list[str] = []
    ordered_rows: list[tuple[str, int, dict[str, object]]] = []
    for page_ref in sorted(comments_by_page):
        page_comments = comments_by_page[page_ref]
        for row_index, comment in enumerate(page_comments, start=1):
            if not isinstance(comment, dict):
                continue
            ordered_rows.append((page_ref, row_index, comment))
            body_keys.append(_body_key(comment))

    body_counts = Counter(body_keys)
    for page_ref, row_index, comment in ordered_rows:
        body = _normalized_body(comment)
        dimension_scores = {
            "persona_consistency": _score_persona_consistency(comment),
            "novelty": _score_novelty(body_counts[body.lower()]),
            "relevance": _score_relevance(body),
            "argument_quality": _score_argument_quality(comment),
            "human_likeness": _score_human_likeness(body),
        }
        for dimension in dimensions:
            if dimension not in dimension_scores:
                raise ValueError(f"Missing deterministic scorer for benchmark dimension: {dimension}")
        ordered_dimension_scores = {
            dimension: round(float(dimension_scores[dimension]), 4)
            for dimension in dimensions
        }
        row_overall = round(
            sum(ordered_dimension_scores[dimension] for dimension in dimensions) / len(dimensions),
            4,
        )
        rows.append(
            {
                "page_ref": page_ref,
                "row_index": row_index,
                "comment_uid": _optional_string(comment.get("comment_uid")),
                "persona_id": _optional_string(comment.get("persona_id")),
                "dimension_scores": ordered_dimension_scores,
                "overall": row_overall,
            }
        )
    return rows


def _compute_aggregates(
    *,
    row_scores: list[dict[str, object]],
    dimensions: tuple[str, ...],
) -> dict[str, object]:
    if not row_scores:
        return {
            "overall": 0.0,
            "dimensions": {dimension: 0.0 for dimension in dimensions},
        }
    dimension_aggregates: dict[str, float] = {}
    for dimension in dimensions:
        total = 0.0
        for row in row_scores:
            row_dimension_scores = row["dimension_scores"]
            assert isinstance(row_dimension_scores, dict)
            total += float(row_dimension_scores[dimension])
        dimension_aggregates[dimension] = round(total / len(row_scores), 4)
    overall = round(
        sum(dimension_aggregates[dimension] for dimension in dimensions) / len(dimensions),
        4,
    )
    return {
        "overall": overall,
        "dimensions": dimension_aggregates,
    }


def _compute_fail_reasons(
    *,
    row_count: int,
    overall: float,
    dimension_scores: dict[str, object],
    overall_min: float,
    dimension_mins: dict[str, float],
    dimensions: tuple[str, ...],
) -> list[str]:
    reasons: list[str] = []
    if row_count <= 0:
        reasons.append("no_comment_rows")
    if overall < overall_min:
        reasons.append(f"overall_below_min:{overall:.4f}<{overall_min:.4f}")
    for dimension in dimensions:
        score = float(dimension_scores[dimension])
        threshold = float(dimension_mins[dimension])
        if score < threshold:
            reasons.append(f"{dimension}_below_min:{score:.4f}<{threshold:.4f}")
    return reasons


def _make_evaluation_id(
    *,
    dimensions: tuple[str, ...],
    row_scores: list[dict[str, object]],
    aggregates: dict[str, object],
    thresholds: dict[str, object],
    fail_reasons: list[str],
) -> str:
    digest_basis = {
        "dimensions": list(dimensions),
        "rows": [
            {
                "page_ref": row["page_ref"],
                "row_index": row["row_index"],
                "dimension_scores": row["dimension_scores"],
                "overall": row["overall"],
            }
            for row in row_scores
        ],
        "aggregates": aggregates,
        "thresholds": thresholds,
        "fail_reasons": fail_reasons,
    }
    digest = hashlib.sha256(
        json.dumps(digest_basis, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return f"CQ-{digest[:12]}"


def _score_persona_consistency(comment: dict[str, object]) -> float:
    persona_id = _optional_string(comment.get("persona_id"))
    return 1.0 if persona_id else 0.0


def _score_novelty(body_occurrences: int) -> float:
    if body_occurrences <= 1:
        return 1.0
    return 0.25


def _score_relevance(body: str) -> float:
    word_count = len(body.split())
    if word_count >= 8:
        return 1.0
    if word_count >= 4:
        return 0.75
    if word_count > 0:
        return 0.5
    return 0.0


def _score_argument_quality(comment: dict[str, object]) -> float:
    turn = comment.get("turn")
    if not isinstance(turn, dict):
        return 0.6
    position = str(turn.get("position") or "").strip().lower()
    if position in _ARGUMENTATIVE_POSITIONS:
        evidence_refs = turn.get("evidence_refs")
        if isinstance(evidence_refs, list) and evidence_refs:
            return 1.0
        return 0.45
    if position == "social":
        return 0.65
    return 0.55


def _score_human_likeness(body: str) -> float:
    word_count = len(body.split())
    if 5 <= word_count <= 80:
        return 0.85
    if 2 <= word_count < 5:
        return 0.6
    if 80 < word_count <= 180:
        return 0.65
    if word_count > 0:
        return 0.4
    return 0.0


def _body_key(comment: dict[str, object]) -> str:
    return _normalized_body(comment).lower()


def _normalized_body(comment: dict[str, object]) -> str:
    return " ".join(str(comment.get("body") or "").split()).strip()


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _as_space_relative_path(*, path: Path | None, space_root: Path) -> str | None:
    if path is None:
        return None
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(space_root.resolve()))
    except ValueError:
        return str(resolved)
