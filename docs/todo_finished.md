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
