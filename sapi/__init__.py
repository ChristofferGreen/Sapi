"""Sapi reconstruction package.

Module boundaries (authoritative topology: docs/low_level.md Section 3):
- contracts: identifiers, paths, run envelopes, schemas, semantic spec metadata
- core: registry resolution, scope resolution, filesystem store, transactions, locks
- llm: backend client, trace wiring, shared semantic executor
- ingest: ingest pipeline orchestration and canonical ingest writes
- query: query pipeline orchestration, retrieval, and rendering
- comments: comments pipeline orchestration and deterministic merge/controls
- profiles: profile pipeline orchestration and history updates
- overview: overview synthesis orchestration and deterministic article rendering
- build: deterministic projection and site build/index logic
- lint: lint engine and severity policy
"""

__all__ = [
    "contracts",
    "core",
    "llm",
    "ingest",
    "query",
    "comments",
    "profiles",
    "overview",
    "build",
    "lint",
]
