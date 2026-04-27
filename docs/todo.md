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

1. TODO-0340 - Define canonical source revision contracts

### Immediate Next 10 (After Ready Now)

1. TODO-0341 - Persist source revision families and explicit ingest links
2. TODO-0342 - Add certain-only LLM source revision detection
3. TODO-0343 - Render source revision history on source pages
4. TODO-0344 - Add revision ingestion validation and quality coverage

### Priority Lanes (Current)

- P0 Foundation/contracts: TODO-0340
- P1 Core product behavior: TODO-0341, TODO-0342, TODO-0343
- P2 Social/eval/hardening: TODO-0344
- P3 Continuous docs governance: (none currently)

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. TODO-0340 - Define canonical source revision contracts

Wave B (ingest + projection + lint):
1. TODO-0341 - Persist source revision families and explicit ingest links
2. TODO-0342 - Add certain-only LLM source revision detection
3. TODO-0343 - Render source revision history on source pages

Wave C (query + social + hardening + release):
1. TODO-0344 - Add revision ingestion validation and quality coverage

Wave D (space/subspace AI overview article):
1. (none currently)

Cross-cutting docs backlog:
1. (none currently)

### Design Coverage Snapshot

| Design area | Primary TODO IDs |
| --- | --- |
| Section 1 (scope/authority/reading) | - |
| Section 2 (runtime policy + semantic loop + mock mode) | - |
| Section 3 (core concepts + identity invariants) | TODO-0340, TODO-0341 |
| Section 4 (repo architecture/spec ownership/versioning/capability boundaries) | TODO-0340, TODO-0342 |
| Section 5 (paths/storage/IDs/registry/metadata/lint contracts) | TODO-0340, TODO-0341 |
| Section 6 (wrapper UX + wrapper-to-entrypoint contract) | TODO-0341 |
| Section 7.1 ingest pipeline | TODO-0341, TODO-0342, TODO-0344 |
| Section 7.2 references/linking | - |
| Section 7.3 query pipeline | - |
| Section 7.4 persona catalog | - |
| Section 7.5 profile pages/history | - |
| Section 7.6 comments pipeline/rendering | - |
| Section 7.7 comment quality harness | - |
| Section 8 site/UI/static build | TODO-0343 |
| Section 9 observability/safety/runtime controls | TODO-0342, TODO-0344 |
| Section 10 run envelopes/lifecycle status | TODO-0342, TODO-0344 |
| Section 11 testing strategy | TODO-0344 |
| Section 12 reconstruction plan | - |
| Section 13 definition of done | - |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | TODO-0342 |
| Section 4 (core data types/run envelope types) | TODO-0340, TODO-0342 |
| Section 5 (path + registry contracts) | TODO-0340, TODO-0341 |
| Section 6 (semantic execution engine + retry/repair) | TODO-0342 |
| Section 7 (transaction/rollback) | TODO-0341, TODO-0344 |
| Section 8 (pipeline execution contracts) | TODO-0341, TODO-0342 |
| Section 9 (deterministic build/projection) | TODO-0343 |
| Section 10 (relation persistence) | - |
| Section 11 (lint/warning threshold) | - |
| Section 12 (wrapper/script interfaces) | TODO-0341 |
| Section 13 (observability/runtime controls/safety) | TODO-0342, TODO-0344 |
| Section 14 (anti-drift and PR guardrails) | TODO-0344 |
| Section 15 (test-plan binding) | TODO-0344 |
| Section 16 (change discipline) | - |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | TODO-0344 |
| Tier 0-3 (fast contract/failure/pipeline suites) | TODO-0340, TODO-0341, TODO-0342, TODO-0343, TODO-0344 |
| Tier 4-6 (determinism/golden/live canary) | TODO-0342, TODO-0344 |
| Section 4-5 (CI gating matrix + command wiring) | TODO-0344 |
| Section 6 (exit criteria gating) | TODO-0344 |

### Task Blocks

- [ ] TODO-0344: Add revision ingestion validation and quality coverage
  - owner: ai
  - created_at: 2026-04-27
  - phase: Cross-cutting
  - depends_on: TODO-0340, TODO-0341, TODO-0342, TODO-0343
  - scope: Add focused tests and validation coverage that prove source revision ingest behavior is transactional, observable, and quality-gated.
  - acceptance:
    - Unit and integration tests cover explicit revision ingest, auto-detected revision ingest, uncertain detection becoming a new source, rollback of revised records/manifests, and source page revision rendering.
    - Run-envelope or semantic invocation assertions distinguish explicit CLI revision linking from LLM revision detection and verify explicit linking does not invoke the detection flow.
    - A live or replayable quality check exercises the revision-detection prompt against at least one positive revision pair and one near-miss pair.
    - Documentation and tests make clear that uncertain LLM output must never merge sources into the same revision family.
  - notes: source revision feature hardening; covers ingest, semantic runtime, rollback, and static site output.

- [ ] TODO-0343: Render source revision history on source pages
  - owner: ai
  - created_at: 2026-04-27
  - phase: Phase 5
  - depends_on: TODO-0341
  - scope: Update the deterministic site builder so each source page lists other revisions in the same source family without synthesizing semantic content.
  - acceptance:
    - Source pages with a `source_family_id` render a revision history section listing every known revision, including current and latest state.
    - Revision entries link to the corresponding source pages and display deterministic metadata from source records only.
    - Source pages with no revision family or a single-member family do not show an empty revision section.
    - Site-builder tests verify ordering, labels, links, and no-section behavior for singleton sources.
  - notes: deterministic rendering is allowed here because it only displays stored source metadata and links.

- [ ] TODO-0342: Add certain-only LLM source revision detection
  - owner: ai
  - created_at: 2026-04-27
  - phase: Phase 5
  - depends_on: TODO-0340, TODO-0341
  - scope: Add an optional semantic flow that decides whether a newly ingested document is certainly a revision of an existing source when the user did not explicitly specify a revision target.
  - acceptance:
    - A canonical `source_revision_detection` semantic flow, schema, generation spec, and run-envelope key are registered.
    - Ingest selects bounded candidate existing sources for prompt size only; deterministic candidate scoring never merges sources or creates a semantic revision judgment.
    - The detection prompt defaults to the new and candidate `source.md` artifacts plus `source_extraction.json` metadata, and only asks the model to inspect the original PDF/binary when markdown quality is degraded or insufficient.
    - Ingest invokes the detection flow only when candidates exist and links as a revision only when the model returns a schema-valid certain revision decision for one candidate.
    - Uncertain, negative, invalid, or non-candidate decisions leave the new document as an independent source.
    - Mock mode and deterministic code paths do not fabricate user-facing revision decisions.
    - Semantic invocation accounting includes the optional detection flow only when it actually runs.
  - notes: this flow must preserve the project guarantee that deterministic code never creates user-facing semantic judgments.

- [ ] TODO-0341: Persist source revision families and explicit ingest links
  - owner: ai
  - created_at: 2026-04-27
  - phase: Phase 5
  - depends_on: TODO-0340
  - scope: Implement canonical storage and CLI behavior for source revisions when the operator explicitly declares that a new ingest revises an existing source.
  - acceptance:
    - Source records can store canonical revision-family metadata, including family id, revision order, latest status, supersedes, and superseded-by relationships.
    - Ingest supports an explicit `--revises-source-id` operator input through the direct entrypoint and repo-root helper path, and this path skips LLM revision detection.
    - `--revises-source-id` and existing `--source-family-id` behavior have a documented precedence or fail-fast conflict rule, with tests for the chosen rule.
    - Revision family manifests are written under a canonical path and updated transactionally with affected source records.
    - Missing, malformed, self-referential, or cross-space revision targets fail fast before semantic ingest output is committed.
    - Existing source records without revision metadata remain valid and continue to ingest/build unchanged.
  - notes: explicit operator input is authoritative and does not require model judgment.

- [ ] TODO-0340: Define canonical source revision contracts
  - owner: ai
  - created_at: 2026-04-27
  - phase: Cross-cutting
  - scope: Specify the source revision/version data model before implementation, including source record fields, revision family manifests, ingest behavior, and source-page rendering requirements.
  - acceptance:
    - `docs/design.md` defines source revisions, revision families, explicit operator revision input, LLM-assisted certain-only detection, and the new-source fallback rule.
    - `docs/low_level.md` defines storage paths, source record keys, manifest shape, transaction expectations, semantic flow ownership, and wrapper/entrypoint contracts.
    - The contract separates deterministic candidate shortlisting from semantic revision judgment and requires markdown-first source reading for any model-based revision decision.
    - The contract identifies which follow-up TODO owns each runtime, schema/spec, rendering, and validation change so implementation tasks do not overlap.
    - The contract states that only a certain model decision or explicit CLI input may merge a new ingest into an existing source family.
  - notes: source versioning should preserve backward compatibility for existing single-version sources.
