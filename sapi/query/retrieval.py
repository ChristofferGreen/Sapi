"""Deterministic query retrieval helpers for canonical context reads."""

from __future__ import annotations

from pathlib import Path


def retrieve_query_context(
    *,
    space_root: Path,
    max_claims: int,
    max_sources: int,
    include_disputed: bool,
) -> tuple[list[str], list[str], dict[str, int]]:
    claim_ids = sorted(path.stem for path in (space_root / "claims").glob("claim-*.json"))
    source_ids = sorted(
        path.stem for path in (space_root / "sources" / "records").glob("source-*.json")
    )

    if not include_disputed:
        claim_ids = [claim_id for claim_id in claim_ids if "disputed" not in claim_id]

    selected_claim_ids = claim_ids[:max_claims]
    selected_source_ids = source_ids[:max_sources]
    omitted = {
        "claims": max(len(claim_ids) - len(selected_claim_ids), 0),
        "sources": max(len(source_ids) - len(selected_source_ids), 0),
    }
    return selected_claim_ids, selected_source_ids, omitted
