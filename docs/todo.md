# Sapi TODO Log

## Operating Rules (Human + AI)

1. This file contains only open work (`[ ]` or `[~]`).
2. Use one task block per item with a stable ID: `TODO-XXXX`.
3. Keep newest items at the top of `## Open Tasks`.
4. Every task must include:
   - clear scope
   - acceptance criteria
   - owner (`human` or `ai`)
5. When a task is completed:
   - mark it `[x]`
   - add `finished_at` and short evidence note
   - move the full block to `docs/todo_finished.md`
   - remove it from this file (do not keep completed tasks here)
6. `docs/todo_finished.md` is append-only history. Do not rewrite old entries except to fix factual mistakes.
7. Each implementation task SHOULD include `phase` and `depends_on` to keep execution order explicit.
8. Prefer small, testable tasks over broad epics; split before starting if acceptance cannot be verified in one PR.
9. Keep the `Execution Queue` and all coverage snapshot sections current when adding/removing tasks.
10. Keep an explicit `Ready Now` shortlist synced with dependencies; only items with no unmet TODO dependencies belong there.
11. When splitting broad tasks, update parent task scope to avoid duplicated acceptance criteria across child tasks.
12. Keep `Priority Lanes` aligned with queue order so critical-path tasks remain visible.
13. For phase-level tracking tasks, pair planning trackers with explicit acceptance-gate tasks before marking phase/slice complete.

Status legend:
- `[ ]` queued
- `[~]` in progress
- `[x]` completed (must be moved to `docs/todo_finished.md`)

Task template:

```md
- [ ] TASK-<id>: Short title
  - owner: ai|human
  - created_at: YYYY-MM-DD
  - phase: Phase N | Cross-cutting (optional but recommended)
  - depends_on: TODO-XXXX, TODO-YYYY (optional but recommended)
  - scope: ...
  - acceptance:
    - ...
    - ...
  - notes: optional
```

## Open Tasks

### Ready Now (No Unmet TODO Dependencies)

1. `TODO-0326`
2. `TODO-0338`

### Immediate Next 10 (After Ready Now)

1. TODO-0327
2. TODO-0339
3. TODO-0340
4. TODO-0341
5. TODO-0342

### Priority Lanes (Current)

- P0 Foundation/contracts: TODO-0338
- P1 Core product behavior: TODO-0339, TODO-0340, TODO-0341
- P2 Social/eval/hardening: TODO-0326, TODO-0327, TODO-0342
- P3 Continuous docs governance: TODO-0327

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. TODO-0326

Wave B (ingest + projection + lint):
1. (none currently)

Wave C (query + social + hardening + release):
1. (none currently)

Wave D (space/subspace AI overview article):
1. TODO-0338
2. TODO-0339
3. TODO-0340
4. TODO-0341
5. TODO-0342

Cross-cutting docs backlog:
1. TODO-0327

### Design Coverage Snapshot

| Design area | Primary TODO IDs |
| --- | --- |
| Section 1 (scope/authority/reading) | - |
| Section 2 (runtime policy + semantic loop + mock mode) | - |
| Section 3 (core concepts + identity invariants) | - |
| Section 4 (repo architecture/spec ownership/versioning/capability boundaries) | - |
| Section 5 (paths/storage/IDs/registry/metadata/lint contracts) | - |
| Section 6 (wrapper UX + wrapper-to-entrypoint contract) | - |
| Section 7.1 ingest pipeline | TODO-0339 |
| Section 7.2 references/linking | - |
| Section 7.3 query pipeline | TODO-0339 |
| Section 7.4 persona catalog | - |
| Section 7.5 profile pages/history | - |
| Section 7.6 comments pipeline/rendering | - |
| Section 7.7 comment quality harness | - |
| Section 8 site/UI/static build | TODO-0340, TODO-0341 |
| Section 9 observability/safety/runtime controls | TODO-0341 |
| Section 10 run envelopes/lifecycle status | TODO-0339, TODO-0341 |
| Section 11 testing strategy | TODO-0342 |
| Section 12 reconstruction plan | - |
| Section 13 definition of done | - |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | TODO-0338 |
| Section 4 (core data types/run envelope types) | - |
| Section 5 (path + registry contracts) | - |
| Section 6 (semantic execution engine + retry/repair) | TODO-0339 |
| Section 7 (transaction/rollback) | TODO-0339 |
| Section 8 (pipeline execution contracts) | TODO-0339, TODO-0341 |
| Section 9 (deterministic build/projection) | TODO-0340, TODO-0341 |
| Section 10 (relation persistence) | TODO-0326 |
| Section 11 (lint/warning threshold) | - |
| Section 12 (wrapper/script interfaces) | TODO-0342 |
| Section 13 (observability/runtime controls/safety) | TODO-0341 |
| Section 14 (anti-drift and PR guardrails) | - |
| Section 15 (test-plan binding) | TODO-0327, TODO-0342 |
| Section 16 (change discipline) | - |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | TODO-0327, TODO-0342 |
| Tier 0-3 (fast contract/failure/pipeline suites) | TODO-0326, TODO-0339, TODO-0341, TODO-0342 |
| Tier 4-6 (determinism/golden/live canary) | TODO-0340, TODO-0342 |
| Section 4-5 (CI gating matrix + command wiring) | TODO-0327, TODO-0342 |
| Section 6 (exit criteria gating) | TODO-0342 |

### Task Blocks

- [ ] TODO-0342: Add overview synthesis tests, wrappers, and live-canary coverage
  - owner: ai
  - created_at: 2026-04-16
  - phase: Phase 6
  - depends_on: TODO-0339, TODO-0340, TODO-0341
  - scope: Add comprehensive coverage and wrapper-level ergonomics for space-overview generation and rendering across local and live modes.
  - acceptance:
    - Unit/integration tests validate overview artifact schema compliance, reference integrity (claims/sources), and deterministic rebuild behavior.
    - Wrapper contract tests cover canonical invocation path for overview generation (including target space/subspace selection and failure semantics).
    - Live canary coverage includes overview generation for at least one seeded space and asserts canonical artifacts are present and parseable.
    - `docs/testing_plan.md` is updated with explicit overview-flow coverage expectations.

- [ ] TODO-0341: Add change-detection and refresh policy for overview regeneration
  - owner: ai
  - created_at: 2026-04-16
  - phase: Phase 6
  - depends_on: TODO-0339
  - scope: Ensure overview generation is refreshed only when relevant canonical inputs change, while preserving explicit force-regeneration behavior for debugging/recovery.
  - acceptance:
    - Overview pipeline computes and persists an input signature derived from canonical records used for synthesis (`sources/records`, `claims`, `relations`, and source dossiers).
    - Re-running overview generation with unchanged signature skips LLM synthesis and records a deterministic “no content change” path.
    - A force mode bypasses signature skip behavior and re-synthesizes overview artifacts.
    - Run metadata records refresh decision details (signature, skip/refresh reason, flow invocation counts).

- [ ] TODO-0340: Render overview article on space/subspace front pages
  - owner: ai
  - created_at: 2026-04-16
  - phase: Phase 6
  - depends_on: TODO-0339
  - scope: Surface generated overview content directly on each space/subspace landing page and expose a dedicated full overview route.
  - acceptance:
    - `sapi/build/site_builder.py` (or delegated render modules) renders a prominent overview section on each space/subspace index page when overview artifacts exist.
    - Full article route is generated at canonical location `spaces/<space_name>/site/overview/index.html`.
    - Space/subspace navigation links to overview route with stable semantics and accessibility labels.
    - If overview artifact is missing, rendering degrades gracefully without broken links.

- [ ] TODO-0339: Implement canonical `space_overview_generation` semantic flow and artifacts
  - owner: ai
  - created_at: 2026-04-16
  - phase: Phase 6
  - depends_on: TODO-0338
  - scope: Add a pipeline that synthesizes a long-form topic overview from ingested sources/claims/relations for each space (and selected subspaces), using shared semantic execution policy.
  - acceptance:
    - Pipeline writes canonical artifacts under `spaces/<space_name>/outputs/space_overview/<overview_id>/` including structured JSON and markdown article outputs.
    - JSON artifact includes required sections: topic framing, key themes, agreement/disagreement map, methods/evidence landscape, open questions, and citation anchors.
    - Output sections include auditable references to canonical `source_id` and `claim_id` values.
    - Run envelopes include canonical flow key (`space_overview_generation`) and accurate attempt/invocation accounting.
    - Pipeline handles “no ingested sources” as a clear non-crashing outcome with explicit warning/status metadata.

- [ ] TODO-0338: Define canonical contracts for space/subspace overview synthesis
  - owner: ai
  - created_at: 2026-04-16
  - phase: Cross-cutting
  - scope: Specify artifact schema, flow ownership, and deterministic rendering boundaries for AI-generated overview articles that summarize all ingested papers in a space/subspace.
  - acceptance:
    - `docs/design.md` and `docs/low_level.md` define normative behavior for overview synthesis inputs, outputs, and citation/auditability requirements.
    - A canonical schema is added for overview artifact JSON payloads (sections, references, metadata, freshness fields).
    - Semantic flow contract entry is added for `space_overview_generation` with canonical output path tokens.
    - Contract tests verify schema/docs/flow-spec alignment and fail on drift.

- [ ] TODO-0327: Purge compatibility/deprecation tests and add strict no-legacy coverage
  - owner: ai
  - created_at: 2026-04-13
  - phase: Cross-cutting
  - depends_on: TODO-0313, TODO-0314, TODO-0315, TODO-0316, TODO-0317, TODO-0318, TODO-0319, TODO-0320, TODO-0321, TODO-0322, TODO-0323, TODO-0326
  - scope: Remove compatibility/deprecation-only test expectations and replace them with strict canonical-only behavior checks.
  - acceptance:
    - Tests no longer assert deprecation warnings or legacy alias acceptance for removed pathways.
    - New/updated tests assert legacy inputs fail fast with clear errors.
    - `docs/testing_plan.md` is updated where test contract expectations changed.

- [ ] TODO-0326: Remove relation status compatibility alias `closed`
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove acceptance/normalization of relation status `closed`; accept only canonical status values.
  - acceptance:
    - `sapi/ingest/relation_store.py` rejects `closed` status inputs.
    - Tests and docs no longer describe `closed` as accepted alias.
