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

1. `TODO-0211` Ingest extraction semantic flow and canonical claim/relation writes

### Immediate Next 10 (After Ready Now)

1. `TODO-0211`
2. `TODO-0213`
3. `TODO-0212`
4. `TODO-0214`
5. `TODO-0215`
6. `TODO-0216`
7. `TODO-0217`
8. `TODO-0218`
9. `TODO-0219`
10. `TODO-0220`

### Priority Lanes (Current)

- P0 Foundation/contracts: (none currently)
- P1 Core product behavior: `TODO-0211` to `TODO-0221`, `TODO-0242`, `TODO-0244`, `TODO-0245`, `TODO-0246`, `TODO-0252`, `TODO-0253`, `TODO-0255`, `TODO-0257`, `TODO-0259`, `TODO-0268`, `TODO-0270`, `TODO-0271`, `TODO-0273`, `TODO-0276`, `TODO-0277`, `TODO-0278`
- P2 Social/eval/hardening: `TODO-0222` to `TODO-0231`, `TODO-0243`, `TODO-0247`, `TODO-0248`, `TODO-0249`, `TODO-0250`, `TODO-0251`, `TODO-0254`, `TODO-0256`, `TODO-0258`, `TODO-0263`, `TODO-0266`, `TODO-0267`, `TODO-0274`, `TODO-0275`
- P3 Continuous docs governance: `TODO-0280`, `TODO-0281`, `TODO-0264`, `TODO-0265`

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. (none currently)

Wave B (ingest + projection + lint):
1. `TODO-0211` -> `TODO-0213` -> `TODO-0278` -> `TODO-0212` -> `TODO-0214` -> `TODO-0270` -> `TODO-0271`
2. `TODO-0215` -> `TODO-0216` -> `TODO-0268` -> `TODO-0217` -> `TODO-0218`
3. `TODO-0246` -> `TODO-0245` -> `TODO-0244` -> `TODO-0253` -> `TODO-0252` -> `TODO-0257` -> `TODO-0234` -> `TODO-0233` -> `TODO-0219`

Wave C (query + social + hardening + release):
1. `TODO-0220` -> `TODO-0242` -> `TODO-0259` -> `TODO-0255` -> `TODO-0221` -> `TODO-0277` -> `TODO-0273` -> `TODO-0276`
2. `TODO-0222` -> `TODO-0223` -> `TODO-0247` -> `TODO-0258` -> `TODO-0248` -> `TODO-0249` -> `TODO-0256` -> `TODO-0224` -> `TODO-0275` -> `TODO-0266` -> `TODO-0267` -> `TODO-0225` -> `TODO-0274`
3. `TODO-0254` -> `TODO-0228` -> `TODO-0251` -> `TODO-0229` -> `TODO-0230` -> `TODO-0263` -> `TODO-0243` -> `TODO-0260` -> `TODO-0261` -> `TODO-0250` -> `TODO-0231`

Cross-cutting docs backlog:
1. `TODO-0265` -> `TODO-0264` -> `TODO-0243`
2. `TODO-0280` -> `TODO-0281`

### Design Coverage Snapshot

| Design area | Primary TODO IDs |
| --- | --- |
| Section 1 (scope/authority/reading) | `TODO-0243`, `TODO-0280`, `TODO-0281` |
| Section 2 (runtime policy + semantic loop + mock mode) | `TODO-0214`, `TODO-0246`, `TODO-0275` |
| Section 3 (core concepts + identity invariants) | - |
| Section 4 (repo architecture/spec ownership/versioning/capability boundaries) | `TODO-0242` |
| Section 5 (paths/storage/IDs/registry/metadata/lint contracts) | `TODO-0218` |
| Section 6 (wrapper UX + wrapper-to-entrypoint contract) | `TODO-0219`, `TODO-0268`, `TODO-0267`, `TODO-0273`, `TODO-0274`, `TODO-0276` |
| Section 7.1 ingest pipeline | `TODO-0211`, `TODO-0212`, `TODO-0213`, `TODO-0214`, `TODO-0270`, `TODO-0271`, `TODO-0278` |
| Section 7.2 references/linking | `TODO-0215` |
| Section 7.3 query pipeline | `TODO-0220`, `TODO-0259`, `TODO-0255`, `TODO-0221`, `TODO-0277` |
| Section 7.4 persona catalog | `TODO-0222` |
| Section 7.5 profile pages/history | `TODO-0224`, `TODO-0275` |
| Section 7.6 comments pipeline/rendering | `TODO-0223`, `TODO-0247`, `TODO-0258`, `TODO-0248`, `TODO-0249`, `TODO-0256`, `TODO-0275`, `TODO-0274` |
| Section 7.7 comment quality harness | `TODO-0225` |
| Section 8 site/UI/static build | `TODO-0216`, `TODO-0268`, `TODO-0217`, `TODO-0245`, `TODO-0244`, `TODO-0253`, `TODO-0252`, `TODO-0256`, `TODO-0257`, `TODO-0233` |
| Section 9 observability/safety/runtime controls | `TODO-0226`, `TODO-0227`, `TODO-0254` |
| Section 10 run envelopes/lifecycle status | `TODO-0234`, `TODO-0250` |
| Section 11 testing strategy | `TODO-0228`, `TODO-0266`, `TODO-0267`, `TODO-0270`, `TODO-0271`, `TODO-0273`, `TODO-0274`, `TODO-0276`, `TODO-0277`, `TODO-0278`, `TODO-0251`, `TODO-0229`, `TODO-0230`, `TODO-0263` |
| Section 12 reconstruction plan | `TODO-0243`, `TODO-0260`, `TODO-0261` |
| Section 13 definition of done | `TODO-0231`, `TODO-0273`, `TODO-0274`, `TODO-0276` |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | `TODO-0214` |
| Section 4 (core data types/run envelope types) | - |
| Section 5 (path + registry contracts) | `TODO-0218` |
| Section 6 (semantic execution engine + retry/repair) | - |
| Section 7 (transaction/rollback) | `TODO-0214` |
| Section 8 (pipeline execution contracts) | `TODO-0270`, `TODO-0271`, `TODO-0273`, `TODO-0274`, `TODO-0275`, `TODO-0276`, `TODO-0277`, `TODO-0278`, `TODO-0220`, `TODO-0223`, `TODO-0224`, `TODO-0242` |
| Section 9 (deterministic build/projection) | `TODO-0216`, `TODO-0217`, `TODO-0246`, `TODO-0275` |
| Section 10 (relation persistence) | `TODO-0213`, `TODO-0278` |
| Section 11 (lint/warning threshold) | `TODO-0218`, `TODO-0219` |
| Section 12 (wrapper/script interfaces) | `TODO-0219`, `TODO-0254`, `TODO-0268`, `TODO-0267`, `TODO-0273`, `TODO-0274`, `TODO-0276` |
| Section 13 (observability/runtime controls/safety) | `TODO-0226`, `TODO-0227`, `TODO-0254` |
| Section 14 (anti-drift and PR guardrails) | `TODO-0265`, `TODO-0264` |
| Section 15 (test-plan binding) | `TODO-0228`, `TODO-0266`, `TODO-0267`, `TODO-0270`, `TODO-0271`, `TODO-0275`, `TODO-0276`, `TODO-0277`, `TODO-0278`, `TODO-0229`, `TODO-0230`, `TODO-0263` |
| Section 16 (change discipline) | `TODO-0264`, `TODO-0243` |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | `TODO-0228`, `TODO-0267`, `TODO-0276`, `TODO-0229` |
| Tier 0-3 (fast contract/failure/pipeline suites) | `TODO-0228`, `TODO-0266`, `TODO-0267`, `TODO-0270`, `TODO-0271`, `TODO-0273`, `TODO-0274`, `TODO-0275`, `TODO-0276`, `TODO-0277`, `TODO-0278` |
| Tier 4-6 (determinism/golden/live canary) | `TODO-0229` |
| Section 4-5 (CI gating matrix + command wiring) | `TODO-0230` |
| Section 6 (exit criteria gating) | `TODO-0263`, `TODO-0231` |

- [ ] TODO-0281: Define default `evaluate_source.sh` query-mode recommendation as an explicit contract task
  - owner: ai
  - created_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0280
  - scope: Convert unresolved recommendation about default query-mode coverage in `evaluate_source.sh` into an explicit tracked decision task with clear acceptance and contract target.
  - acceptance:
    - Task references the unresolved recommendation from the design decision register and assigns one owner/outcome path.
    - Acceptance criteria require explicit contract destination in `design.md` Section 6.3 once resolved.
    - Task notes link to the authoritative recommendation source section.
  - notes: source `design.md` Section 1.3 (decision register), Section 6.3; decision_ref: additional-query-modes-in-evaluate-source-sh-default-evaluation-pack

- [ ] TODO-0280: Define compatibility-reader sunset recommendation as an explicit contract task
  - owner: ai
  - created_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: none
  - scope: Convert unresolved compatibility-reader sunset recommendation into an explicit tracked task with owner, acceptance criteria, and target contract section.
  - acceptance:
    - Task references the unresolved recommendation from the design decision register and assigns one owner/outcome path.
    - Acceptance criteria require explicit contract destination in `design.md` Section 4.1.3 once resolved.
    - Task notes link to the authoritative recommendation source section.
  - notes: source `design.md` Section 1.3 (decision register), Section 4.1.3; decision_ref: compatibility-reader-sunset-policy-for-legacy-aliases

- [ ] TODO-0278: Enforce relation-type matrix semantics and normalization invariants
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0211, TODO-0213
  - scope: Implement relation semantics beyond storage-key hashing, including type-specific canonical ID formation and normalization rules.
  - acceptance:
    - Relation ID generation follows the canonical matrix for directed/undirected relation types.
    - Undirected relations sort claim IDs lexicographically; directed relations preserve semantic source/target order.
    - Canonical relation-write normalization includes required status/field handling and deterministic merge behavior for duplicate relation IDs.
  - notes: source `design.md` Section 7.1 (relation-type matrix + normalization rules)

- [ ] TODO-0277: Enforce query result JSON shape and execution-metadata contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220, TODO-0221, TODO-0255, TODO-0259
  - scope: Implement and validate full recovered query result-shape contract including execution, warnings, and optional fields.
  - acceptance:
    - Query JSON includes required high-signal keys (`query_id`, `answer`, retrieval/falsification counters, mode/scope, run/timestamp, lint/execution blocks).
    - Optional fields (`ancestor_pages_used`, `inherited_conflicts`, `synthesis_claim_ids`) follow deterministic presence/absence rules.
    - `manifest_path` behavior is consistent with output format contract and validated by tests.
  - notes: source `design.md` Section 7.3 (query result shape + artifact output contract)

- [ ] TODO-0274: Integrate `evaluate_source.sh` comments mode and comment-review artifacts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0273, TODO-0223, TODO-0247
  - scope: Add full comments integration to the user-facing evaluation harness so reviewers can inspect generated discussion quality in markdown artifacts.
  - acceptance:
    - `evaluate_source.sh --comments <n>` invokes comment generation with canonical flags and records effective targets/counts.
    - Evaluation artifact folder includes `comments_review.md` with per-page/per-user counts and representative thread excerpts.
    - Harness preserves deterministic output layout and fails fast on invalid comments-mode arguments.
  - notes: source `design.md` Sections 6.3, 7.6, 13

- [ ] TODO-0276: Add deterministic mechanical integration tests for `evaluate_source.sh` harness
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0273
  - scope: Verify the user-facing evaluation harness contract in CI with deterministic mock-LLM runs so regressions are caught mechanically.
  - acceptance:
    - Integration test module `tests/integration/wrappers/test_evaluate_source_harness.py` validates default artifact-pack layout and required markdown outputs.
    - Tests assert `manifest.json` linkage to emitted markdown artifacts and referenced run IDs.
    - Tests cover `--comments <n>` mode and invalid comments arguments fail-fast behavior without partially committed evaluation packs.
  - notes: source `design.md` Sections 6.3, 11; `testing_plan.md` Tier 3

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

- [ ] TODO-0273: Implement `evaluate_source.sh` user-facing evaluation harness (markdown-first artifact pack)
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0200, TODO-0210, TODO-0216, TODO-0219, TODO-0220
  - scope: Implement a single operator command that runs source evaluation and emits a human-readable artifact folder for manual quality review.
  - acceptance:
    - Wrapper/entrypoint pair exists (`evaluate_source.sh` -> `scripts/evaluate_source.py`) with explicit `--registry-path` routing.
    - Default artifact pack includes `README.md`, `summary.md`, `ingest_run.md`, `lint_summary.md`, `site_links.md`, and `query_answers/strict.md`.
    - Companion machine-readable `manifest.json` indexes produced artifacts and referenced run IDs.
    - Artifact output defaults to `<space_root>/outputs/evaluations/<evaluation_id>/` and supports `--out` override.
  - notes: source `design.md` Sections 6.3, 13

- [ ] TODO-0271: Enforce ingest comment-enrichment boundary contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0214, TODO-0211
  - scope: Ensure ingest does not implicitly trigger comment generation and preserves explicit pipeline boundaries for comment enrichment.
  - acceptance:
    - Default ingest path invokes only ingest/topic semantic flows and never `comment_section_generation`.
    - Any optional enrichment path requires explicit operator opt-in and preserves Section 7.6 comment pipeline contracts.
    - Run metadata/tests verify `semantic_flows`/invocation counts remain boundary-correct for ingest modes.
  - notes: source `design.md` Sections 4.4, 7.1 (comment-enrichment policy), 7.6

- [ ] TODO-0270: Enforce ingest date/title resolution and strict-date mode contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210, TODO-0211, TODO-0214
  - scope: Implement and validate recovered ingest date/title policies, warning semantics, and strict-date behavior.
  - acceptance:
    - Source title resolution follows the five-step priority contract exactly.
    - Missing publication date behavior emits `missing_publication_date` warning and persists compliant `source_date_inference` fields.
    - `--require-source-date` strict mode fails ingest when publication date cannot be resolved.
  - notes: source `design.md` Section 7.1

- [ ] TODO-0268: Implement `regenerate_web.sh` wrapper-to-build entrypoint contract
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0209, TODO-0216, TODO-0235
  - scope: Implement and validate `regenerate_web.sh` behavior as the canonical wrapper for deterministic site build/projection entrypoints.
  - acceptance:
    - `regenerate_web.sh` dispatches to the intended build entrypoint/workflow key with explicit `--registry-path` handling for non-bootstrap execution.
    - Wrapper argument normalization and conflict handling match wrapper contract rules.
    - End-to-end wrapper invocation produces deterministic build outputs without semantic-flow execution.
  - notes: source `design.md` Sections 6.1, 8; `low_level.md` Section 12

- [ ] TODO-0267: Implement wrapper compatibility and bootstrap-exception integration tests
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0209, TODO-0235, TODO-0219, TODO-0228
  - scope: Add dedicated wrapper integration tests for alias normalization/conflicts and bootstrap registry-path exceptions.
  - acceptance:
    - Wrapper test modules cover alias normalization and canonical+alias conflict failures.
    - Bootstrap wrappers are explicitly tested for allowed missing operator-supplied `--registry-path`.
    - Non-bootstrap wrappers are tested to require explicit/effective registry-path routing.
  - notes: source `testing_plan.md` Section 2 (`tests/integration/wrappers/*`); `low_level.md` Section 12

- [ ] TODO-0265: Automate low-level anti-drift guardrails
  - owner: ai
  - created_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0102
  - scope: Convert anti-drift constraints into automated checks that fail fast when contracts drift.
  - acceptance:
    - Checks fail on implicit registry fallback, environment-variable flow controls, or duplicate schema/output ownership.
    - Checks flag query-path canonical mutations and other rejected failure patterns from guardrails.
    - Guardrail checks are wired into validation/CI path with clear failure messaging.
  - notes: source `low_level.md` Sections 14.1, 14.3

- [ ] TODO-0264: Add pipeline-change PR checklist and docs-sync discipline
  - owner: ai
  - created_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0265
  - scope: Add review checklist and contribution guardrails so pipeline-changing PRs answer the required contract questions and keep docs/code ordering disciplined.
  - acceptance:
    - PR template/checklist includes the eight required low-level review questions for pipeline changes.
    - Contribution docs enforce `design.md` -> `low_level.md` -> code change order for contract-level changes.
    - Pipeline-affecting PRs fail quality gate when checklist/docs-sync evidence is missing.
  - notes: source `low_level.md` Sections 14.2, 16

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

- [ ] TODO-0242: Enforce ingest/query capability ownership boundaries
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0201, TODO-0211, TODO-0220
  - scope: Encode capability boundaries so ingest owns canonical mutations and query remains read/synthesize-only.
  - acceptance:
    - Ingest-owned components are the only paths that mutate canonical `sources/claims/relations/topics/profiles`.
    - Query pipeline cannot write canonical knowledge artifacts by contract and tests.
    - Boundary violations fail CI through contract tests/static checks.
  - notes: source `design.md` Section 4.4

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

- [ ] TODO-0259: Implement query mode defaults and retrieval-budget policy contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220
  - scope: Implement recovered mode defaults and retrieval-budget policy behavior for strict/exploratory/comparative query execution.
  - acceptance:
    - Mode defaults for `include_disputed` are implemented exactly by mode.
    - `include_warnings` defaults to `true` unless explicitly overridden and is reflected in output metadata.
    - Retrieval budget defaults and override behavior are deterministic and auditable in outputs.
    - Invalid mode/flag combinations fail fast before retrieval/generation.
  - notes: source `design.md` Section 7.3

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

- [ ] TODO-0255: Implement query citation-coverage and deterministic truncation policies
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220, TODO-0213
  - scope: Enforce mode-specific citation coverage targets and deterministic truncation/tie-break behavior in query outputs.
  - acceptance:
    - Coverage policies for `strict`, `exploratory`, and `comparative` modes are implemented and auditable.
    - Truncation order and tie-break behavior are deterministic and consistent with contracts.
    - `omitted_due_to_budget` is populated whenever truncation occurs.
  - notes: source `design.md` Section 7.3

- [ ] TODO-0254: Implement runtime-flag surface parity and validation across wrappers/entrypoints
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0235, TODO-0226, TODO-0240
  - scope: Ensure high-signal runtime/control flags are exposed consistently, validated, and forwarded from wrappers to entrypoints.
  - acceptance:
    - Wrapper flag surface includes required runtime/tracing/testing controls with consistent behavior.
    - Invalid/unsupported flag combinations fail fast with clear errors.
    - Runtime defaults and forwarding behavior are documented and tested end-to-end.
  - notes: source `design.md` Sections 6.2, 9

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

- [ ] TODO-0252: Implement topic-page structure renderers (`wiki` and `source_mirror`)
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0212, TODO-0216
  - scope: Implement deterministic topic renderer selection and section rendering contracts for both topic structures.
  - acceptance:
    - Renderer selection between `wiki` and `source_mirror` is deterministic from topic metadata.
    - Required section ordering and content expectations are enforced for both structures.
    - Source-mirror pages preserve structural correspondence without becoming verbatim restatements.
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

- [ ] TODO-0246: Implement chained-flow coalescing and trigger-equivalence checks
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0211, TODO-0212, TODO-0216
  - scope: Implement optional ingest+topic post-processing coalescing with strict equivalence to independent trigger behavior.
  - acceptance:
    - Ingest/topic chained execution may coalesce deterministic post-processing into one final pass.
    - Coalesced output is equivalent to independent post-processing execution.
    - Tests cover trigger policy and equivalence behavior.
  - notes: source `design.md` Section 2.2

- [ ] TODO-0245: Implement cross-space pinned-link import contract and error rendering
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216, TODO-0218
  - scope: Implement cross-space topic linking via pinned imports with deterministic unresolved-link behavior.
  - acceptance:
    - Pinned parent links resolve through `imports.lock.md` snapshot entries only.
    - Unresolved pinned parent links render disabled markers and emit lint `error`.
    - Parent linkage metadata (`parent_space_name`, `parent_snapshot`, `parent_site_base_url`) persists as required.
  - notes: source `design.md` Section 8

- [ ] TODO-0244: Implement claim-reference rendering/public-debug visibility contracts
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216
  - scope: Implement claim annotation rendering behavior with auditability and metadata visibility modes.
  - acceptance:
    - HTML view avoids always-visible raw claim IDs in sentence text while preserving clickable audit access.
    - JS-off fallback includes minimal static claim-details links.
    - Public mode hides internal IDs/paths/hashes; debug mode exposes internal metadata as configured.
  - notes: source `design.md` Section 8

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
  - depends_on: TODO-0244, TODO-0245, TODO-0252, TODO-0253
  - scope: Integrate and validate UI/IA renderer contracts end-to-end after specialized Section 8 tasks land.
  - acceptance:
    - Section 8 specialized contract tasks produce coherent, non-conflicting site output across page types.
    - Cross-page navigation/search/feed behavior is consistent after integrating all specialized renderers.
    - Final integration pass closes known UI contract gaps and regressions with snapshot evidence.
  - notes: source `design.md` Section 8

- [ ] TODO-0243: Track reconstruction-plan phase/slice progress explicitly
  - owner: ai
  - created_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0102
  - scope: Add a lightweight phase/slice tracker so each backlog item maps to MVP Slice A/B and Phase 1-6 progress checkpoints.
  - acceptance:
    - Progress tracker includes MVP Slice A/B and Phase 1-6 checkpoints.
    - Each phase has explicit entry/exit criteria tied to TODO IDs.
    - Deferred-build backlog and phase-gate blockers are visible in one place.
  - notes: source `design.md` Section 12

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

- [ ] TODO-0227: Runtime safety guards for cleanup and file operations
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0205
  - scope: Implement destructive-operation safeguards and path restrictions in all cleanup and rollback paths.
  - acceptance:
    - Cleanup blocks dangerous roots (`/`, home, repo root, empty).
    - Deletion stays within explicit staging/temp roots.
    - Safety behavior has dedicated tests for reject cases.
  - notes: source `design.md` Section 9

- [ ] TODO-0226: Observability and LLM trace artifact pipeline
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0204, TODO-0209
  - scope: Implement verbose mode behavior, trace-dir output, and trace artifact persistence for all semantic calls.
  - acceptance:
    - `--verbose` prints prompt, stream output, and trace dir early.
    - Trace artifacts are written under `<site_path>/outputs/llm_traces/...`.
    - Trace file set includes prompt/context/response/meta files per contract.
  - notes: source `design.md` Section 9

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

- [ ] TODO-0222: Repository-seeded persona catalog loading and validation
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0201, TODO-0209
  - scope: Implement strict loading/validation for shared persona catalog and profile image resolution.
  - acceptance:
    - Loader reads only `<repo_root>/personas/social_users.json` (with compatibility mirror support).
    - `persona_id` normalization and alias validation rules are enforced.
    - Profile image paths resolve at runtime; invalid rows fail fast.
  - notes: source `design.md` Section 7.4

- [ ] TODO-0221: Query artifact modes and deterministic manifest assembly
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220
  - scope: Implement deterministic non-markdown query output modes and manifest generation without extra LLM steps.
  - acceptance:
    - `mermaid/images/slides/pdf` modes emit canonical `manifest.json`.
    - `markdown` mode emits no manifest and keeps `manifest_path` null/omitted.
    - Manifest keys and artifact hash contracts match doc requirements.
  - notes: source `design.md` Section 7.3

- [ ] TODO-0220: Query pipeline core contracts and preflight rules
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0204, TODO-0206, TODO-0207, TODO-0213
  - scope: Implement query semantic flow, retrieval contracts, strict/non-strict mode behavior, and rollback semantics.
  - acceptance:
    - Mode validation rejects explicit `strict + include-disputed`.
    - Query writes only under `outputs/query/<query_id>/...` plus run/lint metadata.
    - Query never mutates canonical knowledge artifacts or triggers site rebuild.
    - Terminal query failures rollback invocation-scoped query outputs and run/lint artifacts.
  - notes: source `design.md` Section 7.3

- [ ] TODO-0219: `validate.sh` workflow dispatch and lint-engine integration
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0218, TODO-0235
  - scope: Implement workflow-aware lint entrypoint dispatch from `validate.sh` to `scripts/lint.py`.
  - acceptance:
    - `validate.sh` accepts `--workflow` and optional `--run-id`.
    - Selected workflow key maps to gating behavior from Section 5.8.
    - Command exits and envelopes reflect lint-engine outcomes consistently.
  - notes: source `design.md` Sections 5.8, 6.2

- [ ] TODO-0218: Lint severity engine and warning-threshold status mapping
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0206
  - scope: Implement lint severities, workflow-specific gate behavior, warning-threshold status mapping, and lint artifact writes.
  - acceptance:
    - Severity levels and example checks are enforced (`error/warning/info`).
    - Gate behavior matches workflow key table.
    - `lint.json` and `## Lint Summary` are emitted for committed runs.
  - notes: source `design.md` Section 5.8

- [ ] TODO-0217: Site-root `New` feed refresh policy and incremental/full equivalence
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216, TODO-0211, TODO-0212
  - scope: Implement ingest/topic-driven site-root refresh semantics and equivalence checks for full vs incremental updates.
  - acceptance:
    - Ingest/topic updates refresh site-root `New` for same site.
    - Incremental output is equivalent to deterministic full rebuild.
  - notes: source `design.md` Section 2.2; query/comment/profile exclusions in `TODO-0275`

- [ ] TODO-0216: Deterministic projection/site builder and frontend toolchain reproducibility
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0210, TODO-0212, TODO-0208
  - scope: Implement deterministic HTML renderer, Tailwind build integration, and strict Node/package-manager reproducibility rules.
  - acceptance:
    - Build consumes canonical JSON only and never invokes LLM.
    - Build fails on unresolved template/link/conversion errors.
    - `package.json`, single lockfile, Node pin, and frozen install mode are enforced.
  - notes: source `design.md` Section 8

- [ ] TODO-0215: Reference extraction, structured normalization, and local link backfill
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210
  - scope: Implement reference extraction and matching pipeline for reference-heavy sources.
  - acceptance:
    - References normalize to structured rows.
    - Local source matching in same space persists `linked_source_ids`.
    - Backfill links runs for older records after new ingest.
  - notes: source `design.md` Section 7.2

- [ ] TODO-0214: Ingest mode handling (`--source-only`, `--force`, deferred build)
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210, TODO-0211, TODO-0212, TODO-0205
  - scope: Implement ingest mode-specific behavior for skipping semantic flows, rollback overrides, and bootstrap deferred-build metadata.
  - acceptance:
    - `--source-only` skips semantic generation, normalizes compatibility alias `--query-only`, and writes empty semantic-flow metadata accordingly.
    - `--force` may preserve failed invocation artifacts and writes `force_mode/rollback_skipped`.
    - Deferred-build runs include required metadata and are trackable for backfill.
  - notes: source `design.md` Sections 2.1, 7.1

- [ ] TODO-0213: Relation storage-key hashing and relation consistency validation
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0211
  - scope: Implement relation-file mapping (`relation_id` -> `relation_file_id`) and strict consistency checks.
  - acceptance:
    - Relation files are written to `<space_root>/relations/rel-<sha256(relation_id)>.json`.
    - Persisted `relation_file_id` mismatch fails validation on read/write.
    - Readers treat `relation_id` as semantic source of truth and `relation_file_id` as derived storage key.
  - notes: source `design.md` Section 7.1

- [ ] TODO-0212: Topic generation semantic flow and canonical topic persistence
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0211, TODO-0203, TODO-0204
  - scope: Implement topic semantic generation and canonical topic artifact writes including structure-type support.
  - acceptance:
    - Topic flow resolves spec/schema from authoritative map.
    - Canonical topic JSON writes to `topics/<topic_id>.json`.
    - Deterministic post-processing/build triggers run per policy.
  - notes: source `design.md` Sections 2.2, 4.1.3, 7.1

- [ ] TODO-0211: Ingest extraction semantic flow and canonical claim/relation writes
  - owner: ai
  - created_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210, TODO-0202, TODO-0203, TODO-0204
  - scope: Implement ingest extraction flow from source artifacts to canonical claims/relations plus summary/warnings.
  - acceptance:
    - Semantic output validates against ingest schema.
    - Canonical claim/relation writes follow ID/path contracts.
    - Relation normalization/writer behavior aligns with canonical relation persistence contracts.
  - notes: source `design.md` Sections 4.1.4, 7.1
