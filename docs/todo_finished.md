# Sapi Completed TODO Log

This file is append-only history for completed tasks moved out of `docs/todo.md`.

## 2026-04-12

- [x] TODO-0211: Ingest extraction semantic flow and canonical claim/relation writes
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210, TODO-0202, TODO-0203, TODO-0204
  - scope: Implement ingest extraction flow from source artifacts to canonical claims/relations plus summary/warnings.
  - acceptance:
    - Semantic output validates against ingest schema.
    - Canonical claim/relation writes follow ID/path contracts.
    - Relation normalization/writer behavior aligns with canonical relation persistence contracts.
  - evidence: Added ingest extraction semantic execution + deterministic canonical writes in `sapi/ingest/records_writer.py` and `scripts/ingest_source.py`, including claim writes under `<space_root>/claims/`, relation writes through canonical relation store under `<space_root>/relations/`, and source-record summary/warnings/date-inference persistence; covered by `tests/unit/ingest/test_ingest_extraction_canonical_writes.py` (schema validation gate, canonical ID/path writes, relation normalization behavior, source summary/warning/date-inference persistence).

- [x] TODO-0213: Relation storage-key hashing and relation consistency validation
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0211
  - scope: Implement relation-file mapping (`relation_id` -> `relation_file_id`) and strict consistency checks.
  - acceptance:
    - Relation files are written to `<space_root>/relations/rel-<sha256(relation_id)>.json`.
    - Persisted `relation_file_id` mismatch fails validation on read/write.
    - Readers treat `relation_id` as semantic source of truth and `relation_file_id` as derived storage key.
  - evidence: Tightened write-time consistency checks in `sapi/ingest/relation_store.py` to reject provided `relation_id`/`relation_file_id` mismatches against canonical/hash-derived values, and expanded `tests/unit/ingest/test_relation_store_matrix.py` to cover hash-derived write path IDs, write-time mismatch failures, and reader semantics keyed off payload `relation_id`.

- [x] TODO-0264: Add pipeline-change PR checklist and docs-sync discipline
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0265
  - scope: Add review checklist and contribution guardrails so pipeline-changing PRs answer the required contract questions and keep docs/code ordering disciplined.
  - acceptance:
    - PR template/checklist includes the eight required low-level review questions for pipeline changes.
    - Contribution docs enforce `design.md` -> `low_level.md` -> code change order for contract-level changes.
    - Pipeline-affecting PRs fail quality gate when checklist/docs-sync evidence is missing.
  - evidence: Added `.github/pull_request_template.md` with the eight low-level pipeline review questions plus docs-sync checklist item, added `docs/contributing.md` documenting enforced `design.md` -> `low_level.md` -> code/tests order, and extended `scripts/lint.py` + `sapi/lint/guardrails.py` pipeline PR quality gate logic (`--changed-file`, `--pipeline-pr-checklist`) to fail when pipeline-affecting changes lack completed checklist/docs-sync evidence; covered by `tests/unit/lint/test_pipeline_pr_checklist_gate.py`.

- [x] TODO-0265: Automate low-level anti-drift guardrails
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0102
  - scope: Convert anti-drift constraints into automated checks that fail fast when contracts drift.
  - acceptance:
    - Checks fail on implicit registry fallback, environment-variable flow controls, or duplicate schema/output ownership.
    - Checks flag query-path canonical mutations and other rejected failure patterns from guardrails.
    - Guardrail checks are wired into validation/CI path with clear failure messaging.
  - evidence: Added `sapi/lint/guardrails.py` automated checks for registry fallback literals, disallowed env-var flow controls, semantic-contract ownership duplication, and query canonical mutation patterns; wired guardrail execution/failure output into `scripts/lint.py` (invoked by `validate.sh`); and added `tests/unit/lint/test_guardrail_checks.py` coverage validating each acceptance condition plus validate-entrypoint failure messaging.

- [x] TODO-0280: Define compatibility-reader sunset recommendation as an explicit contract task
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: none
  - scope: Convert unresolved compatibility-reader sunset recommendation into an explicit tracked task with owner, acceptance criteria, and target contract section.
  - acceptance:
    - Task references the unresolved recommendation from the design decision register and assigns one owner/outcome path.
    - Acceptance criteria require explicit contract destination in `design.md` Section 4.1.3 once resolved.
    - Task notes link to the authoritative recommendation source section.
  - evidence: Recommendation intake is now explicit and traceable via successor task `TODO-0282` (`owner: human`) with decision_ref mapping and contract outcome path targeting `design.md` Section 4.1.3; references remain linked to `design.md` Section 1.3 decision register.

- [x] TODO-0281: Define default `evaluate_source.sh` query-mode recommendation as an explicit contract task
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0280
  - scope: Convert unresolved recommendation about default query-mode coverage in `evaluate_source.sh` into an explicit tracked decision task with clear acceptance and contract target.
  - acceptance:
    - Task references the unresolved recommendation from the design decision register and assigns one owner/outcome path.
    - Acceptance criteria require explicit contract destination in `design.md` Section 6.3 once resolved.
    - Task notes link to the authoritative recommendation source section.
  - evidence: Recommendation intake is now explicit and traceable via successor task `TODO-0283` (`owner: ai`) with decision_ref mapping and contract outcome path targeting `design.md` Section 6.3; references remain linked to `design.md` Section 1.3 decision register.

- [x] TODO-0283: Resolve default `evaluate_source.sh` query-mode recommendation into a concrete contract update
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0281
  - scope: Resolve the unresolved query-mode recommendation for `evaluate_source.sh` into explicit default behavior and contract wording in the authoritative section.
  - acceptance:
    - Decision outcome is recorded in `design.md` decision register with resolved status and final contract location.
    - Contract update lands in `design.md` Section 6.3 with explicit default evaluation-pack query modes and optional-mode boundaries.
    - Any affected TODO dependencies/docs coverage references are synchronized.
  - evidence: Updated `design.md` Section 1.3 decision register to `resolved` with final-location link to Section 6.3, tightened Section 6.3 execution contract to require strict-mode query output by default and restrict exploratory/comparative modes to explicit opt-in, and removed `TODO-0283` from open backlog/coverage references in `docs/todo.md`.

- [x] TODO-0237: Implement source metadata extensions for paper-focused ingest
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210, TODO-0211
  - scope: Add paper-taxonomy and citation metadata fields to canonical source records with defaults and validation.
  - acceptance:
    - `article_kind` and citation metadata fields are persisted with allowed values/contracts.
    - Unknown/unavailable citation values use specified defaults.
    - Schema and writer validation reject out-of-contract values.
  - evidence: Added source-record metadata extension persistence and validation in `sapi/ingest/records_writer.py`, exposed ingest CLI flags in `scripts/ingest_source.py`, and covered defaults/valid writes/reject-invalid cases in `tests/unit/ingest/test_source_acquisition.py`.

- [x] TODO-0100: Capture incoming design recommendations into structured tasks
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: none
  - scope: As new recommendations arrive, convert each into a discrete TODO with clear acceptance criteria and cross-doc targets.
  - acceptance:
    - Every recommendation gets a task ID.
    - Each task links target docs/sections.
    - No ambiguous "do later" items without acceptance criteria.
  - evidence: Added explicit recommendation-capture tasks `TODO-0280` and `TODO-0281` mapped from unresolved design decision-register recommendations with section-linked notes, and added `tests/unit/contracts/test_todo_recommendation_intake.py` to enforce decision-to-task intake coverage and ambiguity guards.

- [x] TODO-0210: Source ingest acquisition, normalization, and artifact persistence
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0207, TODO-0208, TODO-0205, TODO-0209
  - scope: Implement source intake from file/URL, normalization to managed artifact set, and source metadata persistence.
  - acceptance:
    - Source artifacts persist under `<space_root>/sources/artifacts/<source_id>/`.
    - Canonical source metadata and artifact pointers are persisted in source records.
    - Ingest lock behavior works (exclusive lock, stale lock recovery, release in finally).
  - evidence: Implemented `scripts/ingest_source.py` acquisition flow with lock-guarded writes, added source persistence helpers in `sapi/ingest/records_writer.py`, implemented lock semantics in `sapi/core/locks.py`, and verified via `tests/unit/ingest/test_source_acquisition.py` and `tests/unit/core/test_locks.py`.

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

- [x] TODO-0101: Add unresolved decisions table to the design docs
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0102
  - scope: Add a compact decision register (decision, options, chosen status, owner, due date) in the docs.
  - acceptance:
    - Decision table exists in docs.
    - Each unresolved decision has explicit owner and due date.
    - Resolved decisions link to the final contract location.
  - evidence: Added `### 1.3 Decision register` in `docs/design.md` with explicit owner/due-date columns and final-location links, plus `tests/unit/contracts/test_design_decision_register.py` to enforce unresolved owner/due-date and resolved contract-link requirements.

- [x] TODO-0200: Repository skeleton and wrapper surface bootstrap
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: none
  - scope: Recreate repository root skeleton, wrapper scripts, and baseline metadata files for reconstruction.
  - acceptance:
    - Root layout includes wrappers, docs, schemas, generation-spec dirs, tests, and runtime pin/lockfile constraints.
    - Wrapper interface signatures match `design.md` Section 6.1.
    - README points to authoritative docs and reconstruction status.
  - evidence: Verified by `tests/unit/contracts/test_todo_0200_bootstrap.py` (root layout + wrapper usage contract + README authoritative docs), with README check updated to include `docs/contract_index.md`.

- [x] TODO-0201: Recreate canonical package/module topology
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0200
  - scope: Scaffold `sapi/` and `scripts/` to authoritative low-level topology before implementing behavior.
  - acceptance:
    - Package/module paths match `docs/low_level.md` Section 3.
    - Wrapper-target script files exist with stub entrypoints.
    - Module boundaries are documented in package `__init__` or equivalent.
  - evidence: Verified by `tests/unit/contracts/test_todo_0201_module_topology.py`, including package/module existence, wrapper-target script stub entrypoints, and explicit wrapper-target mapping documentation in `scripts/__init__.py`.

- [x] TODO-0207: Registry path resolution and targeting contract enforcement
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0200
  - scope: Implement strict registry loading/space resolution and no-fallback behavior for non-bootstrap commands.
  - acceptance:
    - Non-bootstrap commands require explicit `--registry-path`.
    - Relative `space_root` values resolve against registry directory.
    - No fallback/merge with `~/.sapi/spaces.toml`.
  - evidence: Verified by `tests/unit/contracts/test_registry_paths.py`, including explicit `--registry-path` enforcement across non-bootstrap scripts, relative `space_root` resolution against registry directory, and a dedicated non-merge test proving explicit registry authority even when `~/.sapi/spaces.toml` exists.

- [x] TODO-0202: Create v1 generation-spec and JSON schema inventory
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0200
  - scope: Add required `ai_flows/generation_specs/*.v1.md` and `schemas/*.v1.schema.json` files for all semantic flows.
  - acceptance:
    - All required v1 spec/schema files from contract inventory exist.
    - Each spec has required machine-readable header fields.
    - Each schema enforces top-level object constraints and required keys.
  - evidence: Verified by `tests/unit/contracts/test_todo_0202_spec_schema_inventory.py`, including file inventory presence, required machine-readable generation-spec header fields, v1 naming checks, and schema top-level object/`required`/`additionalProperties` contract assertions.

- [x] TODO-0208: Canonical ID/time/path contract helpers
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0201
  - scope: Implement helper library for ID generation, timestamp/date formatting, and canonical path token resolution.
  - acceptance:
    - ID classes and suffix constraints match Section 5.4 contracts.
    - Time/date fields use mandated RFC3339/ISO formats.
    - Path aliases/tokens resolve exactly per Section 5.0 rules.
  - evidence: Verified by `tests/unit/contracts/test_id_contracts.py`, including positive/negative suffix-constraint checks for deterministic and execution IDs, RFC3339/ISO/compact UTC temporal-format assertions, and canonical token/alias path-resolution + rejection coverage for prohibited/undocumented aliases.

- [x] TODO-0209: Site and space bootstrap command implementation
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0200, TODO-0207
  - scope: Implement `create_site` and `create_space` bootstrap behavior and generated runtime layout.
  - acceptance:
    - `create_site.sh` creates `site.json`, `spaces.toml`, and runtime skeleton.
    - `create_space.sh` registers space and creates canonical space root layout.
    - Bootstrap exception for missing `--registry-path` is enforced only for bootstrap commands.
  - evidence: Verified by `tests/unit/contracts/test_bootstrap_site_space.py`, including canonical site bootstrap artifacts (`site.json`, `spaces.toml`, discussion-controls skeleton, runtime directories), space registration/layout idempotency, direct `create_space` bootstrap-registry behavior, slug-safe `<space_name>` enforcement, and non-bootstrap `--registry-path` requirement checks.

- [x] TODO-0203: Generation-spec resolver and version pinning
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0202
  - scope: Implement explicit flow-map-based spec/schema resolution and compatibility alias normalization.
  - acceptance:
    - Specs resolve only via authoritative flow map.
    - `persona_comment_generation` normalizes to `comment_section_generation` at input boundaries.
    - Incompatible schema changes require explicit major-version files and flow-map update.
  - evidence: Verified by `tests/unit/semantic/test_spec_resolution.py`, including flow-map-only resolution checks, alias normalization at both resolver and invocation-input boundaries (with deprecation warning), explicit major-version mismatch rejection, and pinned-v1 resolution behavior even when `v2` files are present without flow-map update.

- [x] TODO-0238: Implement prompt-asset precedence contract (`.skill` vs generation specs)
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0202, TODO-0203
  - scope: Enforce semantic contract ownership so generation specs remain authoritative when orchestration text differs.
  - acceptance:
    - Semantic output contract (schema/output path/context roots) is sourced from generation specs, not `.skill` text.
    - Any `.skill` and generation-spec disagreement resolves in favor of generation spec.
    - Deterministic render/build logic never redefines semantic schemas outside spec/schema files.
  - evidence: Verified by `tests/unit/semantic/test_prompt_asset_precedence.py`, including authoritative contract resolution without skill text, explicit conflict-field diagnostics for `.skill` disagreements, and deterministic schema-override rejection in both contract and invocation-resolution paths.

- [x] TODO-0204: Shared semantic executor with repair-loop retry policy
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0202, TODO-0203
  - scope: Implement one semantic executor for all flows using strict schema validation and repair retries.
  - acceptance:
    - `max_repair_loops=3`, `max_attempts=4` behavior is enforced.
    - Repair attempts include prior invalid JSON + machine-readable validation errors + schema.
    - Invalid outputs are never committed as canonical artifacts.
  - evidence: Verified by `tests/unit/semantic/test_retry_budget.py`, with explicit default budget checks
    (`DEFAULT_MAX_REPAIR_LOOPS=3`, `DEFAULT_MAX_ATTEMPTS=4`), repair-context assertions
    (invalid JSON + machine-readable validation errors + schema), and overwrite protection proving
    invalid outputs do not replace existing canonical artifacts.

- [x] TODO-0205: Artifact transaction journal and rollback semantics
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0201, TODO-0208
  - scope: Implement transaction-scoped artifact journaling and rollback behavior for terminal failures.
  - acceptance:
    - Default failures rollback invocation-scoped writes and remove committed run containers.
    - Ingest `--force` failures may preserve artifacts and committed failure run envelope.
    - Rollback coverage includes canonical + derived + invocation run/lint artifacts.
  - evidence: Verified by `tests/unit/core/test_transactions.py` (default rollback/removal of
    run containers, ingest `--force` artifact retention, canonical+derived+run/lint rollback
    coverage, and ingest-only `--force` guard) plus `tests/unit/core/test_pipeline_policy.py`
    (failure-mode run finalization behavior and enforced `force_mode=true`,
    `rollback_skipped=true` for retained ingest failure envelopes).

- [x] TODO-0206: Run-envelope writer with flow-specific extensions
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0201, TODO-0208
  - scope: Implement canonical run metadata writing with base fields and pipeline-specific extension fields.
  - acceptance:
    - Run records write to `<space_root>/runs/<run_id>/run.md`.
    - Base envelope includes `semantic_flows` and `semantic_flow_invocation_counts`.
    - Run body includes required sections: `## Summary`, `## Changes`, `## Lint Summary`, `## Errors`.
    - Flow-specific extension fields are present and typed by pipeline.
  - evidence: Verified by `tests/unit/contracts/test_run_envelope_semantic_flows.py` and
    `tests/unit/contracts/test_run_envelope_metadata_invariants.py`, including canonical
    `<space_root>/runs/<run_id>/run.md` path assertion, semantic flow + invocation-count frontmatter
    checks, required section presence/order with `(none)` fallback, and per-pipeline extension-field
    type enforcement.

- [x] TODO-0262: Enforce common pipeline status/exit-code and commit policy contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0205, TODO-0206
  - scope: Centralize and enforce pipeline state-machine transitions, exit-code mapping, and default commit/rollback policy across ingest/query/comments/profiles.
  - acceptance:
    - Status transitions (`pending`, `success`, `success_with_warnings`, `failed`, `aborted`) follow one shared contract implementation.
    - Exit-code mapping is consistent (`0` only for success statuses, non-zero for failed/aborted).
    - Default-mode failure handling never leaves committed run containers, with ingest `--force` exception explicitly tested.
  - evidence: Verified by `tests/unit/core/test_pipeline_policy.py`, including shared status
    transition checks, exit-code mapping checks (`0` only for success statuses and rejection of
    non-terminal `pending`), default failure run-container pruning for query/comments/profiles,
    and explicit ingest `--force` retained-failure exception coverage.

- [x] TODO-0269: Enforce canonical run-envelope metadata completeness and invariants
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0206, TODO-0262
  - scope: Enforce full base run-envelope field coverage and semantic-flow invariants for all committed pipeline runs.
  - acceptance:
    - Base frontmatter includes all required runtime/fingerprint/toolchain/lint fields for every committed flow.
    - `semantic_flows` ordered-unique semantics and `semantic_flow_invocation_counts` positivity/key coverage invariants are enforced.
    - Flows without lint/build stages follow one consistent null-or-zero lint-total policy with tests.
  - evidence: Verified by `tests/unit/contracts/test_run_envelope_metadata_invariants.py` and
    `tests/unit/contracts/test_run_envelope_semantic_flows.py`, including required base-field
    coverage across all committed flows, semantic-flow key/order/count invariants (duplicate/missing/
    extra/unknown/non-positive cases), RFC3339 UTC timestamp validation for `started_at` and
    `completed_at`, and consistent integer lint-total policy checks for no-lint/no-build flows.

- [x] TODO-0236: Implement site/scope/subspace metadata contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0209
  - scope: Implement `site.json` and `subspaces.json` contracts including validation and resolution rules.
  - acceptance:
    - Site scope contract (`site_scope_v1`) is validated and written at canonical site path.
    - Subspace metadata contract (`space_subspaces_v1`) validates duplicates, nesting rules, and root existence.
    - Compatibility-only read paths are supported only where explicitly allowed.
  - evidence: Verified by `tests/unit/core/test_site_scope_contracts.py`, including canonical
    `<site_path>/site.json` writes with validated relative `site_root` resolution semantics,
    write-time failure for invalid/missing `site_root`, subspace duplicate/nesting/missing-root
    validation checks for `space_subspaces_v1`, and explicit opt-in gating for compatibility
    legacy reads from `<space_root>/site.json`.

- [x] TODO-0235: Implement wrapper normalization and compatibility-alias handling
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0200, TODO-0207
  - scope: Implement canonical wrapper argument normalization and conflict handling across ingest/comments bootstrap rules.
  - acceptance:
    - Ingest alias `--query-only` normalizes to `--source-only` with deprecation warning.
    - Comment aliases (`--user`, `--page`, legacy positional count) normalize to canonical flags.
    - Canonical+alias duplicate argument combinations fail fast with usage error.
  - evidence: Verified by `tests/unit/contracts/test_wrapper_alias_normalization.py`, covering
    ingest `--query-only` normalization/deprecation, comment alias normalization for
    `--user`/`--page` plus legacy positional count, and canonical+alias conflict failures for
    ingest (`--source-only` + `--query-only`) and comments (`--comment-user` + `--user`,
    `--comment-page` + `--page`, positional count + `--count`) with usage errors.

- [x] TODO-0240: Enforce non-negotiable runtime policy guardrails
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0201, TODO-0204
  - scope: Implement explicit runtime guardrails for LLM-only semantic execution, test-only mock mode, and no-env-var flow controls.
  - acceptance:
    - Production/operator semantic flows cannot fall back to deterministic semantics.
    - `--mock-llm` is test-only, auditable in run metadata, and never silently enabled by wrappers.
    - Flow behavior cannot be changed by environment variables; CLI args are the only control surface.
  - evidence: Verified by `sapi/core/runtime_policy.py` plus `tests/unit/core/test_runtime_policy_guardrails.py`
    (deterministic-fallback rejection and all prohibited flow env-var toggles) and
    `tests/unit/contracts/test_wrapper_mock_mode_policy.py` (all semantic wrappers default to
    live LLM mode, require explicit `--mock-llm` for mock mode, and reject env-var flow controls).

- [x] TODO-0241: Enforce canonical site/space storage layout and relocatability
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0208, TODO-0209, TODO-0207
  - scope: Implement and validate canonical layout under `<site_path>` and `<space_root>` including relative-path persistence policy.
  - acceptance:
    - Site-level and space-level directories/files match Section 5.1/5.2 layout contracts.
    - Canonical/derived artifacts write to correct roots (`site` vs `space` vs `repo` ownership).
    - Persisted user-facing paths are relative where required for relocatability.
  - evidence: Verified by `tests/unit/contracts/test_bootstrap_site_space.py`, including canonical
    site/space layout assertions, site-vs-space-vs-repo ownership boundary checks
    (`outputs/llm_traces`, `outputs/query`, source artifacts, persona catalog non-copying), and
    relocatability proof by persisting relative `site_root`/`space_root`, moving the entire site
    root, and resolving the same registry entries to the new filesystem location.

- [x] TODO-0239: Implement core domain models and boundary invariants
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0201
  - scope: Define typed domain models for site/space/sub-space/source/claim/relation/topic/persona/comment with boundary invariants.
  - acceptance:
    - Core entities from system boundary contract are represented in typed models.
    - Identity alias constraints (`persona_id` vs `id`, `topic_id` vs `narrative_id`) are enforced.
    - Invariant checks fail fast on invalid identity or boundary relationships.
  - evidence: Added `sapi/contracts/domain_models.py` with typed dataclasses for Site/Space/SubSpace/
    Source/Claim/Relation/TopicPage/Persona/Comment plus boundary validation utilities; verified by
    `tests/unit/contracts/test_domain_models.py` covering valid typed-model instantiation,
    persona/topic alias mismatch failures, and boundary invariant failures for cross-space records,
    unknown source/claim references, and invalid comment page linkage.

- [x] TODO-0272: Enforce semantic-flow input envelope and prompt payload contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 1
  - depends_on: TODO-0203, TODO-0204, TODO-0238
  - scope: Enforce canonical semantic invocation envelope and prompt input hygiene across all semantic flows.
  - acceptance:
    - Every semantic invocation is passed canonical `schema_path`, `output_json_path`, and `context_paths[]` fields from generation-spec contracts.
    - Semantic prompt assembly passes filesystem pointers/evidence paths instead of pre-expanded semantic dumps except where explicitly required by schema contract.
    - Validation/tests prevent silent drift from canonical envelope fields or prompt-input policy.
  - evidence: Updated `sapi/llm/client.py` and `sapi/llm/semantic_executor.py` so every semantic
    LLM request now carries explicit invocation-envelope fields (`schema_path`,
    `output_json_path`, `context_paths`) and enforces pointer-only prompt context payloads
    (`file://`, `dir://`, `missing://`, `unsupported://`) before invocation; validated by
    expanded `tests/unit/semantic/test_input_envelope_contract.py` covering all canonical semantic
    flows, request-envelope field forwarding, prompt pointer hygiene, and drift rejection.
