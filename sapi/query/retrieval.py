"""Deterministic query retrieval helpers for canonical context reads."""

from __future__ import annotations

import json
from pathlib import Path


def retrieve_query_context(
    *,
    space_root: Path,
    max_claims: int,
    max_sources: int,
    include_disputed: bool,
) -> tuple[list[str], list[str], dict[str, int]]:
    claim_candidates = _load_ranked_candidates(
        root=space_root / "claims",
        pattern="claim-*.json",
    )
    source_candidates = _load_ranked_candidates(
        root=space_root / "sources" / "records",
        pattern="source-*.json",
    )

    if not include_disputed:
        claim_candidates = [
            candidate for candidate in claim_candidates if "disputed" not in candidate["id"]
        ]

    ordered_claim_ids = _sort_candidates(candidates=claim_candidates)
    ordered_source_ids = _sort_candidates(candidates=source_candidates)
    selected_claim_ids = ordered_claim_ids[:max_claims]
    selected_source_ids = ordered_source_ids[:max_sources]
    omitted = {
        "claims": max(len(ordered_claim_ids) - len(selected_claim_ids), 0),
        "sources": max(len(ordered_source_ids) - len(selected_source_ids), 0),
    }
    return selected_claim_ids, selected_source_ids, omitted


def _load_ranked_candidates(*, root: Path, pattern: str) -> list[dict[str, int | str]]:
    candidates: list[dict[str, int | str]] = []
    if not root.is_dir():
        return candidates
    for path in sorted(root.glob(pattern)):
        if not path.is_file():
            continue
        candidate_id = path.stem
        retrieval_rank = _read_retrieval_rank(path=path)
        candidates.append({"id": candidate_id, "retrieval_rank": retrieval_rank})
    return candidates


def _read_retrieval_rank(*, path: Path) -> int:
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return 0
    raw_rank = payload.get("retrieval_rank")
    if isinstance(raw_rank, bool):
        return 0
    if isinstance(raw_rank, int):
        return raw_rank
    return 0


def _sort_candidates(*, candidates: list[dict[str, int | str]]) -> list[str]:
    ordered = sorted(
        candidates,
        key=lambda row: (
            -int(row["retrieval_rank"]),
            str(row["id"]),
        ),
    )
    return [str(row["id"]) for row in ordered]
