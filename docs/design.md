# Sapi Design Document

## 1. Scope and Intent

This document is the reconstruction blueprint for Sapi.

Primary goal:
- recreate the codebase so the original end-to-end product works again.

Product goal:
- ingest sources into a space
- derive claims and relations via LLMs
- project topic pages and build a static web site
- simulate social discussion with repository-seeded users and threaded comments
- support query over retrieved source/claim context

Policy for this doc:
- `MUST`: required for parity
- `SHOULD`: strong default unless consciously redesigned
- `HISTORICAL`: recovered behavior that can be changed with explicit decision

Contract precedence (normative):
1. statements marked `normative` and all `MUST` clauses
2. `SHOULD` defaults and recovered default values
3. `HISTORICAL` notes and recovered footprints

Interpretation rule:
- unless a section explicitly marks a recovered item as normative, any line prefixed with `Recovered ...` is `HISTORICAL` context, not a hard contract.

### 1.1 Reading guide (recommended order)

1. Read Section 2 first for non-negotiable semantic/runtime constraints.
2. Read Section 5 next for canonical filesystem, ID, registry, scope, and lint-gate contracts.
3. Read Sections 6-7 for operator workflow and subsystem pipelines.
4. Read Sections 8-11 for UI/build, observability, and run envelopes.
5. Use Sections 12-13 for implementation sequencing and completion criteria.

### 1.2 Contract authority matrix (normative)

- semantic/runtime invariants: Section 2 is authoritative.
- filesystem, IDs, registry targeting, lint severities/gates: Section 5 is authoritative.
- subsystem pipeline behavior: Section 7 is authoritative.
- run status/envelope fields and lifecycle semantics: Section 10 is authoritative.
- implementation package/module topology for reconstruction: [docs/low_level.md](/Users/chrgre01/src/Sapi/docs/low_level.md) Section 3 is authoritative.
- recovered file/module inventories in this document are historical reference only unless explicitly marked normative.

Change ownership guide:
- update Section 2 only for semantic/runtime invariants.
- update Section 5 for storage/ID/registry/scope/lint contracts.
- update Section 7 for ingest/query/social pipeline behavior.
- update Section 8 for web/UI/rendering requirements.
- update Section 10 for run output and lifecycle semantics.

### 1.3 Decision register

Use this table to track active architecture decisions without losing contract linkage.

| Decision | Options considered | Status | Owner | Due date | Final contract location |
| --- | --- | --- | --- | --- | --- |
| Comment subsystem canonical namespace | `comment_section_*` vs `persona_comment_*` | resolved | ai | 2026-04-12 | [Section 7.6](/Users/chrgre01/src/Sapi/docs/design.md#76-comment-section-generation-and-rendering) |
| Run-envelope semantic flow cardinality shape | ordered flow list only vs ordered list + invocation count map | resolved | ai | 2026-04-12 | [Section 10](/Users/chrgre01/src/Sapi/docs/design.md#10-run-status-and-output-envelopes) |
| Additional query modes in `evaluate_source.sh` default evaluation pack | strict-only default vs strict + exploratory + comparative default | resolved | ai | 2026-05-20 | [Section 6.3](/Users/chrgre01/src/Sapi/docs/design.md#63-user-facing-source-evaluation-harness-normative) |

## 2. Non-Negotiable Runtime Policy

- production/operator semantic generation MUST be LLM-driven.
- deterministic semantic bypass is prohibited for production/operator ingest/query/topic-page/comment/persona-profile semantics.
- explicit test-only mock execution MAY be used via CLI flag `--mock-llm`; this is test-only mode, not a production execution mode.
- runtime feature flags and config toggles MUST NOT switch semantic flows to deterministic/non-LLM execution in production/operator mode.
- if a semantic flow is disabled via runtime/config toggles in production/operator mode, the command MUST fail fast with configuration error instead of falling back to deterministic semantics.
- ingest-only rollback override MAY be exposed via explicit CLI flag `--force` (Section 7.1); this override affects rollback behavior only and MUST NOT switch semantic generation away from LLM execution.
- Invalid LLM output MUST enter a schema-repair retry loop: feed the invalid JSON, schema, and validation errors back to the LLM for correction; fail loudly after the retry cap.
- Recovered default repair-loop cap: `max_repair_loops = 3` before hard failure.
- Effective default attempt budget per semantic generation invocation is `max_attempts = 1 + max_repair_loops` (initial attempt + up to three repair attempts).
- live semantic generation MUST execute through Codex CLI (`--llm-backend codex`).
- model and reasoning effort MUST be runtime-configurable via CLI arguments.
- runtime configuration SHOULD define explicit defaults; recommended precedence is: CLI flag -> wrapper/project default.
- flow behavior/configuration MUST NOT be controlled by environment variables.
- historical baseline defaults (non-normative, may change): backend and model come from wrapper/runtime configuration, with default reasoning effort typically `high` unless a flow intentionally lowers it.
- every LLM generation flow MUST be driven by a checked-in markdown generation spec.
- generation specs MUST declare, at minimum: schema location, output JSON path, and filesystem context pointers used as evidence/input.
- LLM outputs for generation flows MUST be strict JSON that validates against the referenced schema.
- covered semantic LLM flows include ingest extraction, topic generation, query synthesis, comment section generation, and persona profile page generation; each MUST have a checked-in generation spec.
- optional markdown rendering from generated JSON MUST be deterministic and MUST NOT invoke an LLM.
- static site HTML rendering MUST use canonical JSON artifacts as input and MUST NOT invoke an LLM.

### 2.1 Unified semantic generation algorithm (normative)

This algorithm applies identically to semantic JSON generation only across every semantic flow (ingest extraction, topic generation, query synthesis, comment section generation, and persona profile page generation).

1. choose the flow-specific generation spec markdown file from the repository using the mapping contract in Section 4.1.3.
2. resolve from spec: `schema_path`, `output_json_path`, and `context_paths[]` (for example `sources/`, `topics/`, `comments/`, prior run outputs).
3. gather filesystem context from the declared paths.
4. invoke LLM with spec + gathered context, requesting strict JSON for `output_json_path`.
5. validate JSON against schema; on failure, run schema-repair loops up to `max_repair_loops` (invalid JSON + validation errors + schema) and fail loudly on final validation failure.
6. persist validated semantic JSON artifact(s) to the resolved `output_json_path`.
7. run flow-specific deterministic canonical-write/render steps (if applicable) from validated semantic JSON.
8. write run metadata using the base envelope plus flow-specific extensions defined in Section 10 (inputs, model/runtime details, flow-specific outputs, validation/lint/build status).

Deterministic post-processing beyond step 8 is flow-specific and is governed by Section 2.2.

Semantic-output vs canonical-write contract (normative):
- `output_json_path` always denotes the validated semantic JSON artifact produced by one semantic LLM invocation.
- canonical domain artifacts MAY be written at different paths by deterministic post-processing after semantic JSON validation.
- canonical-write mapping by flow:
  - `ingest_extraction`: semantic output at `runs/<run_id>/semantic/ingest_extraction.json`; canonical writes under `sources/`, `claims/`, and `relations/`.
  - `topic_generation`: semantic output at `runs/<run_id>/semantic/topic_generation.json`; canonical writes produce `0..n` topic pages under `topics/<topic_id>.json`.
  - `query_synthesis`: semantic output path and canonical query write are the same file (`outputs/query/<query_id>/query.json`).
  - `comment_section_generation`: semantic output is per target page invocation at `runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json`; canonical comment rows are merged into canonical page JSON/projections during deterministic merge/normalization.
  - `persona_profile_generation`: semantic output path and canonical profile write are the same file (`profiles/persona-<persona_id>.json`).

Retry/repair loop details (normative):
- all semantic flows MUST use the same retry/repair behavior defined here; flow-specific overrides are not allowed.
- `max_repair_loops` is the number of repair retries after the initial attempt (default `3`).
- `max_attempts = 1 + max_repair_loops` (default `4` total attempts).
- each repair attempt MUST include:
  - previous invalid JSON output
  - machine-readable validation errors from schema validation
  - the same target schema contract
- repair attempts MUST request a complete strict-JSON replacement output (not patch/diff text).
- implementations MUST NOT apply deterministic auto-fixes to invalid semantic JSON outside this LLM repair loop.
- invalid attempt outputs MUST NOT be committed outside the declared `output_json_path` for that attempt.
- default failure behavior: if retry budget is exhausted or later deterministic post-processing fails, implementation MUST rollback invocation-scoped artifact writes before returning failure.
- default rollback scope includes canonical artifacts, derived artifacts, and invocation-scoped run/lint metadata touched by the failed invocation.
- terminally failed invocations MUST NOT persist committed `<space_root>/runs/<run_id>/` artifact containers, except ingest invocations explicitly run with `--force` (Section 7.1).
- ingest `--force` override contract:
  - applies only to ingest pipeline invocations
  - MAY skip rollback and preserve invocation-scoped writes produced before failure for forensic recovery
  - MUST mark run metadata with `force_mode: true` and `rollback_skipped: true` when rollback is skipped
  - MUST NOT change semantic retry/schema-validation rules or permit deterministic semantic fallback

### 2.2 Flow-specific deterministic post-processing trigger policy (normative)

Semantic generation completion is defined at validated semantic JSON persistence to `output_json_path` (Section 2.1 step 6). Deterministic rendering/build triggers are flow-specific:

| Semantic flow | Deterministic post-processing requirement |
| --- | --- |
| ingest extraction | In normal operation, MUST run projection/reindex/site build for the affected space and MUST refresh site-root `New` feed/index views for the same `<site_path>` (full site rebuild or incremental equivalent). During reconstruction Phases 1-2 before projection/build modules exist, MAY run in `build_deferred` bootstrap mode that persists canonical ingest artifacts and marks run metadata for deferred build. |
| topic generation | MUST run deterministic projection and site build for the affected space and MUST refresh site-root `New` feed/index views for the same `<site_path>` (full site rebuild or incremental equivalent). |
| query synthesis | MUST run only query-result renderers/artifact assembly from query JSON; MUST NOT trigger space/site HTML rebuild. |
| comment section generation | MUST run batched semantic comment-section generation (single LLM call per targeted page, unless chunking fallback is required), then deterministic comment merge/normalization and page projection; SHOULD rebuild affected space feed/index views (full space rebuild MAY be used). |
| persona profile page generation | MUST run deterministic persona-profile projection and history update; SHOULD rebuild affected profile/user views (full space rebuild MAY be used). |

Chained-flow coalescing rule (normative):
- when one command runs `ingest_extraction` and `topic_generation` back-to-back, implementation MAY coalesce deterministic projection/reindex/site-build into one final pass, provided output is equivalent to running both post-processing requirements independently.

Site-root feed/index scope contract (normative):
- site-root `New` feed/index views are site-scoped and aggregate recent source/topic items across all spaces under one `<site_path>`.
- for multi-space sites, any successful ingest/topic flow in one `<space_name>` MUST refresh site-root `New` feed/index views for that same `<site_path>` before command completion.
- implementations MAY use incremental feed/index refresh instead of full site rebuild, but output MUST be equivalent to a deterministic full rebuild.
- query/comment/profile flows MUST NOT refresh site-root `New` feed/index views unless they mutate canonical source/topic artifacts.

### 2.3 Test-only mock execution mode (normative)

When a semantic command is invoked with `--mock-llm`:
- semantic flows MAY use a deterministic/mock backend for tests and local contract checks.
- output artifacts MUST still validate against the same schemas/contracts as live LLM mode.
- run/query metadata MUST mark `execution_mode` as mock/test (for example `mock_llm_test`) so results are auditable.
- shell wrappers intended for normal operator usage SHOULD default to live LLM mode and MUST NOT silently enable mock mode.

## 3. Core Concepts and System Boundaries

- `Site`: top-level container for spaces/content; persona catalog is repository-seeded and shared across all sites.
- `Space`: primary content unit under a site, conceptually similar to a subreddit/community.
- `Sub-space`: optional child of a space; may contain content but cannot have nested sub-spaces.
- `Source`: ingested artifact + metadata + provenance.
- `Claim`: extracted factual statement.
- `Relation`: typed edge between claims; some relation types are directed (`supports`, `derived_from`, `falsifies`) and others are undirected (`contradictory`, `similar`).
- `Topic Page`: canonical JSON topic document (`topic_id`) rendered to static HTML; optional markdown projection may also be emitted.
  - topic pages support two presentation structures: `wiki` (default) and `source_mirror` (for source-anchored topics, especially journal articles).
- `Persona/User`: repository-seeded actor used for social layer.
- `Comment`: threaded social post with turn schema + moderation summary.

Identity model:
- `persona_id` is the only stable identity key for attribution and links.
- canonical stored identity field is `persona_id`.
- non-canonical legacy identity fields such as `id` MUST NOT replace `persona_id` in canonical reads or writes.
- `display_name` and `full_name` are presentation fields and may collide.

## 4. Repository Architecture to Recreate

### 4.1 Expected root layout

```text
Sapi/
  .skills/
    ingest_source.skill
    query.skill
    maintenance.skill
  personas/
    social_users.json
    profile_images/*
  sapi/
  scripts/
  tests/
  docs/
    design.md
  ai_flows/
    generation_specs/*.md
  schemas/
    *.schema.json
  package.json
  <one of: package-lock.json | pnpm-lock.yaml | yarn.lock>
  <one of: .nvmrc | .node-version>
  create_site.sh
  create_space.sh
  ingest.sh
  query.sh
  create_comments.sh
  generate_profiles.sh
  regenerate_web.sh
  validate.sh
  evaluate_source.sh
```

### 4.1.1 Runtime site-root layout (created by `create_site.sh`)

```text
<site_path>/
  site.json
  spaces.toml
  config/
    discussion_controls.json
  spaces/<space_name>/...
```

- `config/discussion_controls.json` is optional but reserved as the canonical site-level location for comment-section discussion controls (Section 7.6).

### 4.1.2 Prompt-asset ownership and precedence (normative)

- `.skills/*.skill` owns operator-facing orchestration: CLI/task flow, reusable instructions, defaults, and sequencing.
- `ai_flows/generation_specs/*.md` owns semantic generation contracts: required schema, semantic JSON output target, and declared context roots.
- for semantic LLM outputs, generation specs are the source of truth for output shape and validation behavior.
- if a `.skill` file and a generation spec disagree for a semantic flow, the generation spec MUST take precedence.
- `.skill` files SHOULD reference generation spec paths instead of duplicating schema/output contract text inline.
- deterministic render/build stages MAY use `.skill` orchestration, but MUST NOT redefine semantic JSON schemas outside generation specs.

### 4.1.3 Generation spec discovery and versioning (normative)

Canonical path conventions:
- generation spec path pattern: `<repo_root>/ai_flows/generation_specs/<flow_key>.v<major>.md`
- schema path pattern: `<repo_root>/schemas/<flow_key>.v<major>.schema.json`
- each generation spec MUST declare `flow_key`, `version`, `schema_path`, `output_json_path`, and `context_paths[]`.

Flow map (authoritative defaults):

| flow_key | canonical generation spec path | canonical schema path | semantic `output_json_path` template | version policy |
| --- | --- | --- | --- | --- |
| `ingest_extraction` | `ai_flows/generation_specs/ingest_extraction.v1.md` | `schemas/ingest_extraction.v1.schema.json` | `<space_root>/runs/<run_id>/semantic/ingest_extraction.json` | pinned to `v1`; incompatible schema/output changes require `v2` spec+schema files |
| `topic_generation` | `ai_flows/generation_specs/topic_generation.v1.md` | `schemas/topic_generation.v1.schema.json` | `<space_root>/runs/<run_id>/semantic/topic_generation.json` | pinned to `v1`; incompatible schema/output changes require `v2` spec+schema files |
| `query_synthesis` | `ai_flows/generation_specs/query_synthesis.v1.md` | `schemas/query_synthesis.v1.schema.json` | `<space_root>/outputs/query/<query_id>/query.json` | pinned to `v1`; incompatible schema/output changes require `v2` spec+schema files |
| `comment_section_generation` | `ai_flows/generation_specs/comment_section_generation.v1.md` | `schemas/comment_section_generation.v1.schema.json` | `<space_root>/runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json` | pinned to `v1`; incompatible schema/output changes require `v2` spec+schema files |
| `persona_profile_generation` | `ai_flows/generation_specs/persona_profile_generation.v1.md` | `schemas/persona_profile_generation.v1.schema.json` | `<space_root>/profiles/persona-<persona_id>.json` | pinned to `v1`; incompatible schema/output changes require `v2` spec+schema files |

Canonical-write note (normative):
- flow-map `output_json_path` values are semantic-output paths for the LLM invocation.
- downstream canonical writes that differ from `output_json_path` are governed by Section 2.1 (Semantic-output vs canonical-write contract) and Section 7 subsystem contracts.

Discovery and pinning rules:
- semantic flows MUST resolve generation specs from the table above by `flow_key`; no implicit filename discovery beyond this map.
- semantic inputs MUST use canonical flow keys from this table; unknown flow keys, including `persona_comment_generation`, MUST fail fast with usage/configuration error.
- spec/schema version pairing is immutable per major version (`<flow_key>.v1.md` MUST reference `<flow_key>.v1.schema.json`).
- backward-compatible prompt wording/context improvements MAY update an existing major version file.
- incompatible schema shape/output-path contract changes MUST create new major-version files and update this flow map explicitly.
- path templates MAY contain runtime tokens (for example `<space_root>`, `<run_id>`, `<query_id>`, `<topic_id>`, `<persona_id>`, `<page_ref_key>`); tokens MUST be resolved to absolute paths before LLM invocation and validation.
- for comment-section semantic outputs, `<page_ref_key>` MUST be a deterministic filesystem-safe key derived from the canonical `page_ref` (for example `<page_type>--<page_id>`).

Canonical-only naming policy (normative):
- canonical writes, canonical schema keys, generation-spec flow keys, CLI flags, and run-envelope metadata MUST use canonical names only.
- legacy aliases listed for removal in `docs/todo.md` are non-canonical inputs and MUST fail fast with usage/configuration errors.
- documentation examples and operator guidance MUST use only canonical names.

### 4.1.4 Generation spec and schema file contents (normative)

Required v1 file inventory (repository-relative):
- `ai_flows/generation_specs/ingest_extraction.v1.md`
- `ai_flows/generation_specs/topic_generation.v1.md`
- `ai_flows/generation_specs/query_synthesis.v1.md`
- `ai_flows/generation_specs/comment_section_generation.v1.md`
- `ai_flows/generation_specs/persona_profile_generation.v1.md`
- `schemas/ingest_extraction.v1.schema.json`
- `schemas/topic_generation.v1.schema.json`
- `schemas/query_synthesis.v1.schema.json`
- `schemas/comment_section_generation.v1.schema.json`
- `schemas/persona_profile_generation.v1.schema.json`

Generation spec markdown content contract (all flows):
- each spec file MUST include a machine-readable contract header declaring `flow_key`, `version`, `schema_path`, `output_json_path`, and `context_paths[]`.
- each spec file MUST include a concise task statement describing what semantic JSON artifact to generate.
- each spec file MUST include context interpretation rules (how to treat missing/ambiguous context and what evidence sources are in scope).
- each spec file MUST include strict output rules: JSON object only, no markdown fences, no prose outside JSON, and no invented IDs outside allowed contracts.
- each spec file MUST include schema-repair instructions for retry loops: when prior invalid JSON + validation errors are provided, return one complete corrected JSON replacement.
- each spec file SHOULD include one small, non-normative JSON shape sketch for implementer readability.

Schema authoring contract (all flows):
- schemas MUST be valid JSON Schema (Draft 2020-12 or later) and checked in under `schemas/`.
- top-level schema MUST be `type: object` with explicit `required` keys.
- top-level `additionalProperties` MUST be `false` unless an explicit extension-map field is documented.
- identity fields and references (`source_id`, `claim_id`, `topic_id`, `persona_id`, `comment_uid`) MUST enforce formats/patterns aligned with Section 5.4.
- enumerations and bounded numeric ranges (for example turn `position`, `confidence`) MUST be encoded in schema, not left to prompt text.
- nullable values MUST be explicit in schema (for example union with `null`), not implied.

Per-flow v1 schema minimum top-level keys:
- `ingest_extraction`: `source_date_inference`, `source`, `claims`, `relations`, `summary`, `warnings`
- `topic_generation`: `topics` (0..n entries where each entry contains `topic_id`, `title`, `structure_type`, `sections`, `claim_ids`, `source_ids`; `topic_id` may be omitted and deterministically derived in canonical write stage)
- `query_synthesis`: `query_id`, `answer`, `claims_used`, `sources_used`, `retrieval_counts`, `contradictions_considered`, `falsification_signals`, `mode`, `scope`, `execution`, `warnings`
- `comment_section_generation`: `page_ref`, `requested_count`, `comments`
- `persona_profile_generation`: `persona_id`, `space_name`, `profile_sections`, `profile_image_path`, `accountability_summary`

Notes on key naming:
- these are minimum v1 keys; flows MAY add fields only with matching schema updates.
- flows MUST use canonical key names only.

### 4.2 Historical recovered `sapi/` module inventory (HISTORICAL)

- orchestration/contracts: `llm.py`, `skill_runner.py`, `skills.py`, `semantic_contracts.py`, `skill_output_contracts.py`, `contracts.py`
- content pipeline: `space.py`, `records.py`, `run_records.py`, `imports.py`, `ingest_matching.py`, `source_content.py`, `citations.py`, `topic.py`, `naming.py`
- registry/scope: `registry.py`, `site_scope.py`
- site/projection: `site_builder.py`, `projection_index.py`
- social: `social_users.py`, `persona_registry.py`, `persona_profile_images.py`, `persona_profile_pages.py`, `persona_comments.py`, `comment_quality.py`

### 4.3 Historical recovered `scripts/` module inventory (HISTORICAL)

- `ingest_source.py`, `query.py`, `build_site.py`, `build_projection_index.py`
- `lint.py`
- `create_comments.py`
- `generate_profiles.py`
- `evaluate_source.py`
- `project_topic_collection.py`, `rebuild_topic_collection.py`
- `space_registry.py`, `init_space.py`, `set_topic_lifecycle.py`, `generate_short_names.py`, `run_maintenance.py`, `migrate_artifacts.py`

### 4.4 Ingest/query capability ownership (normative)

Ingest flow capability ownership:
- CLI/wrapper entrypoint mapping: `ingest.sh` -> `scripts/ingest_source.py`
- orchestration and semantic-call wiring: ingest pipeline + shared semantic executor/generation-spec resolver
- source fetch/normalization/storage: ingest source-content layer
- canonical record writes (source/claim/relation/topic): canonical record-writer layer
- ID and naming helpers: shared ID/naming contracts layer
- reference extraction/linking: citations/matching layer
- deterministic projection/build/index: site-builder + projection-index layers
- run/lint artifacts: run-envelope/lint writers

Query flow capability ownership:
- CLI/wrapper entrypoint mapping: `query.sh` -> `scripts/query.py`
- orchestration and semantic-call wiring: query pipeline + shared semantic executor/generation-spec resolver
- retrieval over existing canonical artifacts: retrieval/matching layer
- query artifact assembly and output writes: query pipeline deterministic render/output layer
- required run/lint envelope writes: run-envelope/lint writers for every committed query invocation

Flow boundary rule (normative):
- ingest is the canonical-write flow and MAY mutate `sources/`, `claims/`, `relations/`, `topics/`, and deterministic build/index outputs.
- query is read/synthesize and MUST NOT mutate canonical knowledge artifacts under `sources/`, `claims/`, `relations/`, `topics/`, or `profiles/`.
- query writes are limited to query outputs (`outputs/query/<query_id>/...`) plus run/lint metadata artifacts.

## 5. Storage, IDs, and File Contracts

Section 5 contract index:
- 5.0 path token and alias rules
- 5.1-5.3 canonical storage layout (site/space/source artifacts)
- 5.4 ID and naming contracts
- 5.5 registry targeting and precedence
- 5.6 source metadata extensions
- 5.7 site/scope/subspace metadata contracts
- 5.8 lint severities, gates, and required lint artifacts

### 5.0 Canonical path model (normative)

Path tokens used throughout this document:
- `<repo_root>`: absolute filesystem path to this Sapi repository checkout.
- `<site_path>`: absolute filesystem path to one site root created by `create_site.sh`.
- `<space_name>`: slug key for one space registered in `<site_path>/spaces.toml`.
- `<space_root>`: canonical resolved absolute path for `<space_name>` after applying registry path resolution rules. In site-local usage this is typically `<site_path>/spaces/<space_name>`.

Path interpretation rules:
- Bare `site/` paths mean `<space_root>/site/`.
- Bare `outputs/` paths mean `<space_root>/outputs/`.
- Bare `raw/` paths mean `<space_root>/raw/`.
- Bare `personas/` paths refer to repository-seeded catalog under `<repo_root>/personas/` unless explicitly prefixed with `<site_path>` or `<space_root>`.
- All persistent path examples in contracts MUST resolve from `<repo_root>`, `<site_path>`, or `<space_root>`.
- The aliases `sites/<site_name>/...` and any other undocumented root aliases are prohibited in new or normative examples.

Registry path-value resolution rule:
- `space_root` values in registry files MAY be absolute or relative.
- relative `space_root` values MUST resolve against the directory containing the active registry file.
- command/runtime logic SHOULD normalize to a resolved absolute `<space_root>` before file I/O.

### 5.1 Site-level storage

```text
<site_path>/
  site.json
  spaces.toml
  config/discussion_controls.json
  outputs/llm_traces/...
  spaces/<space_name>/...
```

Repository-seeded persona storage (checked in):

```text
<repo_root>/personas/
  social_users.json
  profile_images/*
```

- catalog MUST contain exactly `100` users by default (`schema_version = social_users_v1`).
- each user row MUST include full metadata fields and a resolvable profile image reference under `personas/profile_images/`.
- sites/spaces MUST NOT create or persist user-catalog copies.
- `<site_path>/outputs/` is reserved for site-scoped derived artifacts (for example verbose LLM traces) and MUST NOT be used for space-owned canonical artifacts.

`site.json` contract:
- `schema_version` (`site_scope_v1`)
- `site_name`
- `site_root` (default `.`)
- optional `site_base_url`

Behavior:
- if `site_base_url` exists, use it for canonical/OG/sitemap URLs
- otherwise generated links remain site-relative
- `site_root` SHOULD be stored as a relative path (relative to `<site_path>`) to preserve relocatability

### 5.2 Space-level storage

```text
<site_path>/spaces/<space_name>/
  sources/records/*.json
  sources/artifacts/<source_id>/...
  claims/*.json
  relations/<relation_file_id>.json
  topics/*.json
  profiles/persona-<persona_id>.json
  projections/markdown/*.md
  runs/<run_id>/run.md
  runs/<run_id>/lint.json
  runs/<run_id>/semantic/*.json
  outputs/query/<query_id>/query.json
  outputs/query/<query_id>/manifest.json (only for `mermaid/images/slides/pdf` output modes)
  outputs/persona_profile_history/<persona_id>.json
  outputs/comment_quality/<evaluation_id>/manifest.json
  site/
  raw/snapshots/comment_sections/comment-section-<seed>.json
  .cache/projection-index.db
  imports.lock.md
```

- canonical content artifacts are JSON (`sources/claims/relations/topics`).
- `profiles/` stores canonical persona-profile JSON artifacts (space-scoped).
- `runs/<run_id>/semantic/` stores per-run semantic-generation JSON envelopes when a flow uses run-scoped semantic output artifacts.
- `outputs/` stores deterministic, flow-specific derived artifacts (query manifests, persona profile history, comment-quality evaluation manifests).
- `raw/snapshots/comment_sections/` stores optional comment evidence snapshots in `web-augmented` mode.
- markdown under `projections/markdown/` is optional derived output and is not the canonical build input.

### 5.3 Source artifact storage

```text
<space_root>/sources/artifacts/<source_id>/
  source.pdf
  source.md
  source_extraction.json
  front_page.png
  overview.md
```

- source binaries and previews are space-owned and MUST be stored under `<space_root>/sources/artifacts/`.
- ingest MUST also persist canonical analysis artifacts beside the original binary:
  - `source.md`: extracted markdown used as the default LLM/source-analysis substrate
  - `source_extraction.json`: extraction provenance (`converter_name`, `converter_version`, `status`,
    `quality_status`, hashes, warnings, and artifact-relative pointers)
- source records MUST point to the original binary, `source.md`, and `source_extraction.json`.
- source records MUST persist an explicit `analysis_policy` stating that markdown is the preferred
  analysis artifact and the original binary is the fidelity fallback.
- markdown quality states MUST be explicit (`usable`, `degraded`, `unusable`) so downstream analysis
  never silently treats low-quality extraction as if it were authoritative.
- fidelity-sensitive workflows (tables, figures, equations, layout recovery) MAY read the original
  binary, but only as an explicit fallback or specialized inspection path.
- ingest SHOULD render `front_page.png` at web-preview scale (default max width `840px`, height auto)
  so source-page previews stay readable without oversized assets.
- site-level source artifact roots such as `<site_path>/sources/...` are historical-only and MUST NOT be used for new writes.
- persisted record/site paths SHOULD be relative for relocatability
- avoid persisting machine-absolute paths in user-facing artifacts

### 5.4 Identifier and naming contracts

Canonical ID classes (human-readable + collision-resistant):
- deterministic content IDs:
  - source id (`source_id`): `source-<slug>--<suffix>`
  - claim id (`claim_id`): `claim-<slug>--<suffix>`
  - concept/cluster id (`concept_id`): `concept-<slug>--<suffix>`
  - topic id (`topic_id`): `topic-<slug>--<suffix>`
  - source family id (`family_id`): `family-<slug>--<suffix>`
- execution IDs (invocation-scoped):
  - ingest run id (`run_id`): `run-<utc_timestamp>--<suffix>`
  - query output id (`query_id`): `query-<utc_timestamp>-<slug>--<suffix>`
- stable record IDs:
  - comment uid (`comment_uid`): `comment-<slug>--<suffix>` (write-once, immutable, permalink-stable)
- display ordinal:
  - comment display ordinal (`comment_no`): `pc-###` rendered as `` `#pc-###` `` (display-only; may be renumbered)
- relation edge IDs:
  - `relation_id` is a composite edge key (for example `supports:<src_claim_id>-><dst_claim_id>`), not a `<prefix>-<slug>--<suffix>` entity ID
  - relation edge IDs use the relation-specific grammar in Section 7.1 (Relation persistence/reconciliation contracts and matrix)
  - relation edge IDs are canonical semantic keys and are not required to be filesystem-safe path segments

Page-ID contract:
- canonical page ID field is `topic_id`.
- `narrative_id` is non-canonical and MUST fail fast in canonical readers and validators.

Slug and suffix rules:
- `<slug>` MUST be lowercase kebab-case (`[a-z0-9]+(?:-[a-z0-9]+)*`) derived from title/content intent.
- deterministic content-ID `<suffix>` MUST be deterministic from canonical payload and use lowercase hex digest prefix with minimum length `12` (implementations MAY use longer prefixes).
- execution-ID `<suffix>` MUST be collision-resistant and unique per invocation, with minimum length `10` and URL-safe lowercase `[a-z0-9]` characters; payload determinism is not required.
- `comment_uid` `<suffix>` MUST be unique at write time, with minimum length `10` and URL-safe lowercase `[a-z0-9]` characters; deterministic regeneration is optional, but once written the value MUST NOT change.
- collision handling:
  - deterministic content IDs: writer MUST extend suffix length or append deterministic tiebreak material; never silently overwrite.
  - execution IDs and `comment_uid`: writer MUST regenerate/extend suffix and retry; never silently overwrite.
- IDs MUST remain URL-safe ASCII.
- relation edge IDs are exempt from slug/suffix rules above and MUST follow the relation grammar defined in Section 7.1.

Temporal format contract:
- timestamp fields (`started_at`, `completed_at`, `ingested_at`, `query_timestamp_utc`, `generated_at`, `as_of`, and `citation_count_as_of` when timestamp-valued) MUST use UTC RFC 3339 format with trailing `Z`.
- date-only fields (`date` and `citation_count_as_of` when date-valued) MUST use ISO-8601 `YYYY-MM-DD`.
- `<utc_timestamp>` segments embedded in IDs (for example `run_id`, `query_id`) MUST use compact UTC format `YYYYMMDDTHHMMSSZ`.

Human-readable notation policy:
- prose and UI contracts SHOULD prefer readable labels (`title`, `slug`, `space_name`) over raw IDs.
- user-facing rendering of `space_name`/subspace names MUST apply title-style word casing (each word starts with an uppercase letter), while canonical URL/ID slugs remain lowercase kebab-case.
- when IDs are needed in prose, use named placeholders (`<source_id>`, `<claim_id>`, `<topic_id>`) instead of raw prefix patterns.
- user-facing pages SHOULD display titles first and show machine IDs only in secondary/audit metadata.

Static output expectations:
- source pages: `<space_root>/site/sources/records/<shard>/<source_id>.html`
- claims under `<space_root>/site/claims/<claim_id>.html`
- topics under `<space_root>/site/topics/<topic_id>.html`
- query manifests under `<space_root>/outputs/query/<query_id>/manifest.json` only for non-`markdown` query output modes

URL readability/stability policy:
- canonical URLs MUST embed human-readable ID slugs.
- collision-safe suffixes in IDs MUST remain in URL paths to guarantee uniqueness.
- title changes MAY update display title/metadata, but canonical URL SHOULD remain stable after first publish.
- if URL shape changes are unavoidable, builders SHOULD emit deterministic redirects from old canonical paths.

### 5.5 Registry contract (CLI targeting)

- this contract applies to Python entrypoints under `scripts/` (not shell wrappers)
- space-scoped Python entrypoints MUST require `<space_name>` as first positional argument
- site-scoped Python entrypoints MAY omit `<space_name>`
- no implicit default space
- each `<space_name>` resolves through registry mapping to `<space_root>`

Canonical registry shape (reconstruction mode):
- canonical registry file: `<site_path>/spaces.toml` (site-local authority)
- per-space required fields:
  - `space_name`
  - `space_root` (absolute path or registry-relative path value)
- `space_root` resolution:
  - if absolute, use as-is
  - if relative, resolve against the active registry file directory
- fail fast if `space_name` is unknown or resolved `<space_root>` is unreadable/unwritable as required by the command
- reconstruction/default registries SHOULD persist relative `space_root` values when possible to preserve relocatability

Registry resolution precedence (normative):
1. explicit `--registry-path <path>` (authoritative)
2. otherwise fail fast with usage/configuration error (no implicit default registry path)

Bootstrap command exception (normative):
- this exception applies only to site-bootstrap commands that create or initialize registry state: `create_site.sh` and `create_space.sh` (or their direct Python/bootstrap equivalents).
- `create_site` MUST NOT require a pre-existing `--registry-path`; it creates `<site_path>/spaces.toml` as part of site initialization.
- `create_space` in wrapper mode MAY omit explicit `--registry-path` and MUST target `<site_path>/spaces.toml` derived from `<site_path>`.
- all non-bootstrap registry-backed commands MUST still require explicit `--registry-path` and MUST fail fast when it is missing.

Conflict and fallback behavior:
- each command execution uses exactly one registry file; registry files MUST NOT be merged.
- if explicit `--registry-path` is missing/unreadable/invalid, command MUST fail fast.
- if duplicate `space_name` entries exist inside one registry file, command MUST fail fast.

Legacy compatibility note:
- historical home registry path `~/.sapi/spaces.toml` MAY be supported by dedicated migration/compatibility tooling only.
- wrappers and reconstruction workflows MUST NOT read, merge, or fall back to `~/.sapi/spaces.toml`.

### 5.6 Source metadata extensions (paper-focused)

Paper-source taxonomy:
- `article_kind` allowed values: `empirical`, `theoretical`, `review`, `meta_analysis`, `editorial`

Citation metadata fields:
- `citation_count` (nullable number)
- `citation_count_as_of` (nullable date/timestamp)
- `citation_count_provider` (string; default `unknown` when unavailable)
- `citation_count_confidence` (`unknown`, `low`, `medium`, `high`)

When unknown/unavailable, recovered default values are:
- `citation_count: null`
- `citation_count_as_of: null`
- `citation_count_provider: unknown`
- `citation_count_confidence: unknown`

### 5.7 Site/space scope and subspace metadata contracts

Recovered site-scope contract:
- schema marker: `site_scope_v1`
- canonical file: `<site_path>/site.json`
- keys:
  - `schema_version`
  - `site_name`
  - `site_root`
  - optional `site_base_url`
- `site_root` resolution supports relative paths (resolved from `<site_path>`)
- legacy `<space_root>/site.json` is non-canonical; canonical readers and writers MUST use `<site_path>/site.json` only

Recovered subspace metadata contract:
- file: `<space_root>/subspaces.json`
- schema marker: `space_subspaces_v1`
- top-level keys:
  - `schema_version`
  - `subspaces` (array)
- each subspace entry requires:
  - `space_name` (slug-like)
  - `space_root` (absolute or space-relative path)
  - optional `title`
- invalid schema/version, duplicate `space_name`, missing roots, or nested subspace declarations should fail fast

### 5.8 Lint severity and gate contracts

Severity levels:
- `error`: blocking
- `warning`: non-blocking quality issue
- `info`: advisory

Recovered severity mapping examples:
- `error`:
  - factual sentence missing claim annotation
  - topic reference to missing/non-existent claim ID
  - required canonical field missing
  - invalid canonical ID format
  - stable/final page with unresolved disputed contradiction (`final_disputed_contradiction` for final pages)
- `warning`:
  - source publication date unresolved (`missing_publication_date`) when strict-date mode is disabled
  - weak support (single independent source)
  - sparse backlinks
  - structural hole
  - high ambiguous-match volume
- `info`:
  - ingest/source suggestions
  - optional style/organization suggestions

Gate behavior by workflow key (normative):

| workflow key | operator wrapper path | primary script/entrypoint | gate behavior |
| --- | --- | --- | --- |
| `ingest_source` | `ingest.sh` | `scripts/ingest_source.py` | fail when `error_count > 0`; warnings map to status via threshold policy |
| `create_comments` | `create_comments.sh` | `scripts/create_comments.py` | fail when `error_count > 0`; warnings map to status via threshold policy |
| `generate_profiles` | `generate_profiles.sh` | `scripts/generate_profiles.py` | fail when `error_count > 0`; warnings map to status via threshold policy |
| `build_site` | `regenerate_web.sh` | `scripts/build_site.py` | fail on conversion/link errors (independent of warning threshold) |
| `query` | `query.sh` | `scripts/query.py` | never blocked solely by lint warnings/errors; include lint summary in response metadata |
| `rebuild_topic_collection` | compatibility-only maintenance path | compatibility entrypoint (if present) | fail when `error_count > 0`; warnings map to status via threshold policy |

- `validate.sh` is a lint-engine dispatcher (`scripts/lint.py`) and does not define a separate workflow key; it evaluates one of the workflow keys above.

Lint gate scope note (normative):
- lint-gated workflows (`ingest_source`, `create_comments`, `generate_profiles`, plus compatibility-only `rebuild_topic_collection` when present) apply warning-threshold status mapping when `error_count == 0`.
- non-lint-gated workflows (for example `query`) still emit lint totals in run metadata but MUST NOT fail solely due to lint warnings/errors.

Final-page contradiction resolution (normative):
1. if lint reports `final_disputed_contradiction`, publication workflows remain blocked.
2. final pages MUST NOT be auto-demoted by projection/lint.
3. operator remediation options:
   - resolve the contradiction in canonical claims/relations and rerun projection + lint, or
   - manually reopen lifecycle by running `scripts/set_topic_lifecycle.py <space_name> --topic-id <topic_id> --state stable`, then rerun projection + lint.
4. re-promotion to `final` remains manual-only after contradiction errors are cleared.

Warning-threshold behavior (historical flag name: warning budget):
- default warning threshold is `200`
- if `--warning-budget <int>` is provided, runtime MUST parse a positive integer and use it as the effective warning threshold; invalid values MUST fail fast with configuration error
- if `error_count == 0` and `warning_count > effective_warning_threshold`, status becomes `success_with_warnings`
- if `error_count == 0` and warnings are within threshold, status is `success`
- warning-threshold overflow is non-blocking by default and affects status classification only.

Required lint artifacts (committed runs):
- machine-readable: `<space_root>/runs/<run_id>/lint.json`
- human summary section in `<space_root>/runs/<run_id>/run.md` under `## Lint Summary`
- canonical run artifact container is `<space_root>/runs/<run_id>/`; new writes MUST NOT use root-level `<space_root>/runs/<run_id>.md`
- in strict rollback mode (Section 2.1), terminally failed invocations MUST NOT persist `<run_id>` artifact containers; they MAY emit failure envelopes via command output/stdout/stderr.
- explicit ingest `--force` runs are exempt from strict rollback container cleanup and MAY persist `<run_id>` artifact containers with `status: failed` for forensic inspection.

## 6. End-to-End Operator Workflow

### 6.1 User-facing shell wrappers

Primary shell entrypoints:
- `create_site.sh <site_path> <site_name>`
- `create_space.sh <site_path> <space_name>`
- `ingest.sh <site_path> <space_name> <source_path_or_url> [--force] [--verbose]`
- `create_comments.sh <site_path> <space_name> --count <n> [--verbose] [--comment-user ...] [--comment-page ...] [--comment-seed ...] [--comment-evidence-mode ...]`
- `generate_profiles.sh <site_path> <space_name> [--persona-id <persona_id> ...] [--verbose]`
- `regenerate_web.sh <site_path> [space_name] [--verbose]`
- `query.sh <site_path> <space_name> <question> [--verbose]`
- `validate.sh <site_path> <space_name> [--workflow ...] [--run-id ...]`
- `evaluate_source.sh <site_path> <space_name> <source_path_or_url> [--out <artifact_dir>] [--comments <n>] [--comment-user ...] [--comment-page ...] [--verbose]`

### 6.2 Wrapper-to-entrypoint contract

- wrappers are the primary operator interface and accept `<site_path>` first
- wrappers pass `--registry-path <site_path>/spaces.toml` to registry-backed Python entrypoints
- wrapper-provided site-local registry is authoritative for that invocation
- wrapper mode is the canonical reconstruction mode and documentation/examples SHOULD use it as the default invocation style
- wrapper invocations MUST NOT read or merge `~/.sapi/spaces.toml`
- wrappers SHOULD expose/forward common runtime flags (for example `--llm-backend`, `--llm-model`, `--llm-reasoning-effort`, `--warning-budget`, `--mock-llm`) to Python entrypoints.
- wrappers and Python entrypoints MUST NOT rely on environment variables for semantic/pipeline flow behavior.
- for space-scoped operations, wrappers pass `<space_name>` as the first positional argument to the Python entrypoint
- for site-scoped operations, wrappers invoke site-level entrypoints that do not require `<space_name>`
- `validate.sh` forwards workflow/run-id flags to `scripts/lint.py`
- bootstrap wrappers (`create_site.sh`, `create_space.sh`) are the only commands allowed to run without an operator-supplied `--registry-path`; they MUST initialize/use `<site_path>/spaces.toml` directly.
- wrapper argument normalization for `ingest.sh`:
  - canonical rollback-override flag is `--force` (no alias)
  - removed flags `--source-only` and `--query-only` MUST fail fast with usage error
- wrapper argument normalization for `create_comments.sh`:
  - canonical wrapper flags are `--count`, `--comment-user`, and `--comment-page`
  - removed non-canonical inputs `--user`, `--page`, and positional count argument `<n>` MUST fail fast with a usage error

Recovered mapping examples:
- `ingest.sh <site_path> <space_name> ...` -> `scripts/ingest_source.py <space_name> ... --registry-path <site_path>/spaces.toml`
- `query.sh <site_path> <space_name> ...` -> `scripts/query.py <space_name> ... --registry-path <site_path>/spaces.toml`
- `create_comments.sh <site_path> <space_name> --count <n> ...` -> `scripts/create_comments.py <space_name> --count <n> ... --registry-path <site_path>/spaces.toml`
- `generate_profiles.sh <site_path> <space_name> ...` -> `scripts/generate_profiles.py <space_name> ... --registry-path <site_path>/spaces.toml`
- `evaluate_source.sh <site_path> <space_name> <source> ...` -> `scripts/evaluate_source.py <space_name> <source> ... --registry-path <site_path>/spaces.toml`

Canonical wrapper/script/workflow-key map (normative):

| wrapper | entrypoint | workflow key |
| --- | --- | --- |
| `ingest.sh` | `scripts/ingest_source.py` | `ingest_source` |
| `query.sh` | `scripts/query.py` | `query` |
| `create_comments.sh` | `scripts/create_comments.py` | `create_comments` |
| `generate_profiles.sh` | `scripts/generate_profiles.py` | `generate_profiles` |
| `regenerate_web.sh` | `scripts/build_site.py` | `build_site` |
| `validate.sh` | `scripts/lint.py` | dispatcher only (`--workflow` selects workflow key) |
| `evaluate_source.sh` | `scripts/evaluate_source.py` | `evaluate_source_quality` |

Expected order:
1. create site
2. create space(s)
3. ingest source(s) (store source, generate claims/relations/topics, reconcile links, deterministic build/lint)
4. optionally generate comments
5. optionally generate persona profiles/history
6. optionally run full `regenerate_web.sh` for whole-site verification/catch-up rebuild
7. run queries
8. run validation/lint gate checks
9. run `evaluate_source.sh` when producing user-facing acceptance artifacts

### 6.3 User-facing source evaluation harness (normative)

Purpose:
- provide a single operator command that runs a source through the core pipeline and emits a human-readable artifact folder for quality review.

Canonical command:
- `evaluate_source.sh <site_path> <space_name> <source_path_or_url> [--out <artifact_dir>] [--comments <n>] [--comment-user ...] [--comment-page ...] [--verbose]`

Execution contract:
- wrapper MUST invoke ingest for the provided source.
- wrapper MUST run validation (`validate.sh`) and include lint outcomes in artifacts.
- if `--comments <n>` is provided and `n > 0`, wrapper MUST run comment generation and include comment-review artifacts.
- wrapper MUST run strict query mode and include `query_answers/strict.md` in every evaluation pack.
- default invocation without additional query-mode arguments MUST emit strict-only query artifacts.
- wrapper MAY run additional exploratory/comparative queries only when explicitly requested; strict-mode output remains mandatory.

Artifact location contract:
- if `--out` is provided, write artifacts under that directory.
- otherwise default to `<space_root>/outputs/evaluations/<evaluation_id>/`.
- each run writes a single evaluation folder with a deterministic manifest identifier.

Human-readable artifact contract (primary):
- `README.md` (what was executed, source input, timestamps, command-line arguments)
- `summary.md` (quality checklist, pass/fail gates, notable warnings, next actions)
- `ingest_run.md` (ingest run summary, changed counts, links to canonical run artifacts)
- `query_answers/strict.md` (and additional query markdown outputs when generated)
- `comments_review.md` (present when comments requested; includes per-page/persona counts and representative thread excerpts)
- `lint_summary.md` (human-readable lint totals/findings and gate decision)
- `site_links.md` (links to rebuilt site pages relevant for manual review)

Machine-readable companion artifacts (secondary):
- `manifest.json` (artifact index, run IDs, workflow statuses, paths)
- copied or linked `lint.json` and query manifest JSONs when available

Readability rule:
- markdown artifacts are the primary review interface for operators.
- JSON artifacts are supporting diagnostics and MUST NOT be the only output channel.

Mechanical verification contract:
- repository MUST include deterministic integration tests for `evaluate_source.sh` in mock-LLM mode.
- tests MUST assert required markdown artifact files exist and contain minimally expected contract sections/keys.
- tests MUST assert `manifest.json` references all emitted markdown artifacts and run IDs.
- tests MUST include both default (no comments) and comments-enabled harness runs, including invalid-argument failure cases.

## 7. Pipeline Contracts by Subsystem

Scope note:
- Section 7 covers pipeline behavior only (ingest/query/social generation and post-processing).
- canonical file layout, ID rules, scope metadata, and lint-gate policy live in Section 5.

Cross-subsystem generation pattern:
- each semantic flow uses a checked-in generation spec markdown file that points to schema + output JSON + context roots.
- `.skills/*.skill` orchestrates how flows are run; `ai_flows/generation_specs/*.md` defines what semantic JSON must be produced.
- for semantic output contracts, generation specs are authoritative if any conflict exists with skill text/defaults.
- semantic output generation is LLM-only and JSON-only.
- all semantic flows MUST use the shared schema-repair retry loop from Section 2.1 (`max_repair_loops=3` default). Terminal failures use strict rollback by default; ingest `--force` is the only rollback override.
- markdown projections (if enabled) and HTML are produced in deterministic post-processing stages without LLM calls.
- site HTML build consumes canonical JSON artifacts directly.
- site/projection trigger behavior is flow-specific and governed by Section 2.2 (not all semantic flows trigger a full site build).
- all semantic generation flows MUST use the same LLM input envelope:
  - `schema_path` to a JSON schema in the repository
  - `output_json_path` where the generated JSON artifact must be written
  - `context_paths[]` with filesystem links/paths the LLM is allowed to use as evidence
- generation prompts SHOULD pass filesystem pointers, not pre-expanded semantic dumps, except where explicitly required by a schema contract.

### 7.1 Ingest pipeline

Inputs:
- local file or URL
- optional overrides (`title/date/family/canonical id`)

Core steps:
1. preflight: resolve `<space_root>`, acquire ingest lock, initialize run envelope (`run_id`, timing/runtime metadata)
2. fetch/read bytes, normalize to PDF when needed, and persist source artifact under `<space_root>/sources/artifacts/<source_id>/...` with source record metadata
   - when media type, file suffix, or URL path indicates PDF (`application/pdf` / `.pdf`), ingest MUST verify payload bytes begin with `%PDF-`; otherwise fail ingest before artifact persistence
   - ingest MUST also write `source.md`, `source_extraction.json`, and source-record `analysis_policy`
     before semantic extraction begins
3. extract text and run `ingest_extraction` generation spec with source path + hints + strict JSON schema
   - semantic source reading MUST prefer `source.md` and inspect `source_extraction.json` for quality/provenance
     before falling back to the original binary
4. validate and persist canonical claim/relation outputs from ingest extraction
5. run `topic_generation` generation spec using source + claim context; validate and deterministically persist `0..n` canonical topic JSON pages when cross-source concepts are supported
6. run deterministic link reconciliation so source/claim/topic artifacts are mutually connected and all required references resolve
   - same pass SHOULD also persist curated `external_related_links[]` plus `related_link_enrichment`
     metadata on source records
7. run deterministic projection/reindex/site build from canonical JSON (or mark run `build_deferred` in reconstruction bootstrap mode)
8. run lint gate, write run record, and always release lock

Run envelope model for multi-semantic commands (normative):
- run metadata is command-scoped (`run_id` identifies one wrapper/entrypoint invocation).
- `flow_key` identifies the command/pipeline (`ingest_pipeline`, `query_pipeline`, `comment_section_pipeline`, `persona_profile_pipeline`).
- `semantic_flows[]` records an ordered unique list of semantic generation flow keys executed at least once during that command invocation.
- `semantic_flow_invocation_counts` records per-flow invocation counts for the same command invocation.
- normal ingest writes `semantic_flows: [ingest_extraction, topic_generation]` and `semantic_flow_invocation_counts: {ingest_extraction: 1, topic_generation: 1}`.
- ingest does not support semantic-flow bypass flags.

Terminal failure behavior (normative):
- if `ingest_extraction` or `topic_generation` exhausts repair retries, command MUST fail.
- default mode: failed ingest invocations MUST rollback invocation-scoped writes before exit.
- default rollback scope includes source artifact/record writes, claim/relation/topic writes, deterministic projection/build outputs created by the same invocation, and invocation-scoped run/lint artifacts.

Force mode for ingest (normative):
- explicit flag: `--force`
- when `--force` is enabled, ingest MAY skip invocation rollback on terminal failure and preserve already-written artifacts.
- when rollback is skipped, run metadata MUST include `force_mode: true` and `rollback_skipped: true`.
- `--force` MUST NOT relax schema validation or retry limits, and MUST NOT enable deterministic semantic fallback.

Comment-enrichment policy during ingest (normative):
- default ingest workflow MUST NOT invoke comment section generation automatically.
- operators MAY run comment generation as an explicit follow-up step after ingest success (or via an explicit opt-in ingest mode if implemented).
- comment enrichment targets source/claim/topic pages and MUST follow Section 7.6 contracts.

Reconstruction bootstrap-mode contract:
- bootstrap mode exists only to preserve Phase 2 -> Phase 3 sequencing in Section 12 while rebuilding missing modules.
- runs emitted in bootstrap mode MUST include `build_deferred: true` in run metadata and SHOULD use `status: success_with_warnings` with reason `build_deferred`.
- before Definition-of-Done validation, all deferred ingest runs MUST be backfilled through deterministic projection/site build.

Hard prompt input rule:
- ingest prompt MUST pass source paths/metadata hints
- ingest prompt MUST NOT pass precomputed semantic claim dumps as a replacement for reading

Ingest output contract (minimum):
- `source_date_inference` (`date`, `origin`, `confidence`, optional rationale)
- source semantic metadata
- `claims` with optional claim-local evidence mirrors
  - `claims[].text` SHOULD be truth-apt propositions about source content (state-of-world or formal-result claims), not publication-process narration
  - prefer proposition rewrites over reportive framing (rewrite `the paper argues that X` to `X`)
  - claim-level `evidence_excerpts` are optional mirrors only; canonical evidence pages are driven by top-level `evidence_items`
- required top-level `evidence_items` (`0..n`) as canonical evidence records
  - each evidence item MUST include `evidence_id`, `title`, `excerpt`, `overview`, `evidence_type`, `claim_refs[]`, and `source_id`
  - `evidence_items` MUST represent concrete support artifacts (measurement values/statistics, theorem/proof/derivation steps, equations, table/figure findings, formal argument fragments)
  - `evidence_items` MUST NOT be generic claim paraphrases or publication-process narration (`the paper claims...`, `the article argues...`)
  - deterministic ingest code MUST validate references and required fields but MUST NOT derive evidence IDs/titles/excerpts from claim text
- `relations`
- `summary`, `warnings`
- required `source_dossier` for source-page long-form reading support:
  - `summary_short` (reader-facing abstract for cards + hero)
  - `summary_long` (substantive overview/commentary, target minimum depth roughly 900+ chars)
  - `sections[]` with `heading`, `body`, `grounding_claim_ids`
    - target section count: `5..8` on high-quality outputs
- optional `source_structure_outline` (ordered high-level section headings/signals from the source, when detected)

Recovered `ingest_source.py` option surface (high-signal):
- `--registry-path`
- `--source-title`, `--source-url`, `--source-file`
- `--source-media-type`, `--source-type`, `--source-date`
- `--source-family-id`, `--canonical-identifier`
- `--parent-run-id`
- `--enable-source-index`
- `--force` (ingest rollback override; preserves partial artifacts on failure)
- `--require-source-date`
- `--llm-reasoning-effort {low,medium,high,xhigh}`

Date policy:
- explicit `--source-date` overrides model inference
- default mode: if no explicit date and no valid inferred date, persist `date: null` and continue ingest
- missing-date continuation MUST emit warning code `missing_publication_date`
- when `date: null`, `source_date_inference` SHOULD use `origin: unknown` and `confidence: unknown` (or lowest supported confidence bucket)
- strict mode (optional): `--require-source-date` fails ingest when publication date cannot be resolved
- track both `date` (publication) and `ingested_at` (ordering)

Canonical `source.title` resolution priority:
1. `--source-title`
2. source metadata title signals
3. first plausible in-source title line
4. URL/file-stem fallback
5. `Untitled Source`

`source.display_title` contract (AI/UI title):
- ingest extraction semantic output MUST include `source.display_title` (schema-required field).
- `source.display_title` SHOULD be a high-quality post-style title (target `4..12` words, typically
  `12..120` chars) summarizing the core claim/theme.
- `source.display_title` MUST avoid raw filenames, source IDs, URL fragments, and hash-like metadata.
- writers/readers MUST resolve display titles with strict-first fallback:
  1. strict quality pass over candidates (`source.display_title`, `source.article_title`, persisted values)
  2. relaxed compatibility pass for short legacy titles
  3. humanized `source_id` fallback
  4. `Untitled Source`
- UI surfaces (source tabs, source pages, feeds, search labels) MUST render `source.display_title`
  when available and MUST NOT expose storage slugs as the primary source label.

Locking policy:
- lock file: `<space_root>/.locks/ingest.lock`
- exclusive create
- always release on success/failure
- stale lock with dead PID auto-recovers
- live PID lock fails fast

Removed ingest bypass flags:
- `--source-only` and `--query-only` are removed and MUST fail fast with usage errors.
- ingest always runs `ingest_extraction` and `topic_generation` when ingestion succeeds past preflight.

Relation persistence/reconciliation contracts:
- relation IDs are edge keys and intentionally use a relation-specific grammar (not the generic entity/run ID format in Section 5.4).
- undirected relation IDs sort claim IDs lexicographically (`contradictory`, `similar`)
- directed relation IDs preserve semantic direction (`supports`, `derived_from`, `falsifies`)
- `falsifies` checks use `falsify`, `not_falsify`, `ambiguous`
- semantic output `status: closed` is normalized on write to canonical `status: resolved`
- relation records track `below_040_streak`, `last_evaluated_run_id`, and contradiction confidence banding

Relation filesystem key mapping (normative):
- writers MUST compute `relation_file_id = rel-<sha256_hex(relation_id)>` using UTF-8 bytes of `relation_id` and lowercase hex output.
- relation records MUST be written at `<space_root>/relations/<relation_file_id>.json`.
- each relation record MUST store both `relation_id` (semantic key) and `relation_file_id` (storage key).
- readers MUST treat `relation_id` as the semantic source of truth and `relation_file_id` as a derived storage key.
- on read or write, if persisted `relation_file_id` does not match recomputed hash of `relation_id`, validation MUST fail.

Relation-type matrix (normative):

| relation_type | directed | semantic reading | canonical ID formula |
| --- | --- | --- | --- |
| `contradictory` | no | claim A contradicts claim B (symmetric) | `contradictory:<min_claim_id>|<max_claim_id>` |
| `similar` | no | claim A is similar to claim B (symmetric) | `similar:<min_claim_id>|<max_claim_id>` |
| `supports` | yes | `<src_claim_id>` provides support for `<dst_claim_id>` | `supports:<src_claim_id>-><dst_claim_id>` |
| `derived_from` | yes | `<src_claim_id>` is derived from `<dst_claim_id>` | `derived_from:<src_claim_id>-><dst_claim_id>` |
| `falsifies` | yes | `<src_claim_id>` falsifies `<dst_claim_id>` | `falsifies:<src_claim_id>-><dst_claim_id>` |

Normalization rules:
- for undirected types, writer MUST lexicographically sort claim IDs before ID generation.
- for directed types, writer MUST preserve `(src_claim_id, dst_claim_id)` order from semantic output and MUST NOT reorder lexicographically.
- duplicate writes with the same canonical relation ID MUST merge/update the same `<relation_file_id>` record.

### 7.2 Reference extraction and linking

For reference-heavy sources:
1. extract references at ingest from the markdown analysis artifact when available; only fall back to raw binary decoding when extraction quality is explicitly degraded/unusable
2. normalize to structured rows (`title/authors/year/doi/arxiv/url`)
3. match to ingested local sources in same space
4. persist `linked_source_ids`
5. backfill links in older records on new ingest
6. derive curated `external_related_links[]` from canonical identifiers, source locator, and allowlisted external reference URLs

External related-link contract (normative):
- `external_related_links[]` are distinct from canonical source citations/references; they are reader-facing
  online destinations surfaced on source/topic/claim pages.
- each related-link row MUST persist:
  - `title`
  - `url`
  - `domain`
  - `link_type`
  - `quality_status`
  - provenance object (`origin`, `source_field`)
  - rationale/summary text when available
  - confidence/quality cues
- allowed default link classes are:
  - `canonical_paper` (for DOI landing pages)
  - `primary_source` (original source URL)
  - `research_index` (for example arXiv or Papers With Code)
  - `encyclopedia` (for example Wikipedia)
  - `repository`
  - `discussion_forum`
- enrichment MUST be deterministic and auditable; page rendering MUST NOT perform implicit web search.
- enrichment MUST de-duplicate by normalized URL and prefer higher-trust rows over lower-trust duplicates.
- unsupported or low-signal domains SHOULD be rejected rather than rendered.
- source records MUST persist `related_link_enrichment` metadata with `status`, `sources`, warnings,
  and skip reason when no curated links qualify.

UI requirement:
- source page shows references and linked local source pages when matched
- source, topic, and claim pages SHOULD show `External Related Links` sections when curated links exist.
- topic and claim pages MUST inherit/aggregate curated external links deterministically from linked sources,
  with provenance cues indicating which source(s) supplied each link.

### 7.3 Query pipeline

- query uses structured retrieval context (claims/sources/relations)
- query semantic generation MUST be driven by a checked-in generation spec that declares `schema_path`, `output_json_path`, and `context_paths[]`
- output is strict JSON
- include contradictions/falsification signals and retrieval counts
- query views/artifacts are rendered deterministically from query JSON outputs
- query flow MUST NOT mutate canonical artifacts under `sources/`, `claims/`, `relations/`, `topics/`, or `profiles/`
- query flow writes are limited to `outputs/query/<query_id>/...` plus run/lint metadata artifacts
- query flow MUST NOT trigger ingest-style projection/site rebuild
- if `query_synthesis` exhausts repair retries or deterministic query artifact assembly fails, command MUST fail and rollback invocation-scoped query outputs and run/lint artifacts for that invocation.

Recovered mode semantics:
- `strict`: only verified claims without open contradictions where `confidence >= 0.40`
- `exploratory`: includes unverified claims
- `comparative`: emphasizes disagreement/contrast

Recovered default retrieval budgets:
- `strict`: `max_claims=120`, `max_sources=40`
- `exploratory`: `max_claims=200`, `max_sources=60`
- `comparative`: `max_claims=160`, `max_sources=80`

Recovered query option surface (high-signal):
- `--registry-path`
- `--mode {strict,exploratory,comparative}`
- `--output-format {markdown,mermaid,images,slides,pdf}`
- `--question`
- `--max-claims`, `--max-sources`
- `--scope {default,deep}`
- `--include-disputed`
- `--include-warnings` / `--no-include-warnings`
- `--llm-reasoning-effort {low,medium,high,xhigh}`

Recovered query defaults:
- `include_disputed`: default `false` in `strict`, `true` in non-strict modes
- `include_warnings`: default `true`

Mode/flag compatibility contract (normative):
- `strict` mode and `include_disputed=true` is an invalid combination.
- if the operator explicitly passes `--mode strict --include-disputed`, the command MUST fail fast with a usage/configuration error before retrieval/generation.
- if `--mode strict` is selected without explicit `--include-disputed`, effective `include_disputed` is `false`.
- `--include-disputed` is valid only for non-strict modes (`exploratory`, `comparative`).

Query result shape (high-signal keys):
- `query_id`
- `answer`
- `claims_used`, `sources_used`
- `retrieval_counts`
- `contradictions_considered`
- `falsification_signals`
- `omitted_due_to_budget`
- `mode`, `scope`
- `run_id`, `query_timestamp_utc`
- `citation_coverage`
- optional `ancestor_pages_used`, `inherited_conflicts`
- optional `synthesis_claim_ids`
- `lint_summary`
- `execution` (`execution_mode`, `llm_attempt_count`, `reasoning_effort`, fingerprints)
- `manifest_path` (required for `mermaid/images/slides/pdf`; MUST be `null` or omitted for `markdown`)
- `warnings`

Artifact output contract (`mermaid/images/slides/pdf`):
- for `mermaid/images/slides/pdf`, write manifest at `<space_root>/outputs/query/<query_id>/manifest.json`
- `<query_id>` in path and manifest MUST match the canonical query id contract
- `markdown` output mode MUST NOT emit an artifact manifest; query JSON `manifest_path` MUST be `null` or omitted
- artifact assembly MUST be deterministic from query JSON + renderer templates (no additional LLM generation step)
- required manifest keys: `query_id`, `mode`, `run_id`, `question`, `claims_used`, `sources_used`, `artifacts`, `artifact_hashes`
- artifact rows:
  - `mermaid`: include `diagram.mmd` and optional rendered `diagram.svg`/`diagram.png`, plus `claim_ids`
  - `images`: include `file`, `title`, `alt_text`, `claim_ids`
  - `slides`: include `deck.md`, `deck.html` (optional `deck.pdf`) plus per-slide `claim_ids`
  - `pdf`: include generated file metadata plus `claim_ids`

Citation coverage policy by mode:
- `strict`: target factual-sentence claim coverage `>= 90%`
- `exploratory` and `comparative`: target factual-sentence claim coverage `>= 70%`

Deterministic truncation policy:
- sort primarily by retrieval rank (descending relevance)
- tie-break by lexical canonical ID order
- always populate `omitted_due_to_budget` when truncation occurs

### 7.4 Social users and persona catalog

Seeded catalog requirements:
- persona catalog is checked into repository at `<repo_root>/personas/social_users.json`
- default catalog cardinality is exactly `100` users
- runtime user generation for sites/spaces is disabled; no per-site/per-space catalog creation
- profile photos are checked into `<repo_root>/personas/profile_images/*.jpg`

Primary catalog file:
- `personas/social_users.json`
- schema: `social_users_v1`
- keys: `schema_version`, `count`, `generated_at`, `users`

Recovered user-row fields (high signal):
- `persona_id`, `display_name`, `full_name`, `account_status`, `stance_profile`
- `personality`, `biography`, `biography_profile`, `short_cv`
- `interests`, `hot_topics`, `anger_topics`
- `prompt_fields` (`core_belief`, `argument_style`, `tone`, `evidence_preference`)
- optional `liked_spaces` filtered to known site/space IDs
- required `profile_image_path` (repo-relative `.jpg` path under `personas/profile_images/`)
- required `profile_image_prompt` used for persona-image generation
- derived companion thumbnail path `profile_image_thumb_path` (same basename with `-thumb.jpg` suffix, under `personas/profile_images/`)

Normalization rules:
- derive `name_slug` from `full_name` by lowercasing and joining alphanumeric tokens with `-`
- `persona_id` matches slug pattern `[a-z0-9][a-z0-9_-]*` and must be unique
- `persona_id` MUST equal `persona-<name_slug>` derived from `full_name`
- `profile_image_path` MUST equal `personas/profile_images/<name_slug>.jpg` derived from `full_name`
- rows missing `persona_id` or carrying legacy `id` fields MUST fail validation
- `biography` MUST be written in first person voice from the persona's perspective.
- `biography` SHOULD be high-signal and usually target `90..180` words (`220` hard upper bound) so persona behavior is specific without becoming verbose.
- `biography` SHOULD cover the persona's core worldview, evidence/decision style, priorities, and friction points.
- `biography_profile` is required for profile-page display copy and SHOULD be distinct from `biography`.
- `biography_profile` MUST also be written in first person voice from the persona's perspective.
- `biography_profile` SHOULD be flavorful public-profile prose and usually target `25..120` words (`160` hard upper bound).
- `short_cv` is required and MUST be a non-empty list of concise role/study timeline entries suitable for profile-page display.
- `short_cv` entries MUST use fictional organizations and educational institutions (no real-world entities).
- biography/topic fields normalized for minimum richness
- `profile_image_path` MUST resolve to an existing `.jpg` image file at runtime
- `profile_image_thumb_path` SHOULD exist alongside `profile_image_path` as a smaller square avatar image.
- `profile_image_prompt` MUST request a photorealistic single-person image that reflects the biography and stance.
- `profile_image_prompt` MAY vary scene and appearance details (for example at home, on vacation, in space, with a funny hat, bald) while keeping identity cues consistent with the biography.
- catalog `count` MUST equal the number of user rows and SHOULD be `100` in default checked-in seed

Catalog loading behavior:
- all sites/spaces load users from `<repo_root>/personas/social_users.json`
- implementations MUST NOT write or mirror catalogs under `<site_path>` or `<space_root>`

### 7.5 Persona profile pages and accountability history

Scope model (normative):
- persona identity/catalog is site-shared (Section 7.4), but persona profile page artifacts and accountability history are space-scoped.
- a multi-space site MAY contain one profile page per `(space_name, persona_id)` pair.
- profile/history metrics MUST NOT aggregate across spaces unless a separate explicit site-rollup workflow is defined.

Profile page generation:
- semantic persona-profile page generation MUST be driven by a checked-in generation spec that declares `schema_path`, `output_json_path`, and `context_paths[]`
- operator wrapper/entrypoint path: `generate_profiles.sh` -> `scripts/generate_profiles.py`
- canonical record: `profiles/persona-<persona_id>.json`
- optional projection: `projections/markdown/persona-<persona_id>.md`
- page type: `persona_profile`
- includes identity/viewpoint/debate-style sections, profile biography/CV sections, and profile image link

Projection emits `persona_profiles` stats:
- `generated`, `updated`, `reused`, `pages`, `topic_ids`
- `accountability.personas`
- `accountability.history_generated`
- `accountability.history_updated`
- `accountability.history_reused`
- all `persona_profiles` and `accountability.*` counters in this section are scoped to the current `<space_name>` execution.

Profile history persistence:
- directory: `<space_root>/outputs/persona_profile_history/`
- file: `<persona_id>.json`
- schema: `persona_profile_history_v1`
- keys: `schema_version`, `space_name`, `persona_id`, `entries`

History entry keys:
- `as_of`
- `comments_total`
- `unsupported_claim_rate`
- `retraction_rate`
- `forecast_accuracy`

History update semantics:
- first write creates one entry
- same-day rerun in the same `<space_name>` overwrites last entry only when metrics changed
- new-day appends only when non-date metrics changed (space-local comparison)
- unchanged metrics count as reused/no-write
- profile generation SHOULD run after optional comment injection so metrics reflect latest discussions

### 7.6 Comment section generation and rendering

Targeting and preflight:
- `create_comments.py` supports constrained targeting by user/page plus random mode
- preflight validates content inventory and eligible pages
- failure when no target pages are eligible
- comments are enabled for topic/source/claim pages
- semantic comment-section generation MUST be driven by a checked-in generation spec that declares `schema_path`, `output_json_path`, and `context_paths[]`
- canonical comment-generation flow key is `comment_section_generation`

Comment subsystem naming contract (normative):
- canonical namespace prefix is `comment_section_*` for schema versions, rubric IDs, and context-version markers.
- `persona_comment_*` names are non-canonical and MUST fail fast in canonical readers, validators, and examples.

Batched comment-section generation contract (normative):
- comment generation MUST produce a full page comment section JSON artifact in exactly one LLM invocation per target page.
- each semantic invocation MUST persist one run-scoped semantic artifact at `runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json`.
- requested `--count` MUST be between `5` and `50` (inclusive); values outside this range MUST fail fast with usage/configuration error.
- if multiple target pages are selected, the system SHOULD run one batched generation per page (instead of one comment at a time).
- batched output MUST support nested thread structure in one response using explicit parent references.
- comments flow execution budget is one semantic attempt per target page (`max_repair_loops=0`); invalid JSON/schema output fails fast.

Batched output shape requirements:
- top-level output includes at least `page_ref`, `requested_count`, and `comments[]`.
- each generated comment includes `persona_id`, body content, turn metadata (when present), `parent_ref`, and `score_assessment`.
- `parent_ref` MAY be `null`, an existing `comment_uid`, or a generated in-batch draft reference.
- writer MUST resolve in-batch draft references to canonical `comment_uid` values during merge/normalization.
- `score_assessment.score` MUST be integer `[-30, 30]`; `score_assessment.rationale` MUST be non-empty neutral justification text.

Recovered comment CLI surface (high-signal):
- required `--count` (range `5..50`)
- `--comment-user` (expects `persona_id`)
- `--comment-page`
- `--comment-seed`
- `--comment-evidence-mode {canonical-only,web-augmented}`
- `--llm-reasoning-effort {low,medium,high,xhigh}`
- removed non-canonical inputs `--user`, `--page`, positional count `<n>`, and `--comment-web-evidence` MUST fail fast

Default target-page behavior when page filter omitted:
- default mode targets parseable topic pages only (safety/performance default)
- source/claim page commenting remains supported via explicit `--comment-page` targeting
- exclude the space home page
- exclude persona profile pages

Comment-generation context contract:
- generation context MUST provide filesystem pointers to the target page being commented on (canonical page JSON and render/projection context when available).
- generation context MUST provide filesystem pointers for selected commenters' profile context JSON:
  - use `<space_root>/profiles/persona-<persona_id>.json` when present
  - otherwise use repository-seeded persona catalog context from `<repo_root>/personas/social_users.json`
- generation context MAY include recent page-local thread/history context to improve reply continuity.

Recovered projection/build outputs tied to comment flow:
- `comment_targets` object:
  - `user_filters`
  - `effective_count`
  - `defaulted`
- `site_index` path emitted post-build
- `create_comments.sh` MUST execute the required deterministic post-processing from Section 2.2 (comment merge/normalization, affected-page projection, and affected feed/index refresh as configured) before successful exit.
- a separate `regenerate_web.sh` invocation is optional for explicit full-site rebuilds and MUST NOT be required for comment-flow correctness.

Evidence mode contract:
- primary flag: `--comment-evidence-mode {canonical-only,web-augmented}`
- `canonical-only`: generation MUST use only declared repository/site context; no web search; no evidence snapshot written.
- `web-augmented`: generation MAY perform web searches to gather additional background context and MUST write evidence snapshot + provenance annotations for any external material used.

Evidence snapshot contract:
- path: `raw/snapshots/comment_sections/comment-section-<seed>.json`
- schema: `comment_section_evidence_snapshot_v1`
- when `web-augmented` mode is used, snapshot MUST include at least `(query, source_url, accessed_at, comment_refs[])` for each external evidence item.

Page discussion controls:
- file: `<site_path>/config/discussion_controls.json`
- schema: `comment_section_discussion_controls_v1`
- top keys: `defaults`, `pages`
- non-canonical schema IDs such as `persona_discussion_controls_v1` are removed and MUST NOT be imported
- control keys:
  - `enabled`
  - `roster`
  - `max_turns`
  - `reply_chance`
  - `max_depth`
- non-canonical `persona_discussion_*` keys are removed and MUST NOT be imported
- page-local overrides MUST be read from canonical page JSON metadata (`discussion_controls`) and new writes MUST target canonical page JSON, not markdown
- markdown frontmatter-only controls are non-canonical and MUST fail fast instead of being imported into effective controls
- precedence: defaults -> per-page controls -> canonical page JSON metadata
- missing file or unknown/mismatched schema => safe empty controls fallback

Comment line/thread contract:
- every comment row has immutable `comment_uid` used for anchors/permalinks
- display ordinal `pc-###` is sequential within the rendered page and is not a stable identifier
- canonical comment payload links personas by `persona_id`
- rendered persona attribution links MUST resolve to the space-scoped canonical persona-profile page for that `persona_id`; markdown projections MAY use relative links (for example `./persona-<persona_id>.md`) as an optional non-canonical projection format
- replies include explicit `parent_comment_uid` reference
- non-canonical parent references such as ordinal `pc-###` MUST fail fast instead of being normalized
- rebuttals include steelman acknowledgment before rebuttal text
- optional `claim_badges` suffix includes claim status/confidence
- comment body text SHOULD remain natural/social in style and avoid leaking internal metadata
- claim badge status vocabulary: `verified`, `unverified`, `disputed` (fallback default `unverified`)

Turn marker contract:
- canonical inline marker: `<<turn:{...}>>`
- legacy HTML comment markers are non-canonical and MUST fail fast

Turn classification and validation (normative):
- argumentative turns (positions `support`, `challenge`, `rebuttal`, `synthesis`) are used for factual claims, evidence disputes, and adjudicated argumentation.
- non-argumentative social turns are lightweight conversational replies and MAY omit turn markers; if a marker is present, `position` MUST be `social`.

Strict turn schema validation (argumentative turns only):
- `position` in `{support, challenge, rebuttal, synthesis}`
- non-empty `claim_ids`, each value MUST be a valid `claim_id`
- optional `counter_claim_ids`, each value MUST be a valid `claim_id`
- non-empty `evidence_refs`, every ref is `claim:<claim_id>` or `source:<source_id>`
- `confidence` numeric, finite, and in `[0.0, 1.0]`
- rebuttal turns MUST include `strongest_opposing_point_ack`; removed alias `steelman_before_rebuttal` is non-canonical and MUST fail fast

Lightweight social-turn contract:
- social turns MUST NOT introduce new factual claims or adjudicated claim-vs-claim arguments.
- for social turns, `claim_ids`, `counter_claim_ids`, and `evidence_refs` MAY be omitted or empty.
- for social turns, `confidence` MAY be omitted; if present it MUST still be finite and in `[0.0, 1.0]`.
- if a turn contains factual assertions requiring citation/dispute handling, writer MUST emit an argumentative turn and satisfy the strict schema above.

Anti-gaming/generation-isolation constraint:
- comment-generation prompts/context MUST NOT expose scoring/adjudication rubric details used for evaluation
- generation context is audited under `comment_section_generation_context_v1`

Merge/normalization contract for existing comment sections:
- merge existing and new lines
- preserve existing `comment_uid` values for surviving comments
- assign new `comment_uid` only to newly created comments
- recompute display ordinals to sequential `pc-###` per page render
- reject legacy ordinal parent references such as `pc-###`; replies must use `parent_comment_uid` or in-batch `draft-N` refs
- never rewrite previously persisted `comment_uid` values
- rebuild summary/footer blocks from normalized rows

Moderator and outcome summary contract:
- comment-generation artifacts MAY include moderator/outcome metadata for auditing.
- static comment-page rendering MUST NOT display moderator/outcome summary blocks in page body.

Projection comment stats (high-signal keys):
- `requested`, `added`
- `comments_by_page`, `comments_by_user`
- `page_controls` (`configured_pages`, `active_pages`, `disabled_pages`, `limited_pages`)
- `turn_schema` (`validated_comments`, `positions`, historical `timeline`)
- `thread_outcomes`
- `adjudication` (`rubric_id=comment_section_adjudication_v1`, rows/checks/pages_with_failures)
- `generation_isolation` (`schema_version=comment_section_generation_context_v1`, leak counts)
- `evidence_mode`
- `evidence_snapshot`

Historical memory schema marker:
- canonical: `comment_section_memory_v1`

Comment UI affordances (historical UX contract):
- threaded tree rendering
- avatar and full-name attribution (avatar SHOULD use the smaller `profile_image_thumb_path` companion image)
- score-based collapse behavior with expand/collapse toggles
- thread expansion state keyed by `comment_uid` (not `pc-###`)

### 7.7 Comment quality evaluation harness

Benchmark artifact:
- `sapi/benchmarks/comment_quality_benchmark_v1.json`
- schema: `comment_section_quality_benchmark_v1`
- benchmark id: `comment-quality-v1`
- required dimensions:
  - `persona_consistency`
  - `novelty`
  - `relevance`
  - `argument_quality`
  - `human_likeness`

Recovered default thresholds:
- `overall_min = 0.62`
- dimension mins:
  - `persona_consistency = 0.50`
  - `novelty = 0.50`
  - `relevance = 0.55`
  - `argument_quality = 0.55`
  - `human_likeness = 0.55`

Evaluation manifest contract:
- schema: `comment_section_quality_eval_manifest_v1`
- evaluation id: `CQ-<sha256-prefix>`
- reads snapshot schema `comment_section_evidence_snapshot_v1`
- output path: `outputs/comment_quality/<evaluation_id>/manifest.json`
- keys:
  - `schema_version`, `evaluation_id`, `as_of`
  - `snapshot_path`, `benchmark_path`
  - `row_count`, `dimensions`, `row_scores`, `aggregates`, `thresholds`
  - `pass`, `fail_reasons`

## 8. Site/UI and Static Build Contracts

Information architecture direction:
- UX SHOULD be Reddit-like at a high level: many spaces/communities, strong space identity, and feed-first browsing.
- spaces are the primary navigation unit, similar to subreddits.
- front page SHOULD prioritize recent activity (`new`) across spaces.

Navigation:
- sidebar uses site name and space name without noisy prefixes
- `Space Home` links to the canonical space home page
- stable hierarchy and collapsible state across page types
- current page highlighting
- `Topics` section contains topic pages only
- sidebar layer should sit visually above top search bar layer
- space switcher/list SHOULD be persistent and scannable, similar to a subreddit list

Tabs and pagination:
- tabs include `New`, `Sources`, `Topics`, `Users`
- `Claims` SHOULD remain accessible but de-emphasized (secondary panel/filter/detail view, not primary top-level emphasis)
- page size fixed at `50`
- site root lists spaces/sub-spaces
- sub-spaces can host tabs/content but no nested sub-space tree
- users tab scope:
  - site level: all repository-seeded users
  - space level: same repository-seeded catalog (optionally filtered/highlighted by activity in that scope)
  - persona profile page links in space views resolve to that space's `persona-<persona_id>` page
- subspace/tab rendering is driven by `TAB_PAGE_SIZE = 50` and validated `subspaces.json` entries

Source page specifics:
- source summary/context should be near top
- first-page image appears in a right-side top preview column and links to source PDF
- source detail page SHOULD include a long-form "Overview and Commentary" dossier so users can understand
  argument/evidence/limits without opening the PDF
- dossier rendering contract:
  - show short abstract near top (`summary_short`)
  - show substantial prose body (`summary_long`)
  - show clearly separated sectioned commentary cards (`5..8` sections) with grounded claim links
- related concept section includes only valid clickable targets
- claims should appear lower on the page or inside collapsible/detail sections rather than as the dominant top block

Topic page structure contract:
- topic pages MUST render in one of two structures: `wiki` (default) or `source_mirror`.
- renderer selection SHOULD be deterministic from topic metadata (for example source anchoring and source type) and MUST NOT invoke an LLM at render time.

`wiki` structure (default):
- intended for broad concept/subject coverage across multiple sources.
- recommended section order:
  1. Lead summary
  2. Key points
  3. Background and context
  4. Main concepts/subtopics
  5. Evidence and claims
  6. Related sources
  7. Open questions / disagreements
  8. References
- `Related sources` MUST list linked/adjacent sources with short rationale snippets (why related).

`source_mirror` structure (source-anchored, especially journal articles):
- intended when a topic page primarily reflects one source (or source family) and should mirror its high-level organization.
- section order SHOULD follow detected source structure (from `source_structure_outline` when available), projected at a higher level.
- for journal-article-like sources, preferred high-level mirrors include:
  - Abstract / problem framing
  - Background
  - Methods / approach
  - Results / findings
  - Discussion / interpretation
  - Limitations
  - Conclusion / implications
- each mirrored section SHOULD include:
  - concise synthesized prose
  - supporting claim links (`claim_id`)
  - mentions/links to related sources that corroborate, refine, or dispute the section content.
- source_mirror pages MUST remain higher-level than the source text (not a verbatim restatement), while preserving structural correspondence.

Search/feed presentation:
- single search control
- avoid unnecessary helper controls when removed by design choice
- searchable across configured indexed pages
- deterministic ordering and tie-breaks
- pagination URL semantics distinguish feed vs tab pagination
- public mode avoids internal IDs/paths/hashes leakage
- debug mode can show internal metadata
- front page `New` feed lists recent sources and topics across spaces, newest first
- each feed row SHOULD show space name, item type (`source` or `topic`), timestamp, title, and compact summary
- site-root `New` feed/index views MUST be refreshed after successful ingest/topic updates in any space of the same site (Section 2.2); incremental refresh is allowed when output is equivalent.

Cross-space topic linking contract:
- child-space pages can link to parent-space pages via pinned `imports.lock.md` entries
- unresolved pinned parent links render as disabled markers and produce lint `error`
- cross-space links preserve `space_name` and `topic_id` metadata
- each pinned parent entry includes `parent_space_name`, `parent_snapshot`, `parent_site_base_url`
- hierarchy/link resolution uses pinned snapshots only (no floating `latest`)

Claim reference rendering contract:
- factual markdown keeps `[[claims:...]]` annotations
- HTML view should avoid always-visible raw claim IDs in sentence text
- sentence-level claim bindings SHOULD behave as:
  - one linked claim: sentence links directly to claim page
  - multiple linked claims: sentence opens a selector card with claim page links
- selector options SHOULD use LLM-authored short claim titles from ingest extraction (`claims[].short_title`)
  - short titles SHOULD be semantic proposition labels authored by the LLM, not raw truncations
  - target: `3..7` words
  - compact style preference: `X is Y` / `X implies Y` / `X constrains Y`
  - avoid lead-ins (`the paper claims`, `the article argues`, `authors show`)
  - renderer MAY apply deterministic fallback shortening when canonical short title is missing
- sentence text without attached claim bindings MUST render as normal non-clickable prose
- opening a claim selector SHOULD close any previously open selector on the same page

Claim page content contract:
- claim pages SHOULD display a human-readable title (derived from claim text) and keep raw `claim_id` as secondary metadata.
- claim pages SHOULD include:
  - claim statement text
  - usage index (topic/source pages that reference the claim)
  - overview/interpretation prose
  - evidence item list with links to evidence detail pages
  - comments section (rendered discussion or explicit empty-state placeholder)
  - support stats panel
- support stats panel:
  - no canonical claim-strength formula is currently specified by this contract.
  - renderers MAY show deterministic UI heuristics for navigation/explainability, but MUST label them as non-canonical.
  - topic-page inclusion/reuse MUST NOT increase claim-strength score directly; topic usage may be displayed as context-only metadata.
  - heuristic stats MUST NOT be treated as canonical truth/confidence values in writeback flows.

Evidence page contract:
- deterministic build MUST render evidence pages from canonical evidence records at `<space_root>/evidence/evidence-*.json`.
- evidence items represent concrete support artifacts, not standalone claim paraphrases:
  - measurement/statistical observations
  - formal argument/proof/derivation fragments
  - equation/table/figure-level findings
- deterministic builders MUST NOT synthesize evidence IDs/titles from excerpts; evidence metadata is authored by semantic extraction.
- each evidence page SHOULD include:
  - short human-readable evidence title
  - full evidence excerpt text
  - linked claim page(s)
  - linked source page when `source_id` is available
  - linked topic pages that reference the parent claim
- source/topic/claim pages SHOULD link to evidence pages whenever linked claim evidence exists.

Comment quality-signal rendering contract:
- per-comment `score` MUST come from neutral semantic `score_assessment` output generated by `comment_section_generation`.
- scoring context MUST include the target page thread chain plus original source context for the page.
- deterministic merge/render stages MUST consume semantic `score_assessment` and MUST NOT recompute score from hash/ID heuristics.
- public UI MUST render non-interactive quality badges (no voting controls):
  - `Insightful` when score `> 15`
  - `Average` when score is `0..14`
  - `Bad` when score `< 0`
- renderer SHOULD show numeric points alongside the badge for transparency.

Static build requirements:
- `scripts/build_site.py` renders HTML directly from canonical JSON artifacts plus deterministic templates
- generated HTML uses Tailwind CSS as the primary styling system
- Tailwind build/purge pipeline MUST run as part of site build so emitted CSS is deterministic
- unresolved conversion/template/link errors should hard-fail build
- static build stage MUST NOT invoke LLMs

Canonical presentation contract (normative):
- every rendered HTML document MUST include canonical responsive viewport metadata:
  - `<meta name="viewport" content="width=device-width, initial-scale=1">`
- every rendered HTML document MUST include exactly one canonical stylesheet link emitted by deterministic templates:
  - `<link rel="stylesheet" href=".../assets/site.css">`
- renderer output MUST include stable semantic layout class hooks so modern styling stays deterministic across page types:
  - `site-shell`, `site-sidebar`, `site-main`, `content-card`, `feed-list`, `topic-section`, `source-summary`
- ownership boundary:
  - canonical JSON + deterministic templates own HTML structure and semantic class naming
  - deterministic CSS toolchain stage owns stylesheet compilation
  - static site build/runtime MUST NOT synthesize CSS via LLM or non-deterministic runtime mutation
- determinism boundary:
  - emitted stylesheet bytes MUST be a deterministic function of checked-in style sources and lockfile-pinned toolchain inputs
  - build success MUST require emitted stylesheet asset presence plus HTML link references; metadata alone is insufficient
- ambiguity guardrail:
  - `toolchain_versions.tailwind_cli` is declaration-only metadata and MUST NOT be treated as proof that stylesheet compilation occurred

Frontend toolchain reproducibility contract:
- repository MUST check in `package.json` plus exactly one lockfile (`package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`)
- selected package manager MUST be declared via `packageManager` in `package.json`
- repository MUST pin Node runtime version via `.nvmrc` or `.node-version`; site build wrappers/CI MUST enforce this version
- dependency installation in CI/build wrappers MUST use lockfile-frozen mode (`npm ci`, `pnpm install --frozen-lockfile`, or `yarn install --immutable`)
- site build MUST fail fast when lockfile is missing, out-of-sync with `package.json`, or generated by a different package-manager family
- run metadata `toolchain_versions` SHOULD include at least `node`, package-manager name/version, and Tailwind CLI version

Historical source preview assets:
- canonical preview path is `site/assets/source_previews/<source_id>.<ext>`
- when `sources/records/<source_id>.json` includes `artifacts.front_page_image` pointing to a valid
  space-local image (`.png`, `.jpg`, `.jpeg`, `.webp`), site build MUST copy and use that image for
  source detail and source preview rows in both space/site `New` feeds
- when no valid `artifacts.front_page_image` exists, site build MUST emit deterministic SVG fallback
  at `site/assets/source_previews/<source_id>.svg`

## 9. Observability, Runtime Controls, and Safety

Verbose mode contract:
- print final prompt before LLM launch
- stream both stdout and stderr live
- print trace dir early
- persist traces under:
  - `<site_path>/outputs/llm_traces/<timestamp>-<flow>-<pid>-<attempt>`
- trace artifacts:
  - `*.prompt.txt`, `*.context.json`, `*.response.*`, `*.codex.stdout.jsonl`, `*.codex.stderr.txt`, `*.meta.json`

High-signal CLI runtime flags:
- LLM/runtime: `--llm-backend`, `--llm-model`, `--llm-reasoning-effort`, `--llm-timeout-secs`
- tracing: `--verbose`, `--llm-trace`, `--llm-trace-dir`, `--trace-llm-io`
- toggles/testing: `--mock-llm`, `--enable-source-index`, `--run-search-visibility`, `--site-presentation-mode`, `--warning-budget`, `--require-source-date`
- `--warning-budget` overrides the default lint warning threshold (`200`) for workflows that apply warning-threshold status mapping (Section 5.8); value MUST parse as a positive integer.
- `--mock-llm` is test-only and MUST NOT be enabled by default in production/operator wrapper workflows.
- legacy test/debug gates MUST be exposed as explicit CLI flags (if kept) and MUST NOT trigger deterministic fallback semantics in production/operator mode.
- tests/local contract checks that need non-live execution MUST use `--mock-llm` while preserving schema/output contracts.
- advanced comment controls (if implemented) SHOULD be explicit CLI flags.
- live semantic defaults SHOULD be `--llm-backend codex`, `--llm-model gpt-5.4`, and `--llm-reasoning-effort high`.
- live semantic timeout SHOULD default to disabled (`--llm-timeout-secs none`) so operator runs wait until the
  live child finishes or fails explicitly.
- backend/model defaults are deployment/runtime policy and SHOULD be changed via CLI/wrapper config rather than by editing non-negotiable semantic contracts.
- flow behavior MUST be determined from command-line arguments only; environment variables MUST NOT change semantic/pipeline behavior.

Safety rules:
- cleanup code must guard against dangerous roots (`.`, repo root, home, mount root, empty)
- do not delete outside explicit temp/staging roots
- persisted artifacts should avoid absolute machine paths unless explicitly internal-only

Registry/testing isolation:
- all non-bootstrap registry-backed commands MUST require explicit `--registry-path`
- tests SHOULD use isolated registry files

## 10. Run Status and Output Envelopes

Topic lifecycle model (high-signal recovered contract):
- states: `draft`, `stable`, `final`
- transitions:
  - automatic `draft -> stable` after healthy projections
  - automatic `stable -> draft` on major conflict/structural churn
  - manual-only `stable -> final` and `final -> stable`
  - `final` pages are not auto-demoted
- final pages with unresolved disputed contradictions remain in `final` state but are blocked by lint gates until manually remediated
- audit fields: `finalized_by`, `finalized_at`

Ingest CLI output (high-signal):
- `run_id=run-<utc_timestamp>--<suffix>`
- `source_id=source-<slug>--<suffix>`
- `claims_changed=<int>`
- `relations_changed=<int>`

Projection output (high-signal):
- page change/render/write counts
- `llm_projection` summary
- `comments`, `persona_profiles`, `profile_images_loaded`, `short_names` summaries

Lint-gate failure envelope:
- `status: failed`
- `reason: lint_gate`
- `lint` count map (`error_count`, `warning_count`, `info_count`)
- projection change summary
- `projection_index.changed`
- envelope may be emitted as command output even when failed invocation artifacts are rolled back per Section 2.1.
- for ingest `--force` failures, the same envelope applies but invocation artifacts MAY remain for forensic inspection.

Historical status vocabulary:
- `pending`
- `success`
- `success_with_warnings`
- `failed`
- `aborted`

Canonical run-record metadata (normative base envelope for committed runs):
- run-record markdown path: `<space_root>/runs/<run_id>/run.md`
- base frontmatter fields (all command runs):
  - `run_id`, `flow_key`, `semantic_flows`, `semantic_flow_invocation_counts`, `status`, `started_at`, nullable `completed_at`
  - `model_fingerprint`, `provider_fingerprint`, `reasoning_effort`, `execution_mode`, `llm_attempt_count`
  - `toolchain_versions` (string->string map)
  - lint totals (`lint_error_count`, `lint_warning_count`, `lint_info_count`)
- run-record `flow_key` namespace is command/pipeline oriented and distinct from generation-spec semantic `flow_key` values.
- `flow_key` allowed values: `ingest_pipeline`, `query_pipeline`, `comment_section_pipeline`, `persona_profile_pipeline`
- `semantic_flows` values MUST be an ordered unique subset of canonical semantic flow keys from: `ingest_extraction`, `topic_generation`, `query_synthesis`, `comment_section_generation`, `persona_profile_generation`
- `semantic_flow_invocation_counts` keys MUST be canonical semantic flow keys and values MUST be positive integers; every key in `semantic_flows` MUST appear in this map.
- flow-specific frontmatter extensions:
  - ingest pipeline: `ingest_scope`, `source_ids`, nullable `parent_run_id`, changed sets (`claims_changed`, `relations_changed`, `topic_pages_changed`), optional deferred-build flags (`build_deferred`, `deferred_build_reason`), optional force-mode flags (`force_mode`, `rollback_skipped`)
  - query pipeline: `query_id`, `mode`, `scope`, `claims_used`, `sources_used`, `contradictions_considered`, nullable `manifest_path`
  - comment-section pipeline: `target_page_refs`, `comment_user_filters`, `requested_count`, `comments_added`, `evidence_mode`, nullable `evidence_snapshot_path`
  - persona-profile pipeline: `persona_ids`, `history_generated`, `history_updated`, `history_reused`, `pages_changed`
- flows that do not execute lint/build stages MUST still write lint totals with a consistent null-or-zero policy chosen by implementation and enforced in tests
- required body sections: `## Summary`, `## Changes`, `## Lint Summary`, `## Errors`

Run-truth semantics:
- only `success` and `success_with_warnings` runs advance verification/reconciliation state
- `failed` and `aborted` runs do not count toward consecutive-run resolution logic

## 11. Testing Strategy for Recreation

Must-have tests:
- ingest schema/date behavior
- path relocatability
- navigation/tabs/accessibility
- comment generation and rendering contracts
- seeded persona catalog integrity/load behavior
- profile page + profile history behavior
- projection/query contract schemas
- user-facing evaluation harness artifact-pack behavior (`evaluate_source.sh`) with markdown-first outputs
- mechanical harness contract tests validating artifact-pack shape, manifest linkage, and comments-mode argument handling

Recovered footprint to preserve:
- broad `tests/test_*.py` suite
- golden site snapshots under `tests/golden/site_snapshot/...`
- skill prompt snapshots under `tests/golden/skills/*.skill`

High-value test files (historical):
- `test_site_relocatability.py`
- `test_site_navigation.py`, `test_site_tabs_accessibility.py`
- `test_ingest_source_date_extraction.py`, `test_skill_output_contract_failures.py`
- `test_persona_comments_cli.py`, `test_social_users.py`, `test_persona_profile_pages.py`

## 12. Reconstruction Plan (Code-Recreation Order)

### 12.1 Recommended MVP delivery cuts (execute before full subsystem parity)

This is an execution strategy layered on top of the Phase 1-6 reconstruction plan.  
Goal: ship a narrow but real end-to-end loop first, then widen to social/evaluation features.

MVP Slice A (core vertical slice):
1. bootstrap + registry: `create_site.sh`, `create_space.sh`, strict `--registry-path` handling for non-bootstrap commands.
2. ingest semantic flow: strict generation-spec + schema validation, canonical source/claim/relation persistence, run-record write.
3. deterministic projection + build: render source/topic pages and space/site `New` views from canonical JSON only.
4. query semantic flow: strict JSON output + deterministic markdown rendering (artifact formats beyond markdown may be deferred).
5. baseline validation: lint gate for ingest/build, query lint summary emission, fail-fast on schema/contract violations.

MVP Slice A exit criteria:
- one-source happy path works end-to-end: create site/space -> ingest -> build -> query -> validate.
- all semantic outputs are LLM-generated (or `--mock-llm` in tests) and schema-valid.
- run metadata envelope is present for ingest + query flows.
- no deferred-build backlog for runs created during Slice A verification.

MVP Slice B (core hardening before social):
1. backfill deferred/edge behaviors in ingest/build/query (locking, date policy, truncation/tie-break determinism, manifest rules).
2. complete run-envelope coverage for all implemented core flows and lock contract tests/golden snapshots.
3. stabilize static build reproducibility (frontend toolchain pinning + deterministic CSS pipeline in CI/wrappers).
4. enforce site-root multi-space refresh semantics and incremental/full rebuild equivalence checks.
5. expand validation and regression tests for relocatability, navigation/tabs, and contract drift.

MVP Slice B exit criteria:
- core non-social workflows are reliable under repeated runs and deterministic rebuilds.
- contract tests for ingest/build/query pass with strong signal.
- operators can use wrappers without manual artifact repair or registry/path workarounds.

Defer until after MVP Slice B:
- comment section generation and moderation/adjudication.
- persona profile pages/history updates.
- comment quality benchmark/evaluation harness.
- advanced query artifact formats (`mermaid/images/slides/pdf`) if not already implemented.

### Phase 1: Skeleton and contracts
1. recreate repo structure, package skeleton, shell wrappers
2. recreate skill loader/runner and strict schema validation
3. recreate registry and site/space bootstrap

### Phase 2: Ingest and core records
1. implement ingest flow with strict LLM contract
2. persist source/claim/relation/run records
3. add source date/title resolution and locking
4. add reference extraction + local link backfill
5. allow reconstruction bootstrap ingest mode with deferred build metadata until Phase 3 is implemented

### Phase 3: Projection and static site
1. implement deterministic projection/site build modules
2. process all Phase-2 deferred ingest runs and clear deferred-build backlog
3. topic JSON projection and page writing
4. projection index/cache
5. static site rendering + sidebar/tabs/search
6. enforce JSON->HTML deterministic build hard-fail behavior

### Phase 4: Query and core evaluation
1. query pipeline with strict output schema
2. integrate query run-output envelopes and lint-summary behavior
3. implement deterministic query artifact modes (`mermaid/images/slides/pdf`) as needed

### Phase 5: Social subsystem
1. load and validate repository-seeded persona catalog + profile images
2. threaded comment generation with controls/evidence modes
3. comment section merge normalization + moderator/outcome blocks
4. generation isolation and adjudication summaries
5. persona profile-page projection with seeded profile image links and space-local profile-history refresh
6. comment quality benchmark + evaluation manifest pipeline

### Phase 6: hardening
1. verbose trace artifacts and replayability
2. command-line runtime controls and safety guards
3. test suite expansion + golden snapshots

## 13. Definition of Done

- `create_site.sh`, `create_space.sh`, `ingest.sh`, `query.sh`, `create_comments.sh`, `generate_profiles.sh`, `regenerate_web.sh`, `validate.sh`, `evaluate_source.sh` run successfully.
- `validate.sh` enforces workflow-specific lint gate behavior.
- `evaluate_source.sh` produces a human-readable artifact folder (`README.md`, `summary.md`, query markdown outputs, lint summary, optional comments review) suitable for manual quality review.
- ingest produces source/claim/topic artifacts with valid links.
- publication `date` and ingest `ingested_at` semantics are correct, including nullable `date` fallback when strict-date mode is disabled.
- front-page ordering uses `ingested_at`.
- static site navigation/tabs/search behavior is stable and consistent across page types.
- repository-seeded users (count `100`) with full metadata and profile photos are loaded correctly across all sites/spaces, and threaded comments/persona profile pages/profile-history artifacts are generated correctly.
- production/operator semantic generation paths remain LLM-driven with strict contract validation/retry/fail semantics; test-only mock mode MAY be used for isolated testing while preserving the same output contracts.
- any ingest runs marked `build_deferred: true` have been backfilled; no deferred-build backlog remains.
- tests provide strong signal on contract drift and rendering regressions.
