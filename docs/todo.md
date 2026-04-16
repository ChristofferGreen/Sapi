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

1. `TODO-0313`

### Immediate Next 10 (After Ready Now)

1. TODO-0314
2. TODO-0315
3. TODO-0316
4. TODO-0317
5. TODO-0318
6. TODO-0319
7. TODO-0320
8. TODO-0321
9. TODO-0322
10. TODO-0323

### Priority Lanes (Current)

- P0 Foundation/contracts: TODO-0313, TODO-0317, TODO-0318, TODO-0319, TODO-0324, TODO-0325
- P1 Core product behavior: TODO-0314, TODO-0315, TODO-0316
- P2 Social/eval/hardening: TODO-0320, TODO-0321, TODO-0322, TODO-0323, TODO-0326, TODO-0327
- P3 Continuous docs governance: TODO-0313, TODO-0327

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. TODO-0313
2. TODO-0317
3. TODO-0318
4. TODO-0319
5. TODO-0324
6. TODO-0325
7. TODO-0326

Wave B (ingest + projection + lint):
1. TODO-0314
2. TODO-0315
3. TODO-0316

Wave C (query + social + hardening + release):
1. TODO-0320
2. TODO-0321
3. TODO-0322
4. TODO-0323

Cross-cutting docs backlog:
1. TODO-0327

### Design Coverage Snapshot

| Design area | Primary TODO IDs |
| --- | --- |
| Section 1 (scope/authority/reading) | - |
| Section 2 (runtime policy + semantic loop + mock mode) | TODO-0313 |
| Section 3 (core concepts + identity invariants) | TODO-0318, TODO-0319 |
| Section 4 (repo architecture/spec ownership/versioning/capability boundaries) | TODO-0313, TODO-0317 |
| Section 5 (paths/storage/IDs/registry/metadata/lint contracts) | - |
| Section 6 (wrapper UX + wrapper-to-entrypoint contract) | TODO-0314, TODO-0315, TODO-0316 |
| Section 7.1 ingest pipeline | TODO-0314 |
| Section 7.2 references/linking | - |
| Section 7.3 query pipeline | - |
| Section 7.4 persona catalog | TODO-0319 |
| Section 7.5 profile pages/history | - |
| Section 7.6 comments pipeline/rendering | TODO-0315, TODO-0316, TODO-0320, TODO-0321, TODO-0322, TODO-0323 |
| Section 7.7 comment quality harness | - |
| Section 8 site/UI/static build | - |
| Section 9 observability/safety/runtime controls | - |
| Section 10 run envelopes/lifecycle status | - |
| Section 11 testing strategy | - |
| Section 12 reconstruction plan | - |
| Section 13 definition of done | - |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | - |
| Section 4 (core data types/run envelope types) | TODO-0318, TODO-0319 |
| Section 5 (path + registry contracts) | TODO-0324, TODO-0325 |
| Section 6 (semantic execution engine + retry/repair) | TODO-0317 |
| Section 7 (transaction/rollback) | - |
| Section 8 (pipeline execution contracts) | TODO-0314, TODO-0315, TODO-0316, TODO-0320, TODO-0321, TODO-0322, TODO-0323 |
| Section 9 (deterministic build/projection) | - |
| Section 10 (relation persistence) | TODO-0326 |
| Section 11 (lint/warning threshold) | - |
| Section 12 (wrapper/script interfaces) | TODO-0314, TODO-0315, TODO-0316 |
| Section 13 (observability/runtime controls/safety) | - |
| Section 14 (anti-drift and PR guardrails) | - |
| Section 15 (test-plan binding) | TODO-0327 |
| Section 16 (change discipline) | - |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | TODO-0327 |
| Tier 0-3 (fast contract/failure/pipeline suites) | TODO-0314, TODO-0315, TODO-0316, TODO-0317, TODO-0318, TODO-0319, TODO-0320, TODO-0321, TODO-0322, TODO-0323, TODO-0324, TODO-0325, TODO-0326 |
| Tier 4-6 (determinism/golden/live canary) | - |
| Section 4-5 (CI gating matrix + command wiring) | TODO-0313, TODO-0327 |
| Section 6 (exit criteria gating) | - |

### Task Blocks

- [ ] TODO-0327: Purge compatibility/deprecation tests and add strict no-legacy coverage
  - owner: ai
  - created_at: 2026-04-13
  - phase: Cross-cutting
  - depends_on: TODO-0313, TODO-0314, TODO-0315, TODO-0316, TODO-0317, TODO-0318, TODO-0319, TODO-0320, TODO-0321, TODO-0322, TODO-0323, TODO-0324, TODO-0325, TODO-0326
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

- [ ] TODO-0325: Remove site-scope legacy fallback reader (`<space_root>/site.json`)
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove `allow_legacy_space_scope_read` behavior from site-scope loading and enforce canonical `<site_path>/site.json` only.
  - acceptance:
    - `sapi/core/site_scope.py` no longer contains legacy fallback branch/flag.
    - Site-scope tests assert missing canonical file fails without legacy fallback mode.

- [ ] TODO-0324: Remove registry entry compatibility key `name`
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Stop accepting historical registry key `name`; require `space_name` only.
  - acceptance:
    - `sapi/core/registry.py` rejects registry entries without `space_name`.
    - Registry tests cover rejection of `name`-only entries.

- [ ] TODO-0323: Remove legacy parent reference alias `pc-###`
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove ordinal parent-reference compatibility in comment normalization.
  - acceptance:
    - `sapi/comments/merge_normalize.py` no longer resolves `pc-###` as parent refs.
    - Comment merge tests assert legacy ordinal parent refs fail validation.

- [ ] TODO-0322: Remove rebuttal-field alias `steelman_before_rebuttal`
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Enforce only canonical rebuttal field `strongest_opposing_point_ack`.
  - acceptance:
    - Comment normalization rejects `steelman_before_rebuttal`.
    - Tests and contracts use only canonical rebuttal field naming.

- [ ] TODO-0321: Remove legacy HTML turn-marker compatibility
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove support for `<!-- turn:{...} -->` marker format and allow only canonical `<<turn:{...}>>`.
  - acceptance:
    - `sapi/comments/merge_normalize.py` parses only canonical inline marker.
    - Tests assert legacy marker usage fails fast.

- [ ] TODO-0320: Remove discussion-controls legacy aliases and frontmatter fallback
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove `persona_discussion_*` key/schema aliases and remove canonical-page fallback to legacy frontmatter controls.
  - acceptance:
    - `sapi/comments/controls.py` accepts only canonical schema/key names.
    - Legacy frontmatter-only controls are no longer imported into effective/canonical controls.
    - Tests and docs reflect canonical-only controls behavior.

- [ ] TODO-0319: Remove persona/topic identity legacy aliases (`id`, `narrative_id`)
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove compatibility aliases `Persona.id` and `TopicPage.narrative_id`, and remove loader mapping from persona row `id` to `persona_id`.
  - acceptance:
    - `sapi/contracts/domain_models.py` enforces canonical identity keys only.
    - `sapi/profiles/persona_catalog.py` requires explicit `persona_id`; `id` alias mapping is removed.
    - Tests and docs no longer rely on `id`/`narrative_id` aliases.

- [ ] TODO-0318: Remove direct-script compatibility aliases for comments entrypoint
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove hidden CLI alias inputs in `scripts/create_comments.py` (`--user`, `--page`, `--comment-web-evidence`).
  - acceptance:
    - Parser no longer accepts deprecated alias flags.
    - Evidence mode is controlled only by canonical `--comment-evidence-mode`.
    - Script-level tests assert alias flags fail as unknown arguments.

- [ ] TODO-0317: Remove semantic flow-key compatibility alias `persona_comment_generation`
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove flow alias normalization/deprecation path and require canonical `comment_section_generation`.
  - acceptance:
    - `sapi/contracts/semantic_specs.py` no longer contains `FLOW_ALIAS_MAP` compatibility alias for comment flow.
    - Resolution tests assert alias keys fail as unknown flow keys.

- [ ] TODO-0316: Remove wrapper-level compatibility aliases in `create_comments.sh`
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove wrapper normalization for legacy positional count and aliases `--user`/`--page`; accept only canonical flags.
  - acceptance:
    - `create_comments.sh` accepts only `--count`, `--comment-user`, and `--comment-page`.
    - Wrapper tests assert legacy positional count and alias flags fail fast.

- [ ] TODO-0315: Remove ingest wrapper/entrypoint alias `--query-only`
  - owner: ai
  - created_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove deprecated ingest alias `--query-only` from wrapper and Python entrypoint.
  - acceptance:
    - `ingest.sh` and `scripts/ingest_source.py` reject both `--query-only` and `--source-only`.
    - Tests assert removed ingest mode flags fail as invalid input.

- [ ] TODO-0314: Remove compatibility-reader sunset policy and alias acceptance language from contracts
  - owner: ai
  - created_at: 2026-04-13
  - phase: Cross-cutting
  - depends_on: TODO-0313
  - scope: Update `docs/design.md` and `docs/low_level.md` so contracts are canonical-only and no longer permit compatibility alias acceptance.
  - acceptance:
    - Design/low-level docs remove compatibility alias acceptance policy and deprecation wording for removed paths.
    - Contract tests are updated to canonical-only assertions.

- [ ] TODO-0313: Compatibility purge tracker for canonical-only boundary
  - owner: ai
  - created_at: 2026-04-13
  - phase: Cross-cutting
  - scope: Track complete removal of legacy/backward-compatibility behaviors across wrappers, semantic flow keys, domain models, comment controls/markers, registry/site scope, and relation status handling.
  - acceptance:
    - All compatibility pathways enumerated in TODO-0314..TODO-0327 are represented in discrete tasks.
    - Queue/coverage snapshots in this file are synchronized to those tasks.
