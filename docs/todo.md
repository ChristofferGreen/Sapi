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

1. `TODO-0377`: Seed prepared questions during example-site creation
2. `TODO-0374`: Extract and render question measurement values

### Immediate Next 10 (After Ready Now)

1. TODO-0376: Add prepared-question test and verification coverage

### Priority Lanes (Current)

- P0 Foundation/contracts: (none currently)
- P1 Core product behavior: TODO-0377
- P2 Social/eval/hardening: TODO-0374, TODO-0376
- P3 Continuous docs governance: (none currently)

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. (none currently)

Wave B (ingest + projection + lint):
1. (none currently)

Wave C (query + social + hardening + release):
1. TODO-0377: Seed prepared questions during example-site creation
2. TODO-0374: Extract and render question measurement values
3. TODO-0376: Add prepared-question test and verification coverage

Wave D (space/subspace AI overview article):
1. (none currently)

Cross-cutting docs backlog:
1. (none currently)

### Design Coverage Snapshot

| Design area | Primary TODO IDs |
| --- | --- |
| Section 1 (scope/authority/reading) | - |
| Section 2 (runtime policy + semantic loop + mock mode) | - |
| Section 3 (core concepts + identity invariants) | - |
| Section 4 (repo architecture/spec ownership/versioning/capability boundaries) | - |
| Section 5 (paths/storage/IDs/registry/metadata/lint contracts) | TODO-0374 |
| Section 6 (wrapper UX + wrapper-to-entrypoint contract) | TODO-0377 |
| Section 7.1 ingest pipeline | TODO-0374 |
| Section 7.2 references/linking | - |
| Section 7.3 query pipeline | - |
| Section 7.4 persona catalog | - |
| Section 7.5 profile pages/history | - |
| Section 7.6 comments pipeline/rendering | - |
| Section 7.7 comment quality harness | - |
| Section 8 site/UI/static build | TODO-0374, TODO-0377 |
| Section 9 observability/safety/runtime controls | - |
| Section 10 run envelopes/lifecycle status | - |
| Section 11 testing strategy | TODO-0376 |
| Section 12 reconstruction plan | TODO-0377 |
| Section 13 definition of done | TODO-0376 |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | - |
| Section 4 (core data types/run envelope types) | TODO-0374 |
| Section 5 (path + registry contracts) | - |
| Section 6 (semantic execution engine + retry/repair) | TODO-0374 |
| Section 7 (transaction/rollback) | - |
| Section 8 (pipeline execution contracts) | - |
| Section 9 (deterministic build/projection) | TODO-0374, TODO-0377 |
| Section 10 (relation persistence) | - |
| Section 11 (lint/warning threshold) | - |
| Section 12 (wrapper/script interfaces) | TODO-0377 |
| Section 13 (observability/runtime controls/safety) | - |
| Section 14 (anti-drift and PR guardrails) | - |
| Section 15 (test-plan binding) | TODO-0376 |
| Section 16 (change discipline) | - |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | TODO-0376 |
| Tier 0-3 (fast contract/failure/pipeline suites) | TODO-0377 |
| Tier 4-6 (determinism/golden/live canary) | TODO-0374, TODO-0376, TODO-0377 |
| Section 4-5 (CI gating matrix + command wiring) | TODO-0376 |
| Section 6 (exit criteria gating) | TODO-0376 |

### Task Blocks

- [ ] TODO-0377: Seed prepared questions during example-site creation
  - owner: ai
  - created_at: 2026-04-30
  - phase: Prepared questions
  - depends_on: none
  - scope: Update the example-site creation and reconstruction path so every example space and subspace is created with a useful starter set of prepared questions.
  - acceptance:
    - Example-site seed data includes roughly 10 explicit prepared questions per example space/subspace, tailored to the field of that space and reviewed as operator-authored content rather than generated by deterministic code.
    - `create_site.sh`, `create_space.sh`, reconstruction docs, and any example-site bootstrap helpers invoke the prepared-question authoring path during creation instead of writing ad hoc question files.
    - Example question sets are stored in a documented fixture or seed-data location with stable IDs, display order, scope, and update guidance.
    - Recreating the example site produces question front pages for every seeded space/subspace, with empty question detail pages before ingest and populated detail pages after relevant sources are ingested.
    - Tests or verification scripts assert that newly created example spaces/subspaces contain the expected prepared-question records and that the rendered example site exposes those questions as the landing experience.
  - notes: Deterministic question index/detail rendering and ingest-time question synthesis are implemented. Creation-time example seed wiring remains.

- [ ] TODO-0376: Add prepared-question test and verification coverage
  - owner: ai
  - created_at: 2026-04-30
  - phase: Prepared questions
  - depends_on: TODO-0374, TODO-0377
  - scope: Add focused unit, integration, deterministic build, golden, and optional live-canary coverage for the prepared-question feature.
  - acceptance:
    - Unit tests cover schema resolution, question ID/link validation, measurement compatibility, and synthesis freshness decisions.
    - Integration tests cover authoring questions, ingest-time relevance mapping, affected-question synthesis, rollback on failed semantic output, and wrapper argument contracts in mock-LLM mode.
    - Integration tests cover spaces with no prepared questions, no relevant question matches, and subspace question isolation.
    - Example-site verification covers creation-time prepared-question seeding for every example space/subspace and confirms roughly 10 questions per seeded scope.
    - Determinism/golden tests cover question index/detail pages and chart/table rendering where applicable.
    - Verification scripts or testing-plan docs are updated so prepared questions become part of future DoD/exit-gate evidence.
  - notes: Keep live LLM coverage non-blocking unless the broader live canary policy changes.

- [ ] TODO-0374: Extract and render question measurement values
  - owner: ai
  - created_at: 2026-04-30
  - phase: Prepared questions
  - depends_on: none
  - scope: Add optional structured measurement extraction for question-relevant evidence and deterministic table/chart rendering for compatible measurement rows.
  - acceptance:
    - Measurement records capture source ID, claim ID or evidence ID, measure name, value/range, unit, population/context, outcome, comparator, and uncertainty metadata when available.
    - Extraction fails or warns rather than coercing incompatible or missing measurement values into fake numeric data.
    - Rendering emits a table for all valid measurement rows and emits a graph only when rows share compatible measure/unit/outcome/population semantics.
    - Charted values retain source/evidence links, units, and caveats so visual summaries remain auditable.
    - Tests cover graph-eligible rows, table-only rows, incompatible units, missing values, and no-measurement empty states.
  - notes: Nutrition examples such as grams of protein per day or g/kg/day need unit/context normalization before charting.
