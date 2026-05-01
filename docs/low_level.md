# Sapi Low-Level Design

Status: draft for reconstruction.

This document is the implementation bridge between [design.md](./design.md) and code.
It is intentionally lower-level than `design.md`, but still above final code.

If this file and `design.md` disagree, `design.md` wins, except where `design.md` explicitly delegates authority to this file (module/package topology in Section 3).

## 1. Purpose

Use this document to prevent implementation drift and incoherence while rebuilding:

- module boundaries and ownership
- class/function naming contracts
- per-command control flow
- semantic-flow orchestration contracts
- rollback, persistence, and failure semantics
- testing and code-review gates

Non-goal:
- full code-level detail for every helper function

## 2. Runtime Model

Sapi has two distinct flow namespaces.

1. Semantic flow keys (generation-spec scope):
- `ingest_extraction`
- `topic_generation`
- `source_revision_detection`
- `query_synthesis`
- `comment_section_generation`
- `persona_profile_generation`
- `space_overview_generation`
- `question_relevance_mapping`
- `question_synthesis`
- `question_measurement_extraction`

2. Pipeline flow keys (run-record scope):
- `ingest_pipeline`
- `query_pipeline`
- `comment_section_pipeline`
- `persona_profile_pipeline`
- `overview_pipeline`

Key rules:
- one command invocation writes one `run_id` record
- each run record may reference multiple semantic flows via ordered-unique `semantic_flows[]`
- each run record must also include `semantic_flow_invocation_counts` for per-flow invocation cardinality
- semantic/pipeline behavior is configured by command-line arguments only (no env-var flow controls)
- all committed runs emit the full base run envelope (Section 4)

Examples:
- normal ingest run:
  - `flow_key = ingest_pipeline`
  - `semantic_flows = [ingest_extraction, topic_generation]`
  - `semantic_flow_invocation_counts = {ingest_extraction: 1, topic_generation: 1}`
- ingest run with automatic revision detection:
  - `flow_key = ingest_pipeline`
  - `semantic_flows = [source_revision_detection, ingest_extraction, topic_generation]`
  - `semantic_flow_invocation_counts = {source_revision_detection: 1, ingest_extraction: 1, topic_generation: 1}`
- ingest run with explicit `--revises-source-id`:
  - skips `source_revision_detection`
  - links revision-family metadata transactionally from operator input
- ingest bypass flags are removed:
  - `--source-only` and `--query-only` must fail fast with usage error

## 3. Target Package Layout

Canonical reconstruction code layout under `sapi/` and `scripts/`:
- this topology is the authoritative reconstruction target; recovered module lists in `design.md` Section 4.2/4.3 are historical reference only.

```text
sapi/
  contracts/
    ids.py
    paths.py
    run_envelopes.py
    schemas.py
    semantic_specs.py
  core/
    registry.py
    site_scope.py
    fs_store.py
    transactions.py
    locks.py
  llm/
    client.py
    trace.py
    semantic_executor.py
  ingest/
    ingest_pipeline.py
    source_content.py
    records_writer.py
    relation_store.py
    citations.py
    topic_generator.py
  query/
    query_pipeline.py
    retrieval.py
    renderers.py
  comments/
    comments_pipeline.py
    merge_normalize.py
    controls.py
  profiles/
    profiles_pipeline.py
    history.py
  questions/
    prepared_questions.py
  overview/
    overview_pipeline.py
  build/
    projection.py
    site_builder.py
    projection_index.py
  lint/
    lint_engine.py
    severity.py

scripts/
  ingest_source.py
  query.py
  create_comments.py
  generate_profiles.py
  generate_overview.py
  build_site.py
  create_prepared_questions.py
  lint.py
```

Topology ownership note (resolved stubs):
- `sapi/core/fs_store.py` is the shared JSON filesystem helper used by projection/build readers for
  canonical object loading and deterministic path listing.
- `sapi/build/projection_index.py` owns deterministic projection-index emission at
  `<space_root>/outputs/projection_index/index.json` and is wired from `scripts/build_site.py`.
- `sapi/build/site_builder.py` remains orchestration-heavy but delegates topic sentence-level
  claim annotation parsing/rendering and claim-option title synthesis to
  `sapi/build/topic_claim_rendering.py`.
- `sapi/questions/prepared_questions.py` owns prepared-question record parsing, validation, ordering,
  link resolution, lifecycle filtering, and operator-authored seed writes. It rejects non-schema
  records, filename/question ID mismatches, duplicate display orders, wrong space/subspace scopes, and
  broken source/claim/evidence references before callers receive prepared-question records. Ingest
  relevance mapping, cumulative synthesis, and measurement extraction should extend this package
  rather than adding question persistence inside build or ingest modules directly.
- `scripts/create_prepared_questions.py` owns the non-semantic operator/bootstrap entrypoint for
  prepared-question authoring from approved TSV seed data. It must go through registry resolution and
  the shared question writer rather than writing ad hoc JSON.

## 4. Core Data Types

Use typed models (dataclass or Pydantic). Keep fields aligned with schemas and run frontmatter.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

SemanticFlowKey = Literal[
    "ingest_extraction",
    "topic_generation",
    "source_revision_detection",
    "query_synthesis",
    "comment_section_generation",
    "persona_profile_generation",
    "space_overview_generation",
    "question_relevance_mapping",
    "question_synthesis",
    "question_measurement_extraction",
]

PipelineFlowKey = Literal[
    "ingest_pipeline",
    "query_pipeline",
    "comment_section_pipeline",
    "persona_profile_pipeline",
    "overview_pipeline",
]

RunStatus = Literal["pending", "success", "success_with_warnings", "failed", "aborted"]

@dataclass(frozen=True)
class SemanticSpec:
    flow_key: SemanticFlowKey
    version: str
    schema_path: Path
    output_json_path: Path
    context_paths: list[Path]

@dataclass
class RunEnvelopeBase:
    run_id: str
    flow_key: PipelineFlowKey
    semantic_flows: list[SemanticFlowKey]
    semantic_flow_invocation_counts: dict[SemanticFlowKey, int]
    status: RunStatus
    started_at: str
    completed_at: str | None
    model_fingerprint: str
    provider_fingerprint: str
    reasoning_effort: str
    execution_mode: str
    llm_attempt_count: int
    lint_error_count: int
    lint_warning_count: int
    lint_info_count: int
    toolchain_versions: dict[str, str]

@dataclass
class IngestRunFields:
    ingest_scope: str
    source_ids: list[str]
    parent_run_id: str | None
    claims_changed: int
    relations_changed: int
    topic_pages_changed: int
    build_deferred: bool
    deferred_build_reason: str | None
    force_mode: bool
    rollback_skipped: bool

@dataclass
class QueryRunFields:
    query_id: str
    mode: str
    scope: str
    claims_used: int
    sources_used: int
    contradictions_considered: int
    manifest_path: str | None

@dataclass
class CommentRunFields:
    target_page_refs: list[str]
    comment_user_filters: list[str]
    requested_count: int
    comments_added: int
    evidence_mode: str
    evidence_snapshot_path: str | None

@dataclass
class PersonaProfileRunFields:
    persona_ids: list[str]
    history_generated: int
    history_updated: int
    history_reused: int
    pages_changed: int

@dataclass
class OverviewRunFields:
    overview_id: str
    scope_kind: str
    scope_name: str
    source_records_used: int
    claims_used: int
    relations_used: int
    topics_used: int
    article_path: str | None

@dataclass
class PreparedQuestionRecord:
    question_id: str
    question: str
    status: Literal["active", "inactive", "draft"]
    scope_space_name: str
    display_order: int
    linked_source_ids: list[str]
    claim_ids: list[str]
    evidence_ids: list[str]
    measurement_ids: list[str]
    synthesis: dict[str, Any]
    freshness: dict[str, Any]
    warnings: list[str]
```

Run envelope policy:
- each pipeline writes `RunEnvelopeBase` plus its pipeline-specific extension fields
- `semantic_flows` is an ordered unique list of semantic flows executed at least once in the invocation
- `semantic_flow_invocation_counts` records how many semantic invocations were executed per semantic flow key
- timestamp fields (`started_at`, `completed_at`) use UTC RFC 3339 with trailing `Z`
- `llm_attempt_count` is the total attempts consumed across semantic calls in the invocation
- flows that do not execute lint/build still write lint totals with one implementation-wide null-or-zero policy

## 5. Path and Registry Contracts

Single source of truth:
- wrappers pass `--registry-path <site_path>/spaces.toml`
- scripts resolve `<space_name>` using that registry only

Required helper APIs:

```python
def resolve_registry_path(arg_registry_path: str | None) -> Path: ...
def load_registry(registry_path: Path) -> dict[str, Any]: ...
def resolve_space_root(registry_path: Path, space_name: str) -> Path: ...
def resolve_site_path_from_registry(registry_path: Path) -> Path: ...
```

Rules:
- no default `~/.sapi/spaces.toml` fallback for normal commands
- relative `space_root` in registry resolves relative to registry directory
- normalize to absolute paths before I/O

## 6. Semantic Execution Engine

Implement one shared executor for all semantic flows.

```python
def run_semantic_flow(
    *,
    spec: SemanticSpec,
    llm_client: "LlmClient",
    max_repair_loops: int = 3,
    trace_ctx: "TraceContext",
) -> tuple[dict[str, Any], int]:
    """
    Returns (validated_semantic_json, attempt_count).
    Semantic JSON is already written to spec.output_json_path.
    Raises SemanticFlowError on terminal failure.
    """
```

### 6.1 Spec resolution and version pinning

- semantic specs are resolved through the explicit flow map defined in `design.md` Section 4.1.3
- no implicit spec filename discovery is allowed
- `<flow_key>.v1.md` MUST pair with `<flow_key>.v1.schema.json`
- semantic inputs MUST use canonical flow keys; unknown flow keys, including `persona_comment_generation`, MUST fail fast before resolution

### 6.2 Retry/repair policy

- default `max_repair_loops = 3`
- `max_attempts = 1 + max_repair_loops` (default `4` total attempts)
- each repair attempt includes previous invalid JSON, machine-readable validation errors, and the target schema
- each repair attempt requests a complete replacement JSON object
- deterministic auto-fixes of invalid semantic JSON are prohibited outside the LLM repair loop

Execution algorithm:
1. resolve canonical spec and schema for flow key
2. gather filesystem context from `context_paths`
3. perform initial LLM generation attempt
4. validate schema
5. on failure, execute up to `max_repair_loops` repair attempts
6. on validation success, atomically write validated JSON to `output_json_path`
7. return `(parsed_json, attempt_count)`

Hard constraints:
- never persist invalid attempts as committed artifacts
- failure to validate after max attempts raises terminal error for pipeline rollback handling

## 7. Transaction and Rollback Design

Each command invocation uses one transaction scope keyed by `run_id`.

Required behavior:
- track invocation-scoped writes in a transaction journal
- default mode: terminal failure rolls back invocation-scoped writes
- ingest `--force` mode: terminal failure MAY skip rollback and preserve invocation artifacts
- terminal failures must not leave committed `runs/<run_id>/` containers, except ingest failures with `force_mode=true`

Suggested primitives:

```python
class ArtifactTransaction:
    def mark_create(self, path: Path) -> None: ...
    def mark_replace(self, path: Path, backup_path: Path) -> None: ...
    def mark_delete(self, path: Path, backup_path: Path) -> None: ...
    def mark_mkdir(self, path: Path) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

Rollback algorithm contract:
1. keep run/lint writes in invocation-local staging until commit is allowed
2. restore replaced/deleted files from backups
3. delete invocation-created files and directories in reverse dependency order
4. default mode: ensure `<space_root>/runs/<run_id>/` does not remain after terminal failure
5. release locks in `finally` blocks regardless of success/failure

Force override note:
- for ingest `--force`, the pipeline may bypass rollback and commit failure-state run artifacts for forensic inspection.

Implementation notes:
- atomic file writes via temp file + `os.replace`
- backups only for paths replaced/deleted in this invocation

## 8. Pipeline Execution Contracts

### 8.0 Prepared-question ownership

Prepared-question implementation ownership:
- `sapi/questions/prepared_questions.py` owns canonical record validation, lifecycle filtering,
  display ordering, writer/upsert semantics, linked source/claim/evidence validation, and seed import.
- ingest-time source-to-question relevance mapping belongs in the ingest pipeline only as an
  orchestrator; prompt preparation, output validation, and question-record mutation should delegate
  to `sapi/questions/`. `sapi/questions/relevance_mapping.py` owns the semantic invocation wrapper,
  active-question filtering, source/claim/evidence grounding checks, and transactional question-record
  mutation for `question_relevance_mapping`.
- cumulative question synthesis belongs in `sapi/questions/` and is invoked after relevance mapping or
  explicit refresh. It must consume canonical linked source/claim/evidence context and persist only
  schema-valid semantic output.
- measurement extraction and compatibility grouping belong in `sapi/questions/`; site rendering may
  draw tables/charts from validated measurement records but must not infer missing numeric values.
- deterministic question index/detail rendering belongs in `sapi/build/site_builder.py` and should read
  prepared-question records through the shared loader.
- wrapper ownership is split: `create_questions.sh` and `scripts/create_prepared_questions.py` handle
  operator-approved authoring/seed import; they accept four-field active rows or five-field
  status-aware rows, enforce per-space duplicate IDs/orders, apply reorder/update/deactivation
  changes through the shared writer, and reject empty filtered imports. Later refresh wrappers should
  call question package pipeline helpers rather than writing records directly.

### 8.1 Common pipeline state machine and exit codes

Status transitions:
- initialize run as `pending`
- on terminal errors (schema exhaustion, invalid config, deterministic post-processing failure): `failed`
- on operator/system interrupts: `aborted`
- on success with `error_count == 0` and warnings within threshold: `success`
- on success with `error_count == 0` and warnings over threshold: `success_with_warnings`

Exit-code policy:
- return `0` for `success` and `success_with_warnings`
- return non-zero for `failed` and `aborted`

Commit/rollback policy:
- default mode: committed run/lint artifacts are written only for successful statuses
- default mode: terminal failures rollback invocation artifacts and may emit failure envelopes on stdout/stderr
- ingest `--force` exception: failed ingest runs MAY keep invocation artifacts and committed failure-state run/lint artifacts for audit/forensics

### 8.1 Ingest Pipeline (`scripts/ingest_source.py`)

Function boundary:

```python
def run_ingest_pipeline(args: IngestArgs) -> int: ...
```

Required preflight:
- resolve registry/site/space paths
- parse `--force` as explicit rollback override (ingest-only)
- acquire ingest lock

Control flow:
1. initialize `RunEnvelopeBase(flow_key="ingest_pipeline")`
2. fetch and store source artifact/record
   - if source is inferred/declared as PDF (`application/pdf` or `.pdf` locator), validate payload signature (`%PDF-`) before writing artifacts
   - write canonical sibling artifacts `source.md` and `source_extraction.json`
   - PDF markdown extraction MUST use MarkItDown and record `extraction_failed` when MarkItDown is
     unavailable or cannot produce usable markdown
   - persist source-record `analysis_policy` with `preferred_artifact=source_markdown`,
     explicit fallback list, quality status, and warnings
3. resolve source revision/version handling
   - `--revises-source-id` validates a same-space source target, writes `source_revision`
     metadata and a manifest under `sources/versions/`, and skips model detection
   - `--revises-source-id` and `--source-family-id` are mutually exclusive and fail fast when combined
   - without an explicit target, deterministic code may shortlist same-space candidates only to bound prompt size
   - if candidates exist in live mode, run semantic flow `source_revision_detection`
   - revision detection prompt context defaults to `source.md` and `source_extraction.json`, with original
     binary/PDF inspection reserved for degraded or insufficient markdown
   - only `decision=revision`, `certainty=true`, and a candidate `matched_source_id` links records
   - uncertain/negative/non-candidate decisions leave the new source independent
4. run semantic flow `ingest_extraction`
   - default source-reading input is `<space_root>/sources/artifacts/<source_id>/source.md`
   - inspect `source_extraction.json` before falling back to the original binary for fidelity-sensitive content
5. deterministically write canonical source/claim/relation artifacts
6. persist canonical evidence records from semantic `evidence_items[]` under `<space_root>/evidence/`
7. deterministic ingest validation MUST resolve `evidence_items[].claim_refs` to canonical claim IDs and fail fast on invalid refs
8. deterministic ingest code MUST NOT derive evidence IDs/titles/excerpts from claim text
9. when active prepared questions exist, run semantic flow `question_relevance_mapping`, validate that
   every matched question is active and every claim/evidence ID belongs to the newly ingested source,
   then transactionally append source/claim/evidence links to matched question records
10. when no active prepared questions exist, skip `question_relevance_mapping` and set
   `question_mapping_status = no_active_questions` with `question_matches_changed = 0`
11. run semantic flow `topic_generation`
12. deterministically write 0..n canonical topic artifacts from shared cross-source concepts
13. set `semantic_flows = [ingest_extraction, topic_generation]`, `[ingest_extraction, question_relevance_mapping, topic_generation]`, or `[source_revision_detection, ingest_extraction, question_relevance_mapping, topic_generation]` only when those optional flows actually run
14. set `semantic_flow_invocation_counts` to match exactly the flows invoked in this ingest run
15. run link reconciliation
    - reference extraction prefers `source.md` when `analysis_policy.quality_status != unusable`
    - same step MAY persist curated `external_related_links[]` plus `related_link_enrichment`
      summary metadata on source records
16. run deterministic projection/build and site-root `New` index refresh (or bootstrap deferred mode)
17. run lint and warning-threshold evaluation
18. write `run.md` and `lint.json` for committed run
19. release lock

Bootstrap deferred-build behavior:
- when projection/build modules are intentionally unavailable during reconstruction bootstrap, ingest MAY mark:
  - `build_deferred = true`
  - `deferred_build_reason` set
  - `status = success_with_warnings`
- deferred runs must be backfilled before definition-of-done verification

Ingest force-mode behavior:
- explicit flag: `--force`
- terminal failures MAY skip rollback and preserve already-written invocation artifacts
- when rollback is skipped, ingest run metadata MUST set `force_mode=true` and `rollback_skipped=true`
- `--force` does not relax semantic schema validation, retry budgets, or semantic-flow constraints

### 8.2 Query Pipeline (`scripts/query.py`)

Function boundary:

```python
def run_query_pipeline(args: QueryArgs) -> int: ...
```

Required preflight:
- resolve registry/site/space
- enforce mode compatibility: `--mode strict --include-disputed` is invalid and must fail fast
- apply include-disputed defaults by mode when flag omitted
- apply include-warnings default (`true`) when not explicitly set

Control flow:
1. initialize `RunEnvelopeBase(flow_key="query_pipeline")`
2. retrieve context deterministically from canonical artifacts
3. run semantic flow `query_synthesis` (writes canonical query JSON)
4. if output format in `{mermaid,images,slides,pdf}`:
   - deterministically write query manifest
   - set `manifest_path`
5. if output format is `markdown`:
   - do not write manifest
   - enforce `manifest_path` null/omitted in query JSON
6. write run/lint metadata for every committed invocation

Query constraints:
- query pipeline MUST NOT mutate canonical knowledge artifacts (`sources/`, `claims/`, `relations/`, `topics/`, `profiles/`)
- query pipeline MUST NOT trigger space/site rebuilds or site-root `New` refresh

### 8.3 Comment Pipeline (`scripts/create_comments.py`)

Function boundary:

```python
def run_comment_section_pipeline(args: CommentsArgs) -> int: ...
```

Required preflight:
- resolve paths and controls
- reject removed non-canonical comment flags (`--user`, `--page`, positional count `<n>`, `--comment-web-evidence`) with usage error
- accept only canonical discussion-controls schema/key names; ignore removed schema id `persona_discussion_controls_v1` and removed `persona_discussion_*` keys
- reject legacy HTML comment turn markers `<!-- turn:{...} -->`; only canonical `<<turn:{...}>>` markers are accepted
- accept only canonical rebuttal field `strongest_opposing_point_ack`; reject removed alias `steelman_before_rebuttal`
- reject legacy ordinal parent refs `pc-###`; accept only canonical `parent_comment_uid` values and in-batch `draft-N` refs
- validate `--count` in `[5, 50]`

Control flow:
1. initialize `RunEnvelopeBase(flow_key="comment_section_pipeline")`
2. select targets:
   - default target set is parseable topic pages only
   - source/claim pages require explicit `--comment-page`
3. run semantic flow `comment_section_generation` per target page (single call per page by default)
   - set `semantic_flows = [comment_section_generation]` when at least one target page is processed
   - set `semantic_flow_invocation_counts = {comment_section_generation: <target_page_count>}`
   - write one semantic artifact per invocation at `runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json`
   - enforce one semantic attempt per target page (`max_repair_loops=0`)
   - require per-comment `score_assessment` (neutral `score` + `rationale`) from the semantic output
   - provide target thread-chain and original-source context to semantic generation for scoring
4. merge and normalize comments deterministically
   - consume semantic `score_assessment` values; do not compute hash/ID-derived scores in deterministic merge
5. preserve existing `comment_uid`, assign only for new rows
6. rebuild affected pages/space feed indices per contract
7. in `web-augmented` evidence mode, persist snapshot at `raw/snapshots/comment_sections/comment-section-<seed>.json` using schema `comment_section_evidence_snapshot_v1`
8. run lint and warning-threshold evaluation
9. write `run.md` and `lint.json` on success

Comment constraints:
- comment pipeline does not refresh site-root `New` index unless it also mutates canonical source/topic artifacts
- generation-isolation metadata should use canonical marker `comment_section_generation_context_v1`

### 8.4 Persona Profile Pipeline (`scripts/generate_profiles.py`)

Function boundary:

```python
def run_persona_profile_pipeline(args: ProfilesArgs) -> int: ...
```

Control flow:
1. resolve paths and persona roster
2. initialize `RunEnvelopeBase(flow_key="persona_profile_pipeline")`
3. run semantic flow `persona_profile_generation` for selected personas
4. write canonical `profiles/persona-<persona_id>.json`
5. update deterministic history under `outputs/persona_profile_history/`
6. run deterministic profile projection/build updates
7. run lint and warning-threshold evaluation
8. write `run.md` and `lint.json` on success

Profile constraints:
- semantic profile payloads may include `short_cv_entries[]` with role, organization, period, and
  model-authored description; site rendering prefers those entries over catalog-only CV rows.
- persona-profile pipeline does not refresh site-root `New` index unless it mutates canonical source/topic artifacts

### 8.5 Overview Synthesis Contract (`scripts/generate_overview.py`)

Ownership boundary:
- overview orchestration belongs in `sapi/overview/overview_pipeline.py`
- deterministic markdown/article rendering is owned by the overview pipeline helper and remains
  outside the semantic flow itself

Required inputs:
- canonical scope-selection manifest at `<space_root>/outputs/space_overview/<overview_id>/context.json`
- canonical source/claim/relation/topic inputs from `<space_root>/sources/records`, `<space_root>/claims`,
  `<space_root>/relations`, and `<space_root>/topics`
- optional `<space_root>/subspaces.json` to resolve subspace titles/roots when `scope_kind=subspace`

Refresh/skip contract:
- overview orchestration MUST compute a canonical `input_signature` from the current source/claim/relation/topic
  inputs before any semantic call.
- if `context.json`, `overview.json`, and `article.md` already exist and the persisted overview
  `freshness.input_signature` matches the current signature, the pipeline MUST skip semantic
  regeneration, leave existing overview artifacts untouched, and still write a committed run/lint
  record with `refresh_decision=skip` and `refresh_reason=no_content_change`.
- if overview artifacts are missing/invalid or the signature changed, the pipeline MUST regenerate
  overview artifacts and record the corresponding refresh reason.
- `scripts/generate_overview.py --force` MUST bypass the unchanged-signature skip path, record
  `force_mode=true`, and still use normal rollback semantics on terminal failure.

Semantic contract:
- run semantic flow `space_overview_generation`
- semantic output path is `<space_root>/outputs/space_overview/<overview_id>/overview.json`
- semantic output MUST satisfy `schemas/space_overview_generation.v1.schema.json`
- semantic output MUST contain exactly the five canonical section IDs plus auditable source/claim
  references and citation anchors

Deterministic post-processing boundary:
- deterministic stage MAY write `<space_root>/outputs/space_overview/<overview_id>/article.md` from
  the validated overview JSON
- deterministic stage MUST NOT invent new identifiers, anchors, or prose beyond formatting and
  projection of the semantic JSON content
- overview generation is additive only; it MUST NOT mutate canonical knowledge artifacts outside
  `outputs/space_overview/` and run/lint metadata
- if no source records are available, overview generation still writes `context.json`,
  `overview.json`, and `article.md`, marks the run `success_with_warnings`, and uses empty
  section/reference arrays instead of synthetic source or claim identifiers
- overview rendering MUST NOT issue web requests or additional LLM calls

## 9. Deterministic Build and Projection

Builder contracts:
- read canonical JSON only
- no LLM calls
- hard-fail on unresolved links/templates/conversion errors
- overview article markdown, when present, MUST be rendered deterministically from
  `outputs/space_overview/<overview_id>/overview.json`

Presentation asset and ownership contracts (normative implementation boundary):
- deterministic build MUST emit canonical stylesheet assets at `<render_root>/assets/site.css`
- rendered pages MUST include one viewport meta tag and one stylesheet link to `assets/site.css`
- template/render layer owns semantic HTML class hooks (`site-shell`, `site-sidebar`, `site-main`, `content-card`, `feed-list`, `topic-section`, `source-summary`)
- source feed rendering owns deterministic source order variants for date, citation count, and title; render
  pagination from the sorted source list, show available numeric citation counts on source cards, and cap
  feed-card author display at three visible authors plus an overflow marker
- topic feed rendering owns deterministic topic order variants for date, evidence count, claim count, and
  title; render pagination from the sorted topic list and compute visible topic metrics from canonical
  `claim_ids`, inline claim annotations, and validated evidence records
- list-index rendering owns shared order controls with active ascending/descending arrows; source, topic,
  new, user, claim, and evidence lists must render static order variants and make the active control link
  to the opposite direction
- CSS toolchain stage owns stylesheet compilation; missing or failed stylesheet generation is a build error
- build validation MUST assert stylesheet file existence and HTML link references before reporting success
- run/build metadata key `toolchain_versions.tailwind_cli` is informational only and MUST NOT be treated as compilation success evidence

High-level API:

```python
def build_space_site(space_root: Path, *, incremental: bool, compiled_stylesheet: bytes) -> BuildResult: ...
def refresh_site_new_index(site_path: Path, *, incremental: bool, compiled_stylesheet: bytes) -> Path: ...
```

Coalescing rule:
- ingest may execute both semantic flows then do one final projection/build pass if output is equivalent.

Site-root `New` refresh decision table:
- ingest/topic mutations: MUST refresh site-root `New` for same `<site_path>`
- query pipeline: MUST NOT refresh site-root `New`
- comment/profile pipelines: MUST NOT refresh site-root `New` unless they mutate canonical source/topic artifacts

Incremental rebuild rule:
- incremental refresh is allowed only when output is equivalent to deterministic full rebuild output

## 10. Relation Persistence Layer

Relation key model:
- semantic key: `relation_id`
- storage key: `relation_file_id = rel-<sha256_hex(relation_id)>`

Required API:

```python
def relation_file_id_from_relation_id(relation_id: str) -> str: ...
def write_relation(relation: dict[str, Any], space_root: Path) -> Path: ...
def read_relation(path: Path) -> dict[str, Any]: ...
```

Validation:
- persisted `relation_file_id` must match recomputed hash
- mismatch is validation error

## 11. Lint and Warning Threshold

Warning-threshold source (flag compatibility: `--warning-budget`):
1. default: `200`
2. override: `--warning-budget <int>` if valid positive integer
3. invalid override: fail fast with configuration error

Lint API:

```python
def evaluate_lint_gate(workflow: str, summary: LintSummary, warning_threshold: int) -> GateResult: ...
```

Workflow gate policy alignment (normative):
- lint-gated workflows fail when `error_count > 0`: `ingest_source`, `create_comments`, `generate_profiles`
- compatibility-only maintenance workflow `rebuild_topic_collection` (if present) follows the same lint-gated behavior
- `build_site` fails on conversion/link errors (independent of warning threshold)
- `query` is non-lint-blocking and MUST NOT fail solely from lint warnings/errors
- all pipelines still emit lint totals in run metadata for committed runs
- semantic pipeline entrypoints MUST populate `RunEnvelopeBase.lint_*` counts from a `LintSummary`
  and merge warning-budget status through the shared lint-gate helper before `finalize_pipeline_run`;
  callers MUST NOT hardcode zero-count lint summaries as a shortcut

## 12. Wrapper and Script Interfaces

Wrapper to script mapping:
- `ingest.sh` -> `scripts/ingest_source.py`
- `create_questions.sh` -> `scripts/create_prepared_questions.py`
- `query.sh` -> `scripts/query.py`
- `create_comments.sh` -> `scripts/create_comments.py`
- `generate_profiles.sh` -> `scripts/generate_profiles.py`
- `regenerate_web.sh` -> site build entrypoint
- `validate.sh` -> `scripts/lint.py`

Workflow-key alignment:
- `ingest.sh` -> workflow key `ingest_source`
- `create_questions.sh` -> no semantic workflow key; writes operator-authored canonical question
  records and never generates question text deterministically
- `query.sh` -> workflow key `query`
- `create_comments.sh` -> workflow key `create_comments`
- `generate_profiles.sh` -> workflow key `generate_profiles`
- `regenerate_web.sh` -> workflow key `build_site`
- `validate.sh` dispatches lint checks for workflow key selected via `--workflow`

Wrapper behavior:
- always inject `--registry-path <site_path>/spaces.toml` for registry-backed non-bootstrap scripts
- fail fast on removed non-canonical aliases instead of normalizing them

Required fail-fast behavior:
- ingest: `--force` is canonical and passed through (no alias)
- comments: reject `--user`, `--page`, positional `<n>`, and `--comment-web-evidence`

Removed ingest flags:
- ingest: `--source-only` and `--query-only` MUST fail fast.

Bootstrap exception:
- bootstrap wrappers (`create_site.sh`, `create_space.sh`) may run without an operator-supplied `--registry-path`

## 13. Observability, Runtime Controls, and Safety

Tracing/runtime controls:
- support runtime flags: `--verbose`, `--llm-trace`, `--llm-trace-dir`, `--trace-llm-io`, `--llm-timeout-secs`
- support LLM/runtime flags: `--llm-backend`, `--llm-model`, `--llm-reasoning-effort`, `--mock-llm`
- live semantic execution is Codex-only (`--llm-backend codex`); non-codex backend values are invalid in live mode
- default live model is read from `config/llm.json` (`default_live_model`); default reasoning is read from `config/llm.json` (`default_live_reasoning_effort`)
- default live timeout is disabled (`--llm-timeout-secs none`)
- when tracing is enabled, persist prompt/context/response/meta trace artifacts under site outputs

Mock-mode contract:
- `--mock-llm` is test-only
- output artifacts must still satisfy the same schemas/contracts as live mode
- run metadata must mark mock execution mode (for example `mock_llm_test`)

Safety constraints:
- cleanup logic must guard against dangerous roots
- avoid deletion outside explicit temp/staging roots
- avoid persisting machine-absolute paths in user-facing artifacts

## 14. Implementation Guardrails

### 14.1 Anti-drift rules

- do not duplicate schema/output contracts in multiple files
- generation spec remains semantic source of truth per flow
- keep semantic-flow key and pipeline-flow key namespaces distinct
- no hidden path aliases outside `<repo_root>`, `<site_path>`, `<space_root>`
- do not add environment-variable flow controls; use explicit CLI flags

### 14.2 PR review checks

Every pipeline-changing PR should answer:
1. Which canonical artifacts can this command mutate?
2. Which semantic flow keys can run, and in what order?
3. What exactly is rolled back on terminal failure?
4. Does run envelope include correct `flow_key`, ordered-unique `semantic_flows[]`, `semantic_flow_invocation_counts`, and required extension fields?
5. Are manifest outputs conditional by query format as required?
6. Are comments default-target rules, count bounds, and `comment_uid` stability preserved?
7. Are profile/history links canonical in rendered output?
8. Are site-root `New` refresh decisions correct for this flow?

### 14.3 Common failure patterns to reject

- writing failed-run artifacts outside explicit ingest `--force` mode
- skipping ingest rollback without explicit `--force`
- silently accepting invalid `--warning-budget`
- generating semantic output without schema validation
- mutating canonical knowledge artifacts inside query pipeline
- introducing secondary implicit registry fallback
- allowing strict/query mode incompatibilities to proceed

## 15. Test Plan Binding (Implementation-Level)

Minimum test groups for this low-level design:

- semantic executor:
  - success path
  - repair-loop success
  - repair-loop exhaustion + rollback
  - attempt budget accounting (`max_repair_loops`, `max_attempts`, `llm_attempt_count`)
  - spec-resolution flow map + unknown-flow rejection for removed aliases such as `persona_comment_generation`
- run envelopes:
  - base fields include fingerprints/reasoning/execution mode/lint totals
  - pipeline extension fields are present and typed per flow
  - ingest has pipeline `flow_key` and two semantic flows, plus optional `source_revision_detection`
    only when automatic revision detection actually runs
  - `semantic_flows` is ordered-unique and `semantic_flow_invocation_counts` records call counts
  - default terminal failures leave no committed `runs/<run_id>/` container
  - ingest `--force` failures persist run container and set `force_mode=true`, `rollback_skipped=true`
- query manifests and preflight:
  - non-markdown writes manifest
  - markdown writes no manifest and null/omitted `manifest_path`
  - strict + include-disputed fails fast
- ingest bootstrap mode:
  - deferred-build metadata (`build_deferred`, reason) written when enabled
  - deferred-build backfill path clears backlog
- ingest force mode:
  - terminal failure preserves partial artifacts only when `--force` is set
  - no-force terminal failures continue to rollback fully
- comments:
  - default target set is topics only
  - one semantic artifact is written per target page under `runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json`
  - explicit source/claim targeting allowed
  - `--count` bounds enforced (`5..50`)
  - single-call-per-page default with chunk fallback equivalence
  - `comment_uid` stability in merge
  - web-augmented evidence snapshot path/schema contract
- profiles:
  - `generate_profiles.sh` path produces profile + history outputs
  - persona-catalog loader enforces biography quality contract (generation-facing first-person `biography`, profile-facing `biography_profile`), required `short_cv` timeline rows, non-empty topic arrays, `.jpg` profile image path contract, and photorealistic `profile_image_prompt` contract.
- source dossiers:
  - ingest extraction requires `source_dossier` object (`summary_short`, `summary_long`, `sections[]`)
  - high-quality dossier targets: `summary_long >= 900 chars` and `5..8` substantive sections
  - canonical source record persists `source_dossier` from ingest extraction output
  - source detail renderer uses `source_dossier` as the primary long-form commentary payload
  - source-page dossier sections may include `grounding_claim_ids` links into canonical claim pages
- source analysis artifacts:
  - canonical source artifact set includes original binary, `source.md`, `source_extraction.json`,
    preview image (optional), and `overview.md`
  - `source_extraction.json` records converter identity/version, input/output hashes, warnings,
    and markdown quality status
  - downstream deterministic analysis helpers MUST prefer `source.md` unless `analysis_policy`
    explicitly marks it `unusable`
- external related links:
  - source records may persist curated `external_related_links[]` and `related_link_enrichment`
  - deterministic build aggregates these links onto source/topic/claim pages without issuing web requests
  - reference DOI/arXiv identifiers remain bibliography/source-linking metadata and are not promoted
    into `external_related_links[]`
  - topic and claim pages inherit only contextual link classes from sources: `encyclopedia`,
    `repository`, and `discussion_forum`
  - supported default `link_type` values are `canonical_paper`, `primary_source`, `research_index`,
    `encyclopedia`, `repository`, and `discussion_forum`
  - deterministic aggregation de-duplicates by normalized URL and preserves source provenance cues
- claim pages:
  - claim pages resolve canonical claim JSON under `<space_root>/claims/` and topic/source usage references.
  - page title uses readable claim text when available; `claim_id` remains visible in metadata/audit context.
  - page body includes claim statement, usage links, overview prose, linked evidence items, and comments section placeholder/rendered thread.
  - claim support score shown in UI is currently deterministic heuristic-only; no canonical math formula exists in the contract.
- site refresh behavior:
  - ingest/topic refresh site-root `New`
  - query/comment/profile do not refresh site-root `New` unless source/topic mutation occurs
- wrapper normalization:
  - alias normalization and deprecation warnings
  - canonical+alias conflict fails fast
  - bootstrap wrappers can omit explicit registry path
- lint warning threshold:
  - default `200`
  - CLI override valid
  - CLI override invalid fails

## 16. Change Discipline

When implementation requires behavior change:
1. update `design.md` first if contract-level
2. update this file second with module/control-flow implications
3. then patch code/tests

This keeps architecture intent, implementation plan, and code in sync.
