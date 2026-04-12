# Sapi Completed TODO Log

This file is append-only history for completed tasks moved out of `docs/todo.md`.

## 2026-04-12

- [x] TODO-0001: Align comment semantic-output path with per-page batching
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Make comment semantic artifacts one-per-invocation/per-target-page and make path token explicit.
  - evidence: Updated `docs/design.md` and `docs/low_level.md` contracts to use `runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json`.

- [x] TODO-0002: Unify comment namespace naming for discussion controls
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Resolve naming mismatch between `comment_section_*` namespace and discussion-controls schema naming.
  - evidence: Canonical schema now `comment_section_discussion_controls_v1` with compatibility alias `persona_discussion_controls_v1`.

- [x] TODO-0003: Add wrapper/entrypoint/workflow-key mapping contract
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Remove ambiguity between operator wrappers, script entrypoints, and lint-gate workflow keys.
  - evidence: Added mapping table in `docs/design.md` and workflow-key alignment section in `docs/low_level.md`.

- [x] TODO-0004: Define semantic-flow cardinality in run envelopes
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Specify whether repeated semantic calls are deduped and how invocation counts are represented.
  - evidence: Added ordered-unique `semantic_flows` plus `semantic_flow_invocation_counts` to design + low-level contracts and test checklist.

- [x] TODO-0005: Clarify warning-threshold semantics
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Clarify that `--warning-budget` is threshold-style status mapping and non-blocking by default.
  - evidence: Reworded warning behavior sections in `docs/design.md`, `docs/low_level.md`, and `docs/testing_plan.md`.

- [x] TODO-0006: Pin timestamp and ID-suffix format constraints
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Replace vague format language with explicit timestamp and suffix requirements.
  - evidence: Added temporal format contract and suffix constraints in `docs/design.md`; synchronized test-plan coverage.

- [x] TODO-0007: Reconcile phase ordering for query vs social implementation
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Remove contradiction between MVP slices and phase plan.
  - evidence: Reordered phases so query/core evaluation precedes social subsystem in `docs/design.md`.

- [x] TODO-0008: Remove ambiguous "Recovered" labeling from normative section
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Avoid mixed historical vs normative labeling in authoritative run-envelope section.
  - evidence: Renamed heading to `Canonical run-record metadata (normative base envelope for committed runs)`.

- [x] TODO-0232: Build a design-section-to-todo coverage map in docs
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - scope: Add a compact mapping table from each major design section to one or more TODO IDs to prevent backlog blind spots.
  - evidence: Added and maintained `Design Coverage Snapshot` in `docs/todo.md` covering Sections 1-13 with mapped TODO IDs.

- [x] TODO-0102: Add a cross-document contract index
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0201
  - scope: Create a quick index that maps core contracts to authoritative sections in `design.md`, `low_level.md`, and `testing_plan.md`.
  - acceptance:
    - One consolidated index exists.
    - No duplicate authority claims for the same contract.
    - Readers can locate authoritative contract text in under one minute.
  - evidence: Added `docs/contract_index.md`, linked it from `README.md`, and added `tests/unit/contracts/test_contract_index.py` to enforce one-table authority mapping with unique contract areas and explicit section pointers.
