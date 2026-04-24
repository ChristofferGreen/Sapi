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

1. `TODO-0342`
2. `TODO-0327`

### Immediate Next 10 (After Ready Now)

1. (none currently)

### Priority Lanes (Current)

- P0 Foundation/contracts: (none currently)
- P1 Core product behavior: (none currently)
- P2 Social/eval/hardening: TODO-0342, TODO-0327
- P3 Continuous docs governance: TODO-0327

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. (none currently)

Wave B (ingest + projection + lint):
1. (none currently)

Wave C (query + social + hardening + release):
1. (none currently)

Wave D (space/subspace AI overview article):
1. TODO-0342

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
| Section 7.1 ingest pipeline | - |
| Section 7.2 references/linking | - |
| Section 7.3 query pipeline | - |
| Section 7.4 persona catalog | - |
| Section 7.5 profile pages/history | - |
| Section 7.6 comments pipeline/rendering | - |
| Section 7.7 comment quality harness | - |
| Section 8 site/UI/static build | - |
| Section 9 observability/safety/runtime controls | - |
| Section 10 run envelopes/lifecycle status | - |
| Section 11 testing strategy | TODO-0342 |
| Section 12 reconstruction plan | - |
| Section 13 definition of done | - |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | - |
| Section 4 (core data types/run envelope types) | - |
| Section 5 (path + registry contracts) | - |
| Section 6 (semantic execution engine + retry/repair) | - |
| Section 7 (transaction/rollback) | - |
| Section 8 (pipeline execution contracts) | - |
| Section 9 (deterministic build/projection) | - |
| Section 10 (relation persistence) | - |
| Section 11 (lint/warning threshold) | - |
| Section 12 (wrapper/script interfaces) | TODO-0342 |
| Section 13 (observability/runtime controls/safety) | - |
| Section 14 (anti-drift and PR guardrails) | - |
| Section 15 (test-plan binding) | TODO-0327, TODO-0342 |
| Section 16 (change discipline) | - |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | TODO-0327, TODO-0342 |
| Tier 0-3 (fast contract/failure/pipeline suites) | TODO-0342 |
| Tier 4-6 (determinism/golden/live canary) | TODO-0342 |
| Section 4-5 (CI gating matrix + command wiring) | TODO-0327, TODO-0342 |
| Section 6 (exit criteria gating) | TODO-0342 |

### Task Blocks

- [ ] TODO-0342: Add overview synthesis tests, wrappers, and live-canary coverage
  - owner: ai
  - created_at: 2026-04-16
  - phase: Phase 6
  - depends_on: TODO-0339
  - scope: Add comprehensive coverage and wrapper-level ergonomics for space-overview generation and rendering across local and live modes.
  - acceptance:
    - Unit/integration tests validate overview artifact schema compliance, reference integrity (claims/sources), and deterministic rebuild behavior.
    - Wrapper contract tests cover canonical invocation path for overview generation (including target space/subspace selection and failure semantics).
    - Live canary coverage includes overview generation for at least one seeded space and asserts canonical artifacts are present and parseable.
    - `docs/testing_plan.md` is updated with explicit overview-flow coverage expectations.

- [ ] TODO-0327: Purge compatibility/deprecation tests and add strict no-legacy coverage
  - owner: ai
  - created_at: 2026-04-13
  - phase: Cross-cutting
  - depends_on: TODO-0313, TODO-0314, TODO-0315, TODO-0316, TODO-0317, TODO-0318, TODO-0319, TODO-0320, TODO-0321, TODO-0322, TODO-0323
  - scope: Remove compatibility/deprecation-only test expectations and replace them with strict canonical-only behavior checks.
  - acceptance:
    - Tests no longer assert deprecation warnings or legacy alias acceptance for removed pathways.
    - New/updated tests assert legacy inputs fail fast with clear errors.
    - `docs/testing_plan.md` is updated where test contract expectations changed.
