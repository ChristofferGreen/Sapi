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

1. (none currently)

### Immediate Next 10 (After Ready Now)

1. `TODO-0253`
2. `TODO-0257`
3. `TODO-0234`
4. `TODO-0233`
5. `TODO-0266`
6. `TODO-0223`
7. `TODO-0247`
8. `TODO-0275`
9. `TODO-0258`
10. `TODO-0248`

### Priority Lanes (Current)

- P0 Foundation/contracts: (none currently)
- P1 Core product behavior: `TODO-0253`, `TODO-0257`
- P2 Social/eval/hardening: `TODO-0223` to `TODO-0231`, `TODO-0247`, `TODO-0248`, `TODO-0249`, `TODO-0250`, `TODO-0251`, `TODO-0256`, `TODO-0258`, `TODO-0263`, `TODO-0266`, `TODO-0275`
- P3 Continuous docs governance: (none currently)

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. (none currently)

Wave B (ingest + projection + lint):
1. `TODO-0253` -> `TODO-0257` -> `TODO-0234` -> `TODO-0233`

Wave C (query + social + hardening + release):
1. (none currently)
2. `TODO-0223` -> `TODO-0247` -> `TODO-0258` -> `TODO-0248` -> `TODO-0249` -> `TODO-0256` -> `TODO-0224` -> `TODO-0275` -> `TODO-0266` -> `TODO-0225`
3. `TODO-0228` -> `TODO-0251` -> `TODO-0229` -> `TODO-0230` -> `TODO-0263` -> `TODO-0260` -> `TODO-0261` -> `TODO-0250` -> `TODO-0231`

Cross-cutting docs backlog:
1. (none currently)

### Design Coverage Snapshot

| Design area | Primary TODO IDs |
| --- | --- |
| Section 1 (scope/authority/reading) | - |
| Section 2 (runtime policy + semantic loop + mock mode) | `TODO-0275` |
| Section 3 (core concepts + identity invariants) | - |
| Section 4 (repo architecture/spec ownership/versioning/capability boundaries) | - |
| Section 5 (paths/storage/IDs/registry/metadata/lint contracts) | - |
| Section 6 (wrapper UX + wrapper-to-entrypoint contract) | - |
| Section 7.1 ingest pipeline | - |
| Section 7.2 references/linking | - |
| Section 7.3 query pipeline | - |
| Section 7.4 persona catalog | - |
| Section 7.5 profile pages/history | `TODO-0224`, `TODO-0275` |
| Section 7.6 comments pipeline/rendering | `TODO-0223`, `TODO-0247`, `TODO-0258`, `TODO-0248`, `TODO-0249`, `TODO-0256`, `TODO-0275` |
| Section 7.7 comment quality harness | `TODO-0225` |
| Section 8 site/UI/static build | `TODO-0253`, `TODO-0256`, `TODO-0257`, `TODO-0233` |
| Section 9 observability/safety/runtime controls | - |
| Section 10 run envelopes/lifecycle status | `TODO-0234`, `TODO-0250` |
| Section 11 testing strategy | `TODO-0228`, `TODO-0266`, `TODO-0251`, `TODO-0229`, `TODO-0230`, `TODO-0263` |
| Section 12 reconstruction plan | `TODO-0260`, `TODO-0261` |
| Section 13 definition of done | `TODO-0231` |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | - |
| Section 4 (core data types/run envelope types) | - |
| Section 5 (path + registry contracts) | - |
| Section 6 (semantic execution engine + retry/repair) | - |
| Section 7 (transaction/rollback) | - |
| Section 8 (pipeline execution contracts) | `TODO-0275`, `TODO-0223`, `TODO-0224` |
| Section 9 (deterministic build/projection) | `TODO-0275` |
| Section 10 (relation persistence) | - |
| Section 11 (lint/warning threshold) | - |
| Section 12 (wrapper/script interfaces) | - |
| Section 13 (observability/runtime controls/safety) | - |
| Section 14 (anti-drift and PR guardrails) | - |
| Section 15 (test-plan binding) | `TODO-0228`, `TODO-0266`, `TODO-0275`, `TODO-0229`, `TODO-0230`, `TODO-0263` |
| Section 16 (change discipline) | - |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | `TODO-0228`, `TODO-0229` |
| Tier 0-3 (fast contract/failure/pipeline suites) | `TODO-0228`, `TODO-0266`, `TODO-0275` |
| Tier 4-6 (determinism/golden/live canary) | `TODO-0229` |
| Section 4-5 (CI gating matrix + command wiring) | `TODO-0230` |
| Section 6 (exit criteria gating) | `TODO-0263`, `TODO-0231` |

- [ ] TODO-0275: Enforce site-root `New` refresh exclusions for non-mutating flows
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0217, TODO-0220, TODO-0223, TODO-0224
  - scope: Enforce and test cross-flow site-root refresh policy so query/comment/profile flows do not refresh `New` unless they mutate canonical source/topic artifacts.
  - acceptance:
    - Query flow never refreshes site-root `New`.
    - Comment/profile flows only refresh site-root `New` when canonical source/topic mutation occurs.
    - Deterministic tests validate policy across ingest/query/comment/profile execution paths.
  - notes: source `design.md` Sections 2.2, 7.3, 7.5, 7.6; `low_level.md` Section 9

- [ ] TODO-0266: Implement Tier 3 comments/profiles integration test coverage
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0224, TODO-0228
  - scope: Add social-pipeline integration tests from Tier 3 after comments/profiles behaviors are implemented.
  - acceptance:
    - `tests/integration/pipelines/test_comments_pipeline.py` covers target defaults, count bounds, merge stability, and evidence snapshot behavior.
    - `tests/integration/pipelines/test_profiles_pipeline.py` covers profile outputs, history updates, and run/lint metadata.
    - Tier 3 social tests run in deterministic mock-LLM mode and are included in PR-required suites.
  - notes: source `testing_plan.md` Tier 3; `design.md` Sections 7.5, 7.6

- [ ] TODO-0263: Enforce testing-plan exit criteria gates before DoD closure
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0266, TODO-0229, TODO-0230
  - scope: Implement explicit checks for testing-plan exit criteria and block DoD completion when any test-gate condition is open.
  - acceptance:
    - Verification step asserts PR-required tiers are green and determinism checks have passing evidence.
    - Verification step enforces no rollback/leak regressions and no deferred-build backlog before DoD.
    - `TODO-0231` cannot be marked complete while any exit-criteria gate fails.
  - notes: source `testing_plan.md` Section 6; `design.md` Sections 11, 13

- [ ] TODO-0261: Enforce MVP Slice B exit gates before social/full hardening handoff
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0260, TODO-0217, TODO-0228, TODO-0229
  - scope: Convert MVP Slice B exit criteria into explicit verification checks and block downstream milestone closure until all pass.
  - acceptance:
    - Slice B reliability/determinism/operator-usability exit criteria are represented as verifiable checks.
    - Checks run in CI or scripted local verification path with evidence artifacts.
    - Slice B cannot be marked complete while any gate remains open.
  - notes: source `design.md` Section 12.1

- [ ] TODO-0260: Enforce MVP Slice A exit gates for first end-to-end vertical slice
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0209, TODO-0214, TODO-0216, TODO-0220, TODO-0219
  - scope: Convert MVP Slice A exit criteria into explicit checks with evidence requirements.
  - acceptance:
    - One-source end-to-end path (`create site/space -> ingest -> build -> query -> validate`) is executed and captured.
    - Semantic outputs and run-envelope requirements for ingest/query are validated against contracts.
    - Deferred-build backlog check for Slice A runs is automated and enforced.
  - notes: source `design.md` Section 12.1

- [ ] TODO-0258: Implement rebuttal-steelman and claim-badge rendering contracts for comments
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0247
  - scope: Enforce rebuttal structure and claim-badge vocabulary rules in generated/normalized/rendered comments.
  - acceptance:
    - Rebuttal turns include strongest-opposing-point acknowledgment before rebuttal text.
    - Claim-badge status vocabulary is constrained to contract values with deterministic fallback behavior.
    - Rendering and validation tests cover badge/status consistency and rebuttal formatting.
  - notes: source `design.md` Section 7.6

- [ ] TODO-0256: Implement comment moderator/outcome blocks and deterministic social-vote rendering
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0247, TODO-0233
  - scope: Implement moderator checks, outcome summaries, and deterministic social-vote/permalink behavior for rendered comment threads.
  - acceptance:
    - Moderator check keys and outcome sections are generated per contract.
    - Deterministic social-vote rendering uses stable inputs and preserves repeatable output.
    - Thread permalinks/expansion state remain keyed by `comment_uid`.
  - notes: source `design.md` Sections 7.6, 8

- [ ] TODO-0253: Implement navigation/tabs/feed/pagination information-architecture contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216
  - scope: Implement deterministic navigation/sidebar/tab/feed/search/pagination behavior and scope-aware users tab behavior.
  - acceptance:
    - Sidebar hierarchy, space switcher, tab set, and page-size behavior match contract.
    - Feed ordering, tie-break rules, and pagination URL semantics are deterministic.
    - Users-tab scope behavior (site vs space) and space-scoped profile link resolution are implemented.
  - notes: source `design.md` Section 8

- [ ] TODO-0257: Implement source-preview asset pipeline and page/feed integration
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0210, TODO-0216, TODO-0253
  - scope: Implement deterministic source-preview asset generation and integration into source/detail/feed views.
  - acceptance:
    - Source preview assets are generated under canonical site asset path with deterministic naming.
    - Source detail and optional feed-row integrations render preview assets per contract.
    - Preview generation/integration is deterministic and covered by snapshot tests.
  - notes: source `design.md` Section 8 (historical source preview assets)

- [ ] TODO-0250: Implement run-truth advancement and reconciliation-state semantics
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0206, TODO-0214, TODO-0220, TODO-0223, TODO-0224
  - scope: Implement run-truth rules so only successful runs advance reconciliation/verification state across pipelines.
  - acceptance:
    - Only `success` and `success_with_warnings` runs advance reconciliation state.
    - `failed` and `aborted` runs are excluded from consecutive-run resolution logic.
    - Advancement behavior is tested for ingest/query/comment/profile pipelines.
  - notes: source `design.md` Section 10

- [ ] TODO-0251: Preserve historical test-footprint contracts and golden asset layout
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0228
  - scope: Implement and verify historical testing-footprint expectations that should remain part of reconstruction quality signal.
  - acceptance:
    - Legacy broad `tests/test_*.py` footprint equivalents are represented in modernized test layout.
    - Golden snapshot directories for site and skill assets are created and wired to CI test commands.
    - High-value historical test intents from Section 11 are mapped to concrete tests/modules.
  - notes: source `design.md` Section 11

- [ ] TODO-0249: Implement comment generation-isolation and adjudication summary contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223
  - scope: Implement anti-gaming generation isolation checks and adjudication summary outputs for comment runs.
  - acceptance:
    - Comment-generation prompts/context do not expose adjudication rubric internals.
    - Generation-isolation metadata uses canonical marker/schema version and leak counters.
    - Adjudication summary fields (`rubric_id`, checks, failures) are emitted in projection/run outputs.
  - notes: source `design.md` Sections 7.6, 7.7

- [ ] TODO-0248: Implement discussion-controls precedence and canonical metadata integration
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0236
  - scope: Implement discussion-controls loading and precedence (`defaults -> per-page controls -> canonical page metadata`) with compatibility readers.
  - acceptance:
    - Site controls are read from canonical file/schema and fallback safely when missing/invalid.
    - Canonical page JSON metadata overrides frontmatter when both are present.
    - New writes target canonical page JSON metadata, not markdown frontmatter.
  - notes: source `design.md` Section 7.6

- [ ] TODO-0247: Implement comment turn-marker normalization and turn-schema validation
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0211
  - scope: Implement canonical turn-marker handling and strict/social turn validation rules for comment rows.
  - acceptance:
    - Canonical marker `<<turn:{...}>>` is supported; legacy marker compatibility is normalized.
    - Argumentative turns enforce required claim/evidence/confidence constraints.
    - Social turns are validated under lightweight rules and rejected when they include unclassified factual claims.
  - notes: source `design.md` Section 7.6


- [ ] TODO-0234: Implement topic lifecycle transitions and final-page contradiction gating
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216, TODO-0218
  - scope: Implement lifecycle state transitions and contradiction handling gates for topic publication.
  - acceptance:
    - Lifecycle states/transitions match contract including manual-only finalization/demotion paths.
    - `final_disputed_contradiction` blocks publication workflows without auto-demoting final pages.
    - Manual remediation flow via lifecycle command is supported and auditable.
  - notes: source `design.md` Sections 5.8, 10

- [ ] TODO-0233: Implement UI information architecture and rendering contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0253
  - scope: Integrate and validate UI/IA renderer contracts end-to-end after specialized Section 8 tasks land.
  - acceptance:
    - Section 8 specialized contract tasks produce coherent, non-conflicting site output across page types.
    - Cross-page navigation/search/feed behavior is consistent after integrating all specialized renderers.
    - Final integration pass closes known UI contract gaps and regressions with snapshot evidence.
  - notes: source `design.md` Section 8

- [ ] TODO-0231: Definition-of-Done sweep and release readiness verification
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0229, TODO-0230, TODO-0243
  - scope: Execute final DoD verification across wrappers, runtime behavior, deferred-build backlog, and contract tests before first implementation milestone is considered complete.
  - acceptance:
    - All wrapper commands in DoD execute successfully on a representative site/space.
    - No runs remain with `build_deferred: true`.
    - DoD bullets from `docs/design.md` Section 13 are checked explicitly with evidence links.
  - notes: source `design.md` Section 13

- [ ] TODO-0230: CI matrix and test execution wiring
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0229
  - scope: Wire test tiers to PR/nightly jobs exactly as specified in the testing checklist.
  - acceptance:
    - PR CI runs required tiers (Tier 1-3).
    - Nightly CI runs Tier 4-6.
    - `live_llm` marker is excluded from default PR jobs and included only where intended.
  - notes: source `testing_plan.md` Sections 4-5

- [ ] TODO-0229: Tier 4-6 determinism, golden, and live-canary tests
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0266, TODO-0216, TODO-0220, TODO-0223
  - scope: Implement slower determinism/golden/live checks after core pipelines are stable.
  - acceptance:
    - Tier 4 tests cover deterministic rebuild and incremental/full equivalence.
    - Tier 5 snapshots exist for site/query/run envelope outputs.
    - Tier 6 live canary exists and is non-blocking.
  - notes: source `testing_plan.md` Tier 4-6

- [ ] TODO-0228: Tier 0-2 plus ingest/query Tier 3 foundational test implementation
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0204, TODO-0205, TODO-0206, TODO-0220
  - scope: Implement unit/failure tests and initial deterministic Tier 3 ingest/query integration coverage for core contracts.
  - acceptance:
    - Tier 0 harness fixtures are present.
    - Tier 1 contract tests pass including ID/time formats and semantic-flow cardinality.
    - Tier 2 rollback/failure semantics tests pass.
    - Tier 3 ingest/query integration tests pass in mock LLM mode.
  - notes: source `design.md` Section 11; `testing_plan.md` Tier 0-3

- [ ] TODO-0225: Comment quality benchmark and evaluation manifest pipeline
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223
  - scope: Implement benchmark scoring and evaluation manifest generation for comment quality checks.
  - acceptance:
    - Benchmark artifact and schema contracts are implemented.
    - Evaluation manifest writes to `outputs/comment_quality/<evaluation_id>/manifest.json`.
    - Threshold pass/fail and fail reasons are persisted deterministically.
  - notes: source `design.md` Section 7.7

- [ ] TODO-0224: Persona profile generation and space-local accountability history
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0222, TODO-0223, TODO-0216
  - scope: Implement profile semantic flow, canonical profile writes, and history update semantics per space.
  - acceptance:
    - Profiles write to `profiles/persona-<persona_id>.json`.
    - History writes to `outputs/persona_profile_history/<persona_id>.json` with same-day/new-day semantics.
    - Profile/page projection stats and run-envelope fields are emitted.
  - notes: source `design.md` Section 7.5

- [ ] TODO-0223: Comment pipeline batching, merge normalization, and evidence modes
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0222, TODO-0216, TODO-0204, TODO-0218
  - scope: Implement comment generation contract including per-page semantic artifacts, count bounds, merge behavior, and evidence snapshots.
  - acceptance:
    - Default targets parseable topic pages; explicit source/claim targeting works.
    - One semantic artifact per targeted page is written under `runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json`.
    - Merge preserves existing `comment_uid` values and assigns only for new comments.
    - `web-augmented` mode writes snapshot at canonical path/schema.
  - notes: source `design.md` Section 7.6
