# Sapi Completed TODO Log

This file is append-only history for completed tasks moved out of `docs/todo.md`.

## 2026-04-24

- [x] TODO-0339: Implement canonical `space_overview_generation` semantic flow and artifacts
  - owner: ai
  - created_at: 2026-04-16
  - finished_at: 2026-04-24
  - phase: Phase 6
  - depends_on: TODO-0338
  - scope: Add a pipeline that synthesizes a long-form topic overview from ingested sources/claims/relations for each space (and selected subspaces), using shared semantic execution policy.
  - acceptance:
    - Pipeline writes canonical artifacts under `spaces/<space_name>/outputs/space_overview/<overview_id>/` including structured JSON and markdown article outputs.
    - JSON artifact includes required sections: topic framing, key themes, agreement/disagreement map, methods/evidence landscape, open questions, and citation anchors.
    - Output sections include auditable references to canonical `source_id` and `claim_id` values.
    - Run envelopes include canonical flow key (`space_overview_generation`) and accurate attempt/invocation accounting.
    - Pipeline handles “no ingested sources” as a clear non-crashing outcome with explicit warning/status metadata.
  - notes: source `docs/design.md` Sections 7.2.1 and 10; `docs/low_level.md` Sections 3, 4, and 8.5
  - evidence: Added `sapi/overview/overview_pipeline.py` plus the direct entrypoint
    `scripts/generate_overview.py`, including deterministic `context.json` staging, canonical
    `overview.json` validation, deterministic `article.md` rendering, run/lint metadata via the new
    `overview_pipeline` flow key, and explicit `success_with_warnings` handling for no-source
    scopes. Updated the overview schema/spec to allow the no-source warning path without synthetic
    citations, expanded docs/testing topology for the new overview package/entrypoint, and added
    unit/integration coverage for scope resolution, overview artifact writes, warning-mode runs,
    rollback, and run-envelope/lint workflow invariants.

- [x] TODO-0338: Define canonical contracts for space/subspace overview synthesis
  - owner: ai
  - created_at: 2026-04-16
  - finished_at: 2026-04-24
  - phase: Cross-cutting
  - scope: Specify artifact schema, flow ownership, and deterministic rendering boundaries for AI-generated overview articles that summarize all ingested papers in a space/subspace.
  - acceptance:
    - `docs/design.md` and `docs/low_level.md` define normative behavior for overview synthesis inputs, outputs, and citation/auditability requirements.
    - A canonical schema is added for overview artifact JSON payloads (sections, references, metadata, freshness fields).
    - Semantic flow contract entry is added for `space_overview_generation` with canonical output path tokens.
    - Contract tests verify schema/docs/flow-spec alignment and fail on drift.
  - notes: source `docs/design.md` Sections 4.1.3, 4.1.4, and 7.2.1; `docs/low_level.md` Sections 2, 4, and 8.5
  - evidence: Added the canonical `space_overview_generation` flow-map entry plus checked-in
    generation spec and `space_overview_generation.v1` schema, including deterministic output and
    context path tokens under `outputs/space_overview/<overview_id>/`. Updated `design.md` and
    `low_level.md` to define overview inputs, required sections, citation anchors, freshness
    metadata, and deterministic rendering boundaries, and added contract tests covering the flow
    map, invocation envelope, schema section requirements, run-envelope semantic key set, and
    inventory/doc alignment.

- [x] TODO-0326: Remove relation status compatibility alias `closed`
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove acceptance/normalization of relation status `closed`; accept only canonical status values.
  - acceptance:
    - `sapi/ingest/relation_store.py` rejects `closed` status inputs.
    - Tests and docs no longer describe `closed` as accepted alias.
  - notes: source `docs/design.md` Section 7.1
  - evidence: Removed `closed` from the allowed relation status set in
    `sapi/ingest/relation_store.py`, so relation normalization now rejects the removed alias
    instead of rewriting it to `resolved`. Updated the relation-store matrix and ingest canonical
    write tests to assert fail-fast `ValueError` behavior for `status: closed`, and tightened the
    ingest design/doc-contract assertions so the canonical-only relation status rule is explicit.

- [x] TODO-0325: Remove site-scope legacy fallback reader (`<space_root>/site.json`)
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove `allow_legacy_space_scope_read` behavior from site-scope loading and enforce canonical `<site_path>/site.json` only.
  - acceptance:
    - `sapi/core/site_scope.py` no longer contains legacy fallback branch/flag.
    - Site-scope tests assert missing canonical file fails without legacy fallback mode.
  - notes: source `docs/design.md` Section 5.7
  - evidence: Removed the `load_site_scope()` compatibility parameters and the legacy
    `<space_root>/site.json` read branch from `sapi/core/site_scope.py`, so canonical readers now
    load only `<site_path>/site.json`. Updated the dedicated site-scope contract test to assert
    that a legacy-only `space_root/site.json` no longer loads and instead raises the expected
    missing-canonical-file error, then synchronized `docs/todo.md` to reflect the closed
    site-scope compatibility item.

- [x] TODO-0324: Remove registry entry compatibility key `name`
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Stop accepting historical registry key `name`; require `space_name` only.
  - acceptance:
    - `sapi/core/registry.py` rejects registry entries without `space_name`.
    - Registry tests cover rejection of `name`-only entries.
  - notes: source `docs/design.md` Section 5; `docs/low_level.md` Section 5
  - evidence: Removed the registry loader fallback that treated `name` as a compatibility alias
    for `space_name` in `sapi/core/registry.py`, so registry entries now fail fast unless they
    provide the canonical `space_name` key. Added a registry contract test that writes a
    `name`-only `[[spaces]]` entry and asserts `load_registry()` raises the expected
    missing-`space_name` validation error, then synchronized `docs/todo.md` to reflect the closed
    path/registry contract item.

- [x] TODO-0323: Remove legacy parent reference alias `pc-###`
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove ordinal parent-reference compatibility in comment normalization.
  - acceptance:
    - `sapi/comments/merge_normalize.py` no longer resolves `pc-###` as parent refs.
    - Comment merge tests assert legacy ordinal parent refs fail validation.
  - notes: source `docs/design.md` Section 7.6; `docs/low_level.md` Section 8.3
  - evidence: Removed the `pc-###` parent-reference resolution path from
    `sapi/comments/merge_normalize.py`, so comment normalization now accepts only canonical
    `parent_comment_uid` values and in-batch `draft-N` refs. Updated the comment unit and
    integration tests to assert fail-fast rejection of ordinal parent refs, and synchronized the
    design/low-level contract text plus doc-contract assertions with the canonical-only rule.

- [x] TODO-0322: Remove rebuttal-field alias `steelman_before_rebuttal`
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Enforce only canonical rebuttal field `strongest_opposing_point_ack`.
  - acceptance:
    - Comment normalization rejects `steelman_before_rebuttal`.
    - Tests and contracts use only canonical rebuttal field naming.
  - notes: source `docs/design.md` Section 7.6; `docs/low_level.md` Section 8.3
  - evidence: Removed the `steelman_before_rebuttal` compatibility path from
    `sapi/comments/merge_normalize.py`, so rebuttal normalization now accepts only canonical
    `strongest_opposing_point_ack` and raises a validation error when the removed alias is present.
    Updated the rebuttal unit and integration tests to assert fail-fast rejection, and tightened the
    design/low-level contract text plus doc-contract assertions to use only canonical naming.

- [x] TODO-0321: Remove legacy HTML turn-marker compatibility
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove support for `<!-- turn:{...} -->` marker format and allow only canonical `<<turn:{...}>>`.
  - acceptance:
    - `sapi/comments/merge_normalize.py` parses only canonical inline marker.
    - Tests assert legacy marker usage fails fast.
  - notes: source `docs/design.md` Section 7.6; `docs/low_level.md` Section 8.3
  - evidence: Removed the legacy HTML marker branch from `sapi/comments/merge_normalize.py`, so
    comment normalization now accepts only canonical inline `<<turn:{...}>>` markers and raises a
    validation error for `<!-- turn:{...} -->`. Updated the turn-marker unit and integration tests to
    require fail-fast behavior, and added an explicit low-level doc contract assertion for the
    canonical-only marker policy.

- [x] TODO-0320: Remove discussion-controls legacy aliases and frontmatter fallback
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove `persona_discussion_*` key/schema aliases and remove canonical-page fallback to legacy frontmatter controls.
  - acceptance:
    - `sapi/comments/controls.py` accepts only canonical schema/key names.
    - Legacy frontmatter-only controls are no longer imported into effective/canonical controls.
    - Tests and docs reflect canonical-only controls behavior.
  - notes: source `docs/design.md` Section 7.6; `docs/low_level.md` Section 8.3
  - evidence: Removed the discussion-controls schema/key alias maps and frontmatter fallback from
    `sapi/comments/controls.py`, so only canonical `comment_section_discussion_controls_v1` payloads
    and canonical control keys participate in effective controls. Updated `scripts/create_comments.py`
    to stop writing canonical page metadata derived from legacy frontmatter, replaced the
    discussion-controls unit and integration tests with canonical-only coverage, and tightened the
    design/low-level contract text plus doc-contract assertions.

- [x] TODO-0319: Remove persona/topic identity legacy aliases (`id`, `narrative_id`)
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 5
  - depends_on: TODO-0313
  - scope: Remove compatibility aliases `Persona.id` and `TopicPage.narrative_id`, and remove loader mapping from persona row `id` to `persona_id`.
  - acceptance:
    - `sapi/contracts/domain_models.py` enforces canonical identity keys only.
    - `sapi/profiles/persona_catalog.py` requires explicit `persona_id`; `id` alias mapping is removed.
    - Tests and docs no longer rely on `id`/`narrative_id` aliases.
  - notes: source `docs/design.md` Sections 3, 5.4, and 7.4
  - evidence: Removed the `Persona.id` and `TopicPage.narrative_id` compatibility fields from
    `sapi/contracts/domain_models.py`, so canonical models reject those alias keywords at
    construction time. Updated `sapi/profiles/persona_catalog.py` to require explicit
    `persona_id` and fail fast when repository persona rows still carry a legacy `id` field, then
    rewrote the domain-model, persona-catalog, and persona-doc contract tests to cover canonical-only
    identity handling.

- [x] TODO-0318: Remove direct-script compatibility aliases for comments entrypoint
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove hidden CLI alias inputs in `scripts/create_comments.py` (`--user`, `--page`, `--comment-web-evidence`).
  - acceptance:
    - Parser no longer accepts deprecated alias flags.
    - Evidence mode is controlled only by canonical `--comment-evidence-mode`.
    - Script-level tests assert alias flags fail as unknown arguments.
  - notes: source `docs/design.md` Section 7.6; `docs/low_level.md` Sections 8.3 and 12
  - evidence: Removed the hidden `--user`, `--page`, and `--comment-web-evidence` arguments from
    `scripts/create_comments.py`, so the direct comments entrypoint now accepts only canonical
    `--comment-user`, `--comment-page`, and `--comment-evidence-mode` inputs. Updated
    `tests/unit/contracts/test_runtime_flag_surface.py` to assert the removed flags are absent from
    the parser surface and fail as unrecognized arguments when passed to `argparse`.

- [x] TODO-0317: Remove semantic flow-key compatibility alias `persona_comment_generation`
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove flow alias normalization/deprecation path and require canonical `comment_section_generation`.
  - acceptance:
    - `sapi/contracts/semantic_specs.py` no longer contains `FLOW_ALIAS_MAP` compatibility alias for comment flow.
    - Resolution tests assert alias keys fail as unknown flow keys.
  - notes: source `docs/design.md` Section 4.1.3; `docs/low_level.md` Sections 6.1 and 15
  - evidence: Removed the alias-map/deprecation path from
    `sapi/contracts/semantic_specs.py` so semantic spec resolution now accepts only canonical flow
    keys. Updated `tests/unit/semantic/test_spec_resolution.py` to require `ValueError` for
    `persona_comment_generation` in both direct spec resolution and invocation-spec resolution, and
    rewrote the low-level test-plan note to describe unknown-flow rejection instead of alias
    normalization.

- [x] TODO-0316: Remove wrapper-level compatibility aliases in `create_comments.sh`
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove wrapper normalization for legacy positional count and aliases `--user`/`--page`; accept only canonical flags.
  - acceptance:
    - `create_comments.sh` accepts only `--count`, `--comment-user`, and `--comment-page`.
    - Wrapper tests assert legacy positional count and alias flags fail fast.
  - notes: source `docs/design.md` Section 7.6; `docs/low_level.md` Sections 8.3 and 12
  - evidence: Updated `create_comments.sh` to stop normalizing positional count, `--user`,
    and `--page`, and to fail fast on those removed wrapper inputs plus
    `--comment-web-evidence`. Updated wrapper-facing assertions in
    `tests/integration/wrappers/test_wrapper_alias_normalization.py`,
    `tests/integration/wrappers/test_wrapper_alias_conflicts.py`, and
    `tests/unit/contracts/test_wrapper_alias_normalization.py` so they now require usage
    failures instead of deprecation warnings and successful forwarding.

- [x] TODO-0315: Remove ingest wrapper/entrypoint alias `--query-only`
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Phase 4
  - depends_on: TODO-0313
  - scope: Remove deprecated ingest alias `--query-only` from wrapper and Python entrypoint.
  - acceptance:
    - `ingest.sh` and `scripts/ingest_source.py` reject both `--query-only` and `--source-only`.
    - Tests assert removed ingest mode flags fail as invalid input.
  - notes: source `docs/design.md` Sections 6.1 and 7.1; `docs/low_level.md` Sections 2 and 12
  - evidence: Confirmed `ingest.sh` already hard-fails on both removed flags and
    `scripts/ingest_source.py` already rejects them through its canonical parser surface. Existing
    wrapper and entrypoint tests in `tests/integration/wrappers/test_wrapper_alias_normalization.py`,
    `tests/integration/wrappers/test_wrapper_alias_conflicts.py`, and
    `tests/unit/ingest/test_ingest_mode_handling.py` already cover failure behavior; this run added
    `tests/unit/contracts/test_runtime_flag_surface.py` coverage to assert the ingest parser does not
    expose `--source-only` or `--query-only` as valid flags.

- [x] TODO-0314: Remove compatibility-reader sunset policy and alias acceptance language from contracts
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Cross-cutting
  - depends_on: TODO-0313
  - scope: Update `docs/design.md` and `docs/low_level.md` so contracts are canonical-only and no longer permit compatibility alias acceptance.
  - acceptance:
    - Design/low-level docs remove compatibility alias acceptance policy and deprecation wording for removed paths.
    - Contract tests are updated to canonical-only assertions.
  - notes: source `docs/design.md` Sections 4.1.3 and 7.6; `docs/low_level.md` Sections 6.1, 8.3, and 12
  - evidence: Rewrote the design and low-level contracts to remove compatibility sunset/deprecation
    wording and alias-acceptance clauses for canonical flow keys, comment CLI flags, discussion
    control schemas, turn markers, site-scope readers, and legacy identity/page-id fields. Added
    `tests/unit/contracts/test_canonical_only_doc_contracts.py` and updated
    `tests/unit/contracts/test_todo_recommendation_intake.py` so doc-contract assertions now require
    canonical-only wording instead of the retired sunset-policy text.

- [x] TODO-0313: Compatibility purge tracker for canonical-only boundary
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-24
  - phase: Cross-cutting
  - scope: Track complete removal of legacy/backward-compatibility behaviors across wrappers, semantic flow keys, domain models, comment controls/markers, registry/site scope, and relation status handling.
  - acceptance:
    - All compatibility pathways enumerated in TODO-0314..TODO-0327 are represented in discrete tasks.
    - Queue/coverage snapshots in this file are synchronized to those tasks.
  - notes: source `docs/todo.md` queue and coverage snapshot sections
  - evidence: Audited the open compatibility-purge chain and confirmed every enumerated pathway is
    covered by the discrete leaf tasks `TODO-0314..TODO-0327`. Removed `TODO-0313` from the open
    Ready Now, priority, execution-queue, and coverage snapshot sections, promoted the leaf tasks
    into the ready queue, and added `tests/unit/contracts/test_compatibility_purge_tracker_closure.py`
    so the tracker stays closed once its bookkeeping role is complete.

- [x] TODO-0350: Add related-link quality gates and coverage
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Phase 2
  - depends_on: TODO-0348, TODO-0349
  - scope: Add validation, allowlist/ranking rules, provenance checks, and test coverage for externally-related links so source/topic/claim pages surface useful links without degrading trust.
  - acceptance:
    - Unit/integration tests cover applicable-link selection, de-duplication, unsupported domains or low-signal candidates, and rollback or warning behavior when related-link enrichment fails.
    - `docs/testing_plan.md` is updated with explicit related-link enrichment and rendering coverage expectations.
    - Coverage asserts page rendering degrades gracefully when no external links qualify.
    - Operator-facing artifacts and metadata surface provenance and link-quality warnings when present.
  - notes: source `docs/design.md` Section 7.2; `docs/testing_plan.md` Tier 1-4
  - evidence: Added deterministic related-link enrichment/validation in `sapi/ingest/citations.py`,
    early source-record validation in `sapi/build/projection.py`, source/topic/claim rendering coverage
    in `tests/unit/build/test_site_builder_contracts.py`, and ingest/reference-linking coverage in
    `tests/unit/ingest/test_reference_linking.py`.

- [x] TODO-0349: Render external related-link sections on source/topic/claim pages
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Phase 2
  - depends_on: TODO-0347, TODO-0348
  - scope: Surface curated external related links on source, topic, and claim pages, including stable section labeling, provenance cues, and deterministic aggregation of inherited links where appropriate.
  - acceptance:
    - `sapi/build/site_builder.py` renders a dedicated external related-links section on source, topic, and claim pages when qualifying links exist.
    - Topic and claim pages deterministically aggregate or inherit applicable links from canonical source/topic context without inventing unsupported associations.
    - Rendering includes link title, domain/source type, optional rationale/snippet, and provenance cues without breaking existing local-reference sections.
    - If no qualifying external links exist, pages render without empty placeholders or broken layout.
  - notes: source `docs/design.md` Sections 7.1-7.2; `docs/low_level.md` Section 8.1
  - evidence: Added source analysis/external-link rendering helpers and deterministic aggregation in
    `sapi/build/site_builder.py`, plus page-contract coverage in
    `tests/unit/build/test_site_builder_contracts.py`.

- [x] TODO-0348: Implement related-link enrichment and persistence for canonical artifacts
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Phase 2
  - depends_on: TODO-0347
  - scope: Add an explicit enrichment path that discovers and persists applicable external links for sources, then makes them available for deterministic projection onto source/topic/claim pages.
  - acceptance:
    - Canonical artifacts persist curated related-link metadata with title, URL, domain/source type, rationale, provenance, and confidence/quality fields.
    - Enrichment behavior is explicit and auditable rather than an uncontrolled implicit web fallback during page rendering.
    - Source-linked external references can be propagated deterministically to related topic/claim pages under documented rules.
    - Run or source metadata records link-enrichment provenance, warnings, and skip reasons.
  - notes: source `docs/design.md` Section 7.2
  - evidence: `sapi/ingest/citations.py` now writes `external_related_links` and
    `related_link_enrichment` into canonical source records from canonical identifiers, source locator,
    and allowlisted reference URLs; `scripts/ingest_source.py` surfaces related-link counts in ingest
    summaries.

- [x] TODO-0347: Define canonical external related-link contracts for sources, topics, and claims
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Cross-cutting
  - scope: Specify the contract for surfacing curated external related links such as Wikipedia pages, discussion forums, documentation pages, and other relevant online resources on source/topic/claim pages.
  - acceptance:
    - `docs/design.md` and `docs/low_level.md` define canonical storage, provenance, and rendering rules for external related links on sources, topics, and claims.
    - Contracts distinguish external related links from canonical source citations/references and require explicit provenance plus quality-status metadata.
    - Allowed link classes, ranking/de-duplication rules, and low-trust or irrelevant-link rejection behavior are specified.
    - Contract tests are added or updated to fail on docs/schema/path drift for the new related-link fields and rendering expectations.
  - notes: source `docs/design.md` Section 7.2; `docs/low_level.md` Sections 8.1 and 15
  - evidence: Updated `docs/design.md`, `docs/low_level.md`, and `docs/testing_plan.md`; added
    `tests/unit/contracts/test_source_analysis_and_related_link_contracts.py`.

- [x] TODO-0346: Add source-markdown extraction quality gates and coverage
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Phase 2
  - depends_on: TODO-0344, TODO-0345
  - scope: Add validation, failure semantics, and test coverage for markdown extraction quality, provenance persistence, and markdown-first analysis behavior.
  - acceptance:
    - Unit/integration tests cover successful extraction, unusable markdown output, fallback routing, and rollback or `--force` retention semantics when extraction or downstream analysis fails.
    - `docs/testing_plan.md` is updated with explicit markdown-extraction and markdown-first analysis coverage expectations.
    - Operator-facing review artifacts surface extraction provenance and markdown-quality warnings when present.
    - Coverage asserts semantic flows do not silently fall back to raw binary analysis when markdown is required by contract.
  - notes: source `docs/design.md` Sections 5.3 and 7.1; `docs/testing_plan.md` Tier 1-3
  - evidence: Added markdown quality classification and provenance persistence in
    `sapi/ingest/records_writer.py`, markdown-first deterministic reads in `sapi/ingest/citations.py`,
    ingest acquisition coverage in `tests/unit/ingest/test_source_acquisition.py`, and contract/spec
    coverage in `tests/unit/semantic/test_input_envelope_contract.py`.

- [x] TODO-0345: Route semantic analysis to source markdown with explicit fidelity fallback
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Phase 2
  - depends_on: TODO-0343, TODO-0344
  - scope: Update semantic-flow context resolution so analysis-oriented LLM calls prefer extracted source markdown while preserving controlled access to the original binary for fidelity-sensitive cases such as tables, graphs, and figures.
  - acceptance:
    - Ingest and downstream analysis-oriented semantic flows use extracted `source.md` as the default source-reading input instead of raw binary artifacts.
    - The original binary remains preserved and available to deterministic rendering and explicitly-declared fidelity-sensitive enrichment paths.
    - Fallback policy for missing or low-quality markdown is explicit, auditable, and recorded in source/run metadata.
    - Contract tests verify markdown-preferred context selection and no-drift behavior in generation-spec path resolution.
  - notes: source `ai_flows/generation_specs/ingest_extraction.v1.md`; `docs/design.md` Section 7.1
  - evidence: Updated the ingest extraction generation spec to point at `sources/records` and
    `sources/artifacts` with explicit markdown-first instructions; deterministic reference extraction
    now reads `source.md` first and records fallback policy in source records.

- [x] TODO-0344: Persist extracted source markdown and provenance during ingest
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Phase 2
  - depends_on: TODO-0343
  - scope: Extend ingest artifact persistence to generate and store analysis-oriented markdown plus extraction provenance alongside the original binary, initially via a pluggable converter adapter with MarkItDown as the first backend candidate.
  - acceptance:
    - Ingest writes canonical `source.md` and `source_extraction.json` files under `<space_root>/sources/artifacts/<source_id>/` beside the original binary.
    - Extraction provenance records converter name/version, options, status, warnings, and input/output hashes without persisting machine-absolute paths in user-facing artifacts.
    - Source records point to the original artifact, extracted markdown, and extraction metadata.
    - Ingest reports clear failure or warning behavior when extraction cannot produce contract-compliant markdown.
  - notes: source `docs/design.md` Section 5.3
  - evidence: `sapi/ingest/records_writer.py` now persists `source.md` and
    `source_extraction.json`, records extraction status/quality metadata on the source record, and
    tracks both new files for rollback in `scripts/ingest_source.py`.

- [x] TODO-0343: Define canonical source-markdown analysis artifact contracts
  - owner: ai
  - created_at: 2026-04-24
  - finished_at: 2026-04-24
  - phase: Cross-cutting
  - scope: Specify the canonical storage, provenance, and usage rules for preserving original source binaries together with extracted markdown that becomes the primary analysis substrate for semantic flows.
  - acceptance:
    - `docs/design.md` and `docs/low_level.md` define canonical source-artifact layout including the original binary, extracted `source.md`, and extraction provenance metadata.
    - Contracts state that markdown is the default LLM analysis input while original binaries remain preserved for fidelity-sensitive workflows involving tables, graphs, figures, or extraction fallback.
    - The extraction metadata contract includes converter identity/version, input hash, output hash, warnings, and quality-status fields.
    - Contract tests are added or updated to fail on docs/schema/path drift for the new artifact set.
  - notes: source `docs/design.md` Section 5.3; `docs/low_level.md` Section 8.1
  - evidence: Updated source-artifact/storage and ingest-pipeline contracts in `docs/design.md`
    and `docs/low_level.md`, then added synchronized contract assertions in
    `tests/unit/contracts/test_source_analysis_and_related_link_contracts.py`.

## 2026-04-13

- [x] TODO-0333: Add deterministic style-output and presentation contract tests
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0331, TODO-0332
  - scope: Add/refresh tests to prove stylesheet linking, generated CSS assets, and deterministic/stable styled output contracts.
  - acceptance:
    - Unit/integration tests assert rendered pages include canonical stylesheet link and responsive viewport metadata.
    - Build contract tests assert compiled CSS asset exists and deterministic rebuild output remains byte-stable.
    - Wrapper/build tests fail when CSS asset generation contract is broken.
  - notes: source `docs/testing_plan.md` Tier 4; `docs/design.md` Section 8; `docs/low_level.md` Section 9
  - evidence: Extended unit and integration coverage to assert viewport + stylesheet-link contracts and deterministic stylesheet assets:
    `tests/unit/build/test_site_builder_contracts.py`,
    `tests/integration/build/test_build_determinism.py`,
    and `tests/integration/build/test_incremental_vs_full_equivalence.py`.
    Added an explicit stylesheet-contract failure test by removing required pipeline input
    file (`web/styles/site.css`) and verifying `scripts/build_site.py` fails fast.

- [x] TODO-0332: Modernize deterministic HTML renderer layout and component structure
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0330, TODO-0331
  - scope: Refactor site HTML rendering to modern, responsive semantic component structure (cards/nav/sidebar/feed/topic/source pages) while preserving deterministic output rules.
  - acceptance:
    - `sapi/build/site_builder.py` removes inline style attributes and emits stable semantic class structure for primary pages.
    - Space/site/topic/source/user/feed pages render with consistent modern layout hooks and accessibility-focused nav/focus semantics.
    - Existing deterministic render contracts remain green with updated snapshots/assertions where required.
  - notes: source `docs/design.md` Section 8
  - evidence: Reworked layout rendering in `sapi/build/site_builder.py` to emit semantic hooks
    (`site-shell`, `site-sidebar`, `site-main`, `content-card`, `feed-list`, `topic-section`,
    `source-summary`), removed inline style attributes, and standardized viewport/stylesheet
    metadata across space and site-root pages. Updated golden fixtures in
    `tests/golden/site_snapshot/space_home_empty.html` and
    `tests/golden/site_snapshot/site_root_index_empty.html`.

- [x] TODO-0331: Implement Tailwind/PostCSS asset pipeline in deterministic site build
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0330
  - scope: Add actual CSS toolchain execution (Tailwind + PostCSS/autoprefixer) and deterministic stylesheet emission under build outputs.
  - acceptance:
    - `package.json` + lockfile declare/pin required frontend dependencies (`tailwindcss`, `postcss`, `autoprefixer`) and reproducible build scripts.
    - `scripts/build_site.py` compiles canonical CSS into site assets and hard-fails on toolchain/CSS build errors.
    - Build manifest captures concrete Tailwind toolchain version (not `not_declared`) and emitted CSS artifact metadata.
  - notes: source `docs/design.md` Section 8; `docs/low_level.md` Section 9
  - evidence: Added deterministic stylesheet pipeline files under `web/styles/` and wired
    `scripts/build_site.py` to run Tailwind + PostCSS, emit `site/assets/site.css` and
    `spaces/<space>/site/assets/site.css`, and persist `stylesheet_assets` metadata in
    `outputs/build_site/manifest.json`. Updated `package.json` + `package-lock.json` with
    pinned `tailwindcss`, `postcss`, `postcss-cli`, and `autoprefixer`.

- [x] TODO-0330: Define canonical web-presentation contract for modern styled output
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Cross-cutting
  - scope: Update contracts to require modern deterministic UI presentation semantics
    (stylesheet contract, responsive metadata, semantic component classes, deterministic CSS
    asset policy).
  - acceptance:
    - `docs/design.md` Section 8 and corresponding `docs/low_level.md` sections define
      normative styling/render contracts including CSS asset ownership and determinism
      boundaries.
    - `docs/testing_plan.md` includes explicit coverage requirements for presentation
      contract checks.
    - Contract wording resolves current Tailwind/toolchain ambiguity by distinguishing
      declaration-only metadata from required build behavior.
  - notes: source `docs/design.md` Section 8; `docs/low_level.md` Section 9;
    `docs/testing_plan.md` Tier 4
  - evidence: Added normative "Canonical presentation contract" requirements in
    `docs/design.md` (viewport tag, canonical stylesheet link, semantic class hooks, ownership
    boundary, and metadata-vs-build ambiguity guardrail), plus implementation-boundary clauses
    in `docs/low_level.md` Section 9 and explicit presentation test requirements in
    `docs/testing_plan.md`. Added
    `tests/unit/contracts/test_web_presentation_contracts.py` to assert these contracts are
    present and synchronized across all three docs.

- [x] TODO-0312: Close Section 6 testing exit criteria with explicit evidence
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Cross-cutting
  - depends_on: TODO-0311
  - scope: Convert remaining Section 6 exit criteria into explicit verification evidence and only then mark criteria complete.
  - acceptance:
    - Exit criteria checks produce concrete evidence references (commands/artifacts) for each unchecked Section 6 bullet.
    - `docs/testing_plan.md` Section 6 checkboxes are updated only with linked evidence.
    - `docs/todo_finished.md` records completion evidence for this gate.
  - notes: source `docs/testing_plan.md` Section 6
  - evidence: Regenerated committed exit-gate evidence with
    `python3 scripts/verify_testing_exit_criteria.py verification/testing_exit_site --space-name alpha --out verification/testing_exit_criteria.latest --evidence-path verification/testing_exit_criteria.latest.json`
    and updated Section 6 checkboxes in `docs/testing_plan.md` to include explicit linked
    command/artifact references to
    `verification/testing_exit_criteria.latest.json` and
    `verification/testing_exit_criteria.latest/manifest.json`.

- [x] TODO-0311: Add deterministic helpers for run/lint and rollback assertions
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 4
  - scope: Add reusable helpers in `tests/conftest.py` for `run.md`, `lint.json`, and rollback-cleanup assertions, then adopt them in failure tests.
  - acceptance:
    - `tests/conftest.py` includes helper APIs for run-frontmatter assertions, lint artifact assertions, and rollback cleanup checks.
    - At least one failure integration module uses the new helpers.
    - Tier 0 helper checklist item is marked complete in `docs/testing_plan.md`.
  - notes: source `docs/testing_plan.md` Tier 0
  - evidence: Added helper APIs in `tests/conftest.py`
    (`assert_run_frontmatter_fields`, `assert_lint_artifact`, `assert_rollback_cleanup`) and
    wired them into integration tests: rollback assertions in
    `tests/integration/failure/test_postprocess_failure_rollback.py` and run/lint assertions in
    `tests/integration/pipelines/test_ingest_pipeline.py` and
    `tests/integration/pipelines/test_ingest_force_mode.py`. Marked Tier 0 helper checklist item
    complete in `docs/testing_plan.md`.

- [x] TODO-0225: Comment quality benchmark and evaluation manifest pipeline
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0223
  - scope: Implement benchmark scoring and evaluation manifest generation for comment quality checks.
  - acceptance:
    - Benchmark artifact and schema contracts are implemented.
    - Evaluation manifest writes to `outputs/comment_quality/<evaluation_id>/manifest.json`.
    - Threshold pass/fail and fail reasons are persisted deterministically.
  - notes: source `design.md` Section 7.7
  - evidence: Added canonical benchmark and schema contracts at
    `sapi/benchmarks/comment_quality_benchmark_v1.json`,
    `schemas/comment_section_quality_benchmark_v1.schema.json`, and
    `schemas/comment_section_quality_eval_manifest_v1.schema.json`. Implemented deterministic
    benchmark loading/scoring/threshold evaluation in `sapi/comments/quality.py`, including
    canonical `evaluation_id` generation (`CQ-<sha256-prefix>`) and deterministic fail-reason
    ordering. Wired `scripts/create_comments.py` to emit a validated quality manifest at
    `outputs/comment_quality/<evaluation_id>/manifest.json` for comment runs. Added coverage in
    `tests/unit/comments/test_comment_quality_manifest.py` and
    `tests/integration/pipelines/test_comments_pipeline.py`.

## 2026-04-12

- [x] TODO-0248: Implement discussion-controls precedence and canonical metadata integration
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0236
  - scope: Implement discussion-controls loading and precedence (`defaults -> per-page controls -> canonical page metadata`) with compatibility readers.
  - acceptance:
    - Site controls are read from canonical file/schema and fallback safely when missing/invalid.
    - Canonical page JSON metadata overrides frontmatter when both are present.
    - New writes target canonical page JSON metadata, not markdown frontmatter.
  - notes: source `design.md` Section 7.6
  - evidence: Implemented discussion-controls loading and precedence in
    `sapi/comments/controls.py`, including canonical schema loading with safe empty fallback,
    compatibility alias normalization, and explicit precedence
    (`defaults -> per-page controls -> canonical page metadata`) with canonical-over-frontmatter
    behavior. Wired canonical metadata writeback into `scripts/create_comments.py` so legacy
    frontmatter-derived controls are written to canonical page JSON `discussion_controls` without
    mutating frontmatter fields. Added unit coverage in
    `tests/unit/comments/test_discussion_controls.py` and integration coverage in
    `tests/integration/pipelines/test_comments_pipeline.py`.

- [x] TODO-0249: Implement comment generation-isolation and adjudication summary contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223
  - scope: Implement anti-gaming generation isolation checks and adjudication summary outputs for comment runs.
  - acceptance:
    - Comment-generation prompts/context do not expose adjudication rubric internals.
    - Generation-isolation metadata uses canonical marker/schema version and leak counters.
    - Adjudication summary fields (`rubric_id`, checks, failures) are emitted in projection/run outputs.
  - notes: source `design.md` Sections 7.6, 7.7
  - evidence: Extended `scripts/create_comments.py` with explicit generation-isolation auditing
    for semantic request payloads and leak detection against adjudication-rubric terms,
    persisted canonical generation-isolation metadata (`schema_version=comment_section_generation_context_v1`)
    with leak counters into comment run outputs, and added deterministic adjudication summary
    emission (`rubric_id=comment_section_adjudication_v1`, `checks`, `failures`, `pages_with_failures`)
    to comment run metadata. Updated `CommentRunFields` in `sapi/contracts/run_envelopes.py`
    and added tests in `tests/unit/comments/test_generation_isolation_audit.py`,
    `tests/integration/pipelines/test_comments_pipeline.py`, and run-envelope contract suites.

- [x] TODO-0258: Implement rebuttal-steelman and claim-badge rendering contracts for comments
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0247
  - scope: Enforce rebuttal structure and claim-badge vocabulary rules in generated/normalized/rendered comments.
  - acceptance:
    - Rebuttal turns include strongest-opposing-point acknowledgment before rebuttal text.
    - Claim-badge status vocabulary is constrained to contract values with deterministic fallback behavior.
    - Rendering and validation tests cover badge/status consistency and rebuttal formatting.
  - notes: source `design.md` Section 7.6
  - evidence: Extended `sapi/comments/merge_normalize.py` to require rebuttal turns to carry
    `strongest_opposing_point_ack` (with compatibility alias `steelman_before_rebuttal`) and
    validate that rebuttal body text starts with the acknowledgment before additional rebuttal
    content. Added deterministic `claim_badges` normalization with status vocabulary enforcement
    (`verified|unverified|disputed`) and fallback-to-`unverified` behavior for missing/unknown
    statuses. Added coverage in `tests/unit/comments/test_turn_marker_validation.py` and
    `tests/integration/pipelines/test_comments_pipeline.py` for rebuttal formatting validation,
    claim-badge normalization consistency, and command-level failure semantics.

- [x] TODO-0247: Implement comment turn-marker normalization and turn-schema validation
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0211
  - scope: Implement canonical turn-marker handling and strict/social turn validation rules for comment rows.
  - acceptance:
    - Canonical marker `<<turn:{...}>>` is supported; legacy marker compatibility is normalized.
    - Argumentative turns enforce required claim/evidence/confidence constraints.
    - Social turns are validated under lightweight rules and rejected when they include unclassified factual claims.
  - notes: source `design.md` Section 7.6
  - evidence: Extended `sapi/comments/merge_normalize.py` to parse canonical
    `<<turn:{...}>>` and legacy `<!-- turn:{...} -->` markers, normalize marker content into
    canonical `turn` payloads, enforce strict argumentative validation
    (`claim_ids`/`evidence_refs`/`confidence`), and reject social comments that carry
    unclassified factual claim/source references without argumentative metadata. Added focused
    unit coverage in `tests/unit/comments/test_turn_marker_validation.py` and end-to-end
    pipeline coverage in `tests/integration/pipelines/test_comments_pipeline.py`, including
    command-level failure assertions with rollback-clean run-container behavior.

- [x] TODO-0223: Comment pipeline batching, merge normalization, and evidence modes
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0222, TODO-0216, TODO-0204, TODO-0218
  - scope: Implement comment generation contract including per-page semantic artifacts, count bounds, merge behavior, and evidence snapshots.
  - acceptance:
    - Default targets parseable topic pages; explicit source/claim targeting works.
    - One semantic artifact per targeted page is written under `runs/<run_id>/semantic/comment_section_generation/<page_ref_key>.json`.
    - Merge preserves existing `comment_uid` values and assigns only for new comments.
    - `web-augmented` mode writes snapshot at canonical path/schema.
  - notes: source `design.md` Section 7.6
  - evidence: Replaced `scripts/create_comments.py` scaffold with a full comment-section
    pipeline path that enforces count bounds (`5..50`), applies default parseable-topic
    targeting with explicit source/claim/topic targeting, emits one semantic artifact per
    target page under `runs/<run_id>/semantic/comment_section_generation/`, merges deterministic
    rows while preserving existing `comment_uid` values, and writes canonical web-augmented
    snapshots under `raw/snapshots/comment_sections/comment-section-<seed>.json` with schema marker
    `comment_section_evidence_snapshot_v1`. Added integration coverage in
    `tests/integration/pipelines/test_comments_pipeline.py` for all acceptance criteria and
    updated wrapper contract tests impacted by the non-stub comments execution path.

- [x] TODO-0260: Enforce MVP Slice A exit gates for first end-to-end vertical slice
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0209, TODO-0214, TODO-0216, TODO-0220, TODO-0219
  - scope: Convert MVP Slice A exit criteria into explicit checks with evidence requirements.
  - acceptance:
    - One-source end-to-end path (`create site/space -> ingest -> build -> query -> validate`) is executed and captured.
    - Semantic outputs and run-envelope requirements for ingest/query are validated against contracts.
    - Deferred-build backlog check for Slice A runs is automated and enforced.
  - notes: source `design.md` Section 12.1
  - evidence: Added `scripts/verify_slice_a.py` as a scripted local verification path that
    executes the full Slice A vertical path (create site/space, ingest, deterministic build,
    query, validate gate checks) and writes a machine-readable evidence manifest under
    `<site_path>/outputs/verification/slice_a/<verification_id>/manifest.json`. Added reusable
    gate helpers in `sapi/core/slice_a_gates.py` for ingest/query run-envelope contract checks and
    deferred-build backlog detection. Added focused coverage in
    `tests/unit/core/test_slice_a_gates.py` and
    `tests/integration/wrappers/test_verify_slice_a.py`.

- [x] TODO-0251: Preserve historical test-footprint contracts and golden asset layout
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0228
  - scope: Implement and verify historical testing-footprint expectations that should remain part of reconstruction quality signal.
  - acceptance:
    - Legacy broad `tests/test_*.py` footprint equivalents are represented in modernized test layout.
    - Golden snapshot directories for site and skill assets are created and wired to CI test commands.
    - High-value historical test intents from Section 11 are mapped to concrete tests/modules.
  - notes: source `design.md` Section 11
  - evidence: Added root-level footprint mapping test `tests/test_historical_footprint_equivalents.py`
    that preserves a broad `tests/test_*.py` entrypoint and asserts explicit mappings from
    historical high-value tests to current module coverage. Added golden snapshot assets under
    `tests/golden/site_snapshot/` and `tests/golden/skills/` plus golden validation modules
    `tests/golden/test_site_snapshot.py` and `tests/golden/test_skill_snapshot.py`. Added
    CI-target command wiring in `package.json` (`test:pr`, `test:golden`, `test:live`) and
    validated `test:golden` plus focused mapping tests.

- [x] TODO-0228: Tier 0-2 plus ingest/query Tier 3 foundational test implementation
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0204, TODO-0205, TODO-0206, TODO-0220
  - scope: Implement unit/failure tests and initial deterministic Tier 3 ingest/query integration coverage for core contracts.
  - acceptance:
    - Tier 0 harness fixtures are present.
    - Tier 1 contract tests pass including ID/time formats and semantic-flow cardinality.
    - Tier 2 rollback/failure semantics tests pass.
    - Tier 3 ingest/query integration tests pass in mock LLM mode.
  - notes: source `design.md` Section 11; `testing_plan.md` Tier 0-3
  - evidence: Added Tier 0 harness helpers in `tests/conftest.py` for isolated site/space
    bootstrap, deterministic command execution, run-frontmatter parsing, and rollback assertions.
    Added Tier 2 failure integration modules under `tests/integration/failure/`
    (`test_semantic_repair_exhaustion_rollback.py`, `test_postprocess_failure_rollback.py`,
    `test_run_container_not_persisted.py`) covering semantic retry exhaustion rollback,
    deterministic post-processing rollback, and failed-run container non-persistence in default
    mode. Added Tier 3 mock-mode pipeline integration modules under
    `tests/integration/pipelines/` (`test_ingest_pipeline.py`, `test_query_pipeline_outputs.py`)
    covering ingest canonical writes + run/lint envelopes and query output-mode manifest
    contracts. Verified Tier 1/Tier 2/Tier 3 criteria with targeted unittest runs.

- [x] TODO-0233: Implement UI information architecture and rendering contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0253
  - scope: Integrate and validate UI/IA renderer contracts end-to-end after specialized Section 8 tasks land.
  - acceptance:
    - Section 8 specialized contract tasks produce coherent, non-conflicting site output across page types.
    - Cross-page navigation/search/feed behavior is consistent after integrating all specialized renderers.
    - Final integration pass closes known UI contract gaps and regressions with snapshot evidence.
  - notes: source `design.md` Section 8
  - evidence: Extended `sapi/build/site_builder.py` with a deterministic space search index page
    (`site/search/index.html`) that indexes sources/topics/runs and wired a single consistent
    cross-page search control (`/spaces/<space_name>/site/search/index.html?q=...`) into the
    shared space layout. Added integration assertions in
    `tests/unit/build/test_site_builder_contracts.py` validating search-control consistency
    across page types, indexed page/run coverage, and deterministic full snapshot stability across
    repeated builds.

- [x] TODO-0234: Implement topic lifecycle transitions and final-page contradiction gating
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216, TODO-0218
  - scope: Implement lifecycle state transitions and contradiction handling gates for topic publication.
  - acceptance:
    - Lifecycle states/transitions match contract including manual-only finalization/demotion paths.
    - `final_disputed_contradiction` blocks publication workflows without auto-demoting final pages.
    - Manual remediation flow via lifecycle command is supported and auditable.
  - notes: source `design.md` Sections 5.8, 10
  - evidence: Added topic lifecycle resolution in `sapi/build/topic_lifecycle.py` and
    integrated it into deterministic projection loading via `sapi/build/projection.py`, including
    automatic `draft -> stable` and `stable -> draft` transitions while preserving non-auto-demoted
    `final` pages. Added publication-gating enforcement for
    `final_disputed_contradiction` in `scripts/build_site.py`. Implemented manual lifecycle
    remediation command `scripts/set_topic_lifecycle.py` with auditable lifecycle transition
    entries and finalization metadata updates. Added acceptance coverage in
    `tests/unit/build/test_topic_lifecycle_contracts.py` for transition semantics, publication
    blocking behavior, and auditable manual remediation flows.

- [x] TODO-0257: Implement source-preview asset pipeline and page/feed integration
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0210, TODO-0216, TODO-0253
  - scope: Implement deterministic source-preview asset generation and integration into source/detail/feed views.
  - acceptance:
    - Source preview assets are generated under canonical site asset path with deterministic naming.
    - Source detail and optional feed-row integrations render preview assets per contract.
    - Preview generation/integration is deterministic and covered by snapshot tests.
  - notes: source `design.md` Section 8 (historical source preview assets)
  - evidence: Added deterministic source-preview asset generation to
    `sapi/build/site_builder.py`, writing canonical assets at
    `site/assets/source_previews/<source_id>.svg` during site-root refresh. Integrated preview
    rendering into source detail pages (summary + preview image linked to canonical source-file
    path when present) and feed rows (`site/new` and space `new` tab) via compact preview
    thumbnails. Extended `tests/unit/build/test_site_builder_contracts.py` with acceptance tests
    for canonical preview-asset path/naming, source/detail/feed integration, and deterministic
    snapshot equivalence across repeated builds.

- [x] TODO-0253: Implement navigation/tabs/feed/pagination information-architecture contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216
  - scope: Implement deterministic navigation/sidebar/tab/feed/search/pagination behavior and scope-aware users tab behavior.
  - acceptance:
    - Sidebar hierarchy, space switcher, tab set, and page-size behavior match contract.
    - Feed ordering, tie-break rules, and pagination URL semantics are deterministic.
    - Users-tab scope behavior (site vs space) and space-scoped profile link resolution are implemented.
  - notes: source `design.md` Section 8
  - evidence: Extended `sapi/build/site_builder.py` to implement Section 8 IA contracts with
    deterministic sidebar hierarchy and persistent space switcher, canonical tab set (`New`,
    `Sources`, `Topics`, `Users`, optional `Runs`), fixed `TAB_PAGE_SIZE = 50` tab pagination,
    deterministic site-root `New` feed ordering with explicit tie-breaks and feed-vs-tab pagination
    URL semantics (`feed_page` vs `tab_page`), site-root spaces/subspaces listing, and site/space
    users-tab rendering with space-scoped persona profile links at
    `spaces/<space>/site/users/persona-<persona_id>.html`. Added acceptance coverage in
    `tests/unit/build/test_site_builder_contracts.py` for navigation/tabs/page-size contracts,
    deterministic feed ordering + pagination semantics, and users-tab scope/profile-link resolution.

- [x] TODO-0252: Implement topic-page structure renderers (`wiki` and `source_mirror`)
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0212, TODO-0216
  - scope: Implement deterministic topic renderer selection and section rendering contracts for both topic structures.
  - acceptance:
    - Renderer selection between `wiki` and `source_mirror` is deterministic from topic metadata.
    - Required section ordering and content expectations are enforced for both structures.
    - Source-mirror pages preserve structural correspondence without becoming verbatim restatements.
  - notes: source `design.md` Section 8
  - evidence: Implemented structure-specific topic rendering in `sapi/build/site_builder.py` with
    deterministic renderer selection (`wiki`/`source_mirror`) from topic metadata, wiki preferred
    section ordering, source-mirror outline-aware ordering, and explicit rejection of verbatim
    heading-as-body mirror sections. Added deterministic build tests in
    `tests/unit/build/test_site_builder_contracts.py` covering renderer selection, enforced wiki
    ordering, source-mirror ordering from `source_structure_outline`, and non-verbatim content guard.

- [x] TODO-0244: Implement claim-reference rendering/public-debug visibility contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216
  - scope: Implement claim annotation rendering behavior with auditability and metadata visibility modes.
  - acceptance:
    - HTML view avoids always-visible raw claim IDs in sentence text while preserving clickable audit access.
    - JS-off fallback includes minimal static claim-details links.
    - Public mode hides internal IDs/paths/hashes; debug mode exposes internal metadata as configured.
  - notes: source `design.md` Section 8
  - evidence: Added deterministic claim-annotation rendering in `sapi/build/site_builder.py` so
    inline `[[claims:...]]` markers are removed from sentence text while claim details remain
    clickable/auditable via section-scoped details links and JS-off `<noscript>` fallback links.
    Wired `--site-presentation-mode {public,debug}` through `scripts/build_site.py` and
    `regenerate_web.sh`, with debug-mode metadata exposure and public-mode suppression of
    debug-only claim metadata. Expanded `tests/unit/build/test_site_builder_contracts.py` and
    `tests/unit/contracts/test_regenerate_web_wrapper_contract.py` to cover all acceptance clauses.

- [x] TODO-0245: Implement cross-space pinned-link import contract and error rendering
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216, TODO-0218
  - scope: Implement cross-space topic linking via pinned imports with deterministic unresolved-link behavior.
  - acceptance:
    - Pinned parent links resolve through `imports.lock.md` snapshot entries only.
    - Unresolved pinned parent links render disabled markers and emit lint `error`.
    - Parent linkage metadata (`parent_space_name`, `parent_snapshot`, `parent_site_base_url`) persists as required.
  - notes: source `design.md` Section 8
  - evidence: Added pinned-parent import resolution in `sapi/build/projection.py` using `imports.lock.md`
    snapshot entries only, with unresolved pins materialized as lint issues (`unresolved_pinned_parent_link`)
    instead of hard build failures. Updated `sapi/build/site_builder.py` and `scripts/build_site.py` to render
    resolved/unresolved parent markers deterministically and emit lint errors in build output/manifest. Extended
    `tests/unit/build/test_site_builder_contracts.py` with coverage for lock-only resolution, unresolved disabled
    marker rendering, lint-error emission, and persisted parent-link metadata.

- [x] TODO-0274: Integrate `evaluate_source.sh` comments mode and comment-review artifacts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0273, TODO-0223, TODO-0247
  - scope: Add full comments integration to the user-facing evaluation harness so reviewers can inspect generated discussion quality in markdown artifacts.
  - acceptance:
    - `evaluate_source.sh --comments <n>` invokes comment generation with canonical flags and records effective targets/counts.
    - Evaluation artifact folder includes `comments_review.md` with per-page/per-user counts and representative thread excerpts.
    - Harness preserves deterministic output layout and fails fast on invalid comments-mode arguments.
  - evidence: Extended `scripts/evaluate_source.py` comments-mode handling to compute and persist
    deterministic effective targets/counts in both `comments_review.md` and `manifest.json`
    (`comments` block with effective targets/distributions), while retaining canonical
    `create_comments.py` invocation flags (`--count`, `--comment-user`, `--comment-page`) and
    fail-fast invalid `--comments` argument behavior. Expanded
    `tests/integration/wrappers/test_evaluate_source_harness.py` to assert canonical comments
    command flags in `README.md`, manifest effective-target/count linkage, and per-page/per-user
    count rows plus representative excerpt sections in `comments_review.md`.

- [x] TODO-0267: Implement wrapper compatibility and bootstrap-exception integration tests
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0209, TODO-0235, TODO-0219, TODO-0228
  - scope: Add dedicated wrapper integration tests for alias normalization/conflicts and bootstrap registry-path exceptions.
  - acceptance:
    - Wrapper test modules cover alias normalization and canonical+alias conflict failures.
    - Bootstrap wrappers are explicitly tested for allowed missing operator-supplied `--registry-path`.
    - Non-bootstrap wrappers are tested to require explicit/effective registry-path routing.
  - evidence: Added dedicated integration modules under `tests/integration/wrappers/`:
    `test_wrapper_alias_normalization.py` (alias normalization + deprecation coverage),
    `test_wrapper_alias_conflicts.py` (canonical+alias conflict fail-fast coverage), and
    `test_bootstrap_registry_exception.py` (bootstrap exception and non-bootstrap
    explicit/effective registry-path routing coverage via script-failure + wrapper-success checks).

- [x] TODO-0268: Implement `regenerate_web.sh` wrapper-to-build entrypoint contract
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0209, TODO-0216, TODO-0235
  - scope: Implement and validate `regenerate_web.sh` behavior as the canonical wrapper for deterministic site build/projection entrypoints.
  - acceptance:
    - `regenerate_web.sh` dispatches to the intended build entrypoint/workflow key with explicit `--registry-path` handling for non-bootstrap execution.
    - Wrapper argument normalization and conflict handling match wrapper contract rules.
    - End-to-end wrapper invocation produces deterministic build outputs without semantic-flow execution.
  - evidence: Added deterministic wrapper integration coverage in
    `tests/integration/wrappers/test_regenerate_web_wrapper_contract.py` verifying wrapper-managed
    registry-path dispatch to `scripts/build_site.py` with workflow key `build_site`, explicit
    conflict rejection when `--registry-path` override is supplied, and deterministic repeated
    wrapper execution producing identical `outputs/build_site/manifest.json` with
    `semantic_flows_executed: []`.

- [x] TODO-0276: Add deterministic mechanical integration tests for `evaluate_source.sh` harness
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0273
  - scope: Verify the user-facing evaluation harness contract in CI with deterministic mock-LLM runs so regressions are caught mechanically.
  - acceptance:
    - Integration test module `tests/integration/wrappers/test_evaluate_source_harness.py` validates default artifact-pack layout and required markdown outputs.
    - Tests assert `manifest.json` linkage to emitted markdown artifacts and referenced run IDs.
    - Tests cover `--comments <n>` mode and invalid comments arguments fail-fast behavior without partially committed evaluation packs.
  - evidence: Hardened `tests/integration/wrappers/test_evaluate_source_harness.py` with
    deterministic assertions for required markdown artifact content keys (README/summary/ingest/lint/site-links/strict query),
    explicit `manifest.json` linkage checks for all emitted markdown artifacts and referenced ingest
    run IDs, comments-mode assertions for `comments_review.md` structural sections, and fail-fast
    invalid comments argument behavior without partial evaluation-pack writes.

- [x] TODO-0273: Implement `evaluate_source.sh` user-facing evaluation harness (markdown-first artifact pack)
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0200, TODO-0210, TODO-0216, TODO-0219, TODO-0220
  - scope: Implement a single operator command that runs source evaluation and emits a human-readable artifact folder for manual quality review.
  - acceptance:
    - Wrapper/entrypoint pair exists (`evaluate_source.sh` -> `scripts/evaluate_source.py`) with explicit `--registry-path` routing.
    - Default artifact pack includes `README.md`, `summary.md`, `ingest_run.md`, `lint_summary.md`, `site_links.md`, and `query_answers/strict.md`.
    - Companion machine-readable `manifest.json` indexes produced artifacts and referenced run IDs.
    - Artifact output defaults to `<space_root>/outputs/evaluations/<evaluation_id>/` and supports `--out` override.
  - evidence: Replaced the evaluate harness scaffold with a working orchestration in
    `scripts/evaluate_source.py` that executes ingest + validation + strict query (+ optional
    comments), writes the required markdown-first artifact pack, emits `manifest.json` with run/artifact
    linkage, and defaults output to `<space_root>/outputs/evaluations/<evaluation_id>/` with `--out`
    override support. Added deterministic integration coverage in
    `tests/integration/wrappers/test_evaluate_source_harness.py` for default artifact-pack output,
    `--out` + `--comments <n>` behavior, and invalid comments argument fail-fast behavior.

- [x] TODO-0246: Implement chained-flow coalescing and trigger-equivalence checks
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0211, TODO-0212, TODO-0216
  - scope: Implement optional ingest+topic post-processing coalescing with strict equivalence to independent trigger behavior.
  - acceptance:
    - Ingest/topic chained execution may coalesce deterministic post-processing into one final pass.
    - Coalesced output is equivalent to independent post-processing execution.
    - Tests cover trigger policy and equivalence behavior.
  - evidence: Introduced explicit coalesced ingest/topic post-processing helper in
    `scripts/ingest_source.py` (`_run_coalesced_ingest_topic_postprocess`) and routed chained
    ingest/topic executions through that single final deterministic pass; expanded
    `tests/unit/ingest/test_topic_generation_flow.py` with
    `test_chained_ingest_topic_flow_coalesces_to_one_postprocess_pass` (asserting one coalesced
    deterministic pass) and `test_coalesced_output_matches_independent_follow_up_build` (proving
    output equivalence against an independent follow-up `scripts/build_site.py` execution).

- [x] TODO-0219: `validate.sh` workflow dispatch and lint-engine integration
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0218, TODO-0235
  - scope: Implement workflow-aware lint entrypoint dispatch from `validate.sh` to `scripts/lint.py`.
  - acceptance:
    - `validate.sh` accepts `--workflow` and optional `--run-id`.
    - Selected workflow key maps to gating behavior from Section 5.8.
    - Command exits and envelopes reflect lint-engine outcomes consistently.
  - evidence: Implemented workflow-dispatch lint entrypoint behavior in `scripts/lint.py`
    (workflow/run-id selection, warning-budget parsing, run lint artifact loading, workflow-key gate
    evaluation, and deterministic JSON lint-gate envelope output/exit codes) backed by
    `sapi/lint/lint_engine.py`; added focused dispatch coverage in
    `tests/unit/lint/test_validate_workflow_dispatch.py`; and retained/verified guardrail + checklist
    gate integration through `tests/unit/lint/test_guardrail_checks.py` and
    `tests/unit/lint/test_pipeline_pr_checklist_gate.py`.

- [x] TODO-0218: Lint severity engine and warning-threshold status mapping
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0206
  - scope: Implement lint severities, workflow-specific gate behavior, warning-threshold status mapping, and lint artifact writes.
  - acceptance:
    - Severity levels and example checks are enforced (`error/warning/info`).
    - Gate behavior matches workflow key table.
    - `lint.json` and `## Lint Summary` are emitted for committed runs.
  - evidence: Implemented canonical lint severity/check mapping and gate evaluation in
    `sapi/lint/severity.py` and `sapi/lint/lint_engine.py` (including warning-budget parsing,
    workflow-key gate policy, and lint artifact writer); wired committed-run lint artifact emission
    into `sapi/core/pipeline_policy.py`; added tests in
    `tests/unit/lint/test_warning_budget_gate.py` for severity/gate contracts and warning-budget
    validation; and extended `tests/unit/core/test_pipeline_policy.py` plus
    `tests/unit/ingest/test_topic_generation_flow.py` to assert committed runs emit both
    `runs/<run_id>/lint.json` and `run.md` `## Lint Summary`.

- [x] TODO-0217: Site-root `New` feed refresh policy and incremental/full equivalence
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0216, TODO-0211, TODO-0212
  - scope: Implement ingest/topic-driven site-root refresh semantics and equivalence checks for full vs incremental updates.
  - acceptance:
    - Ingest/topic updates refresh site-root `New` for same site.
    - Incremental output is equivalent to deterministic full rebuild.
  - evidence: Added explicit incremental build mode plumbing in `scripts/build_site.py` and
    deterministic incremental-write behavior in `sapi/build/site_builder.py` for both space pages
    and site-root `site/new/index.html`; expanded `tests/unit/ingest/test_topic_generation_flow.py`
    to assert ingest/topic runs refresh site-root `New` content; and added
    `tests/unit/build/test_site_builder_contracts.py::test_incremental_build_output_is_equivalent_to_full_rebuild`
    to verify incremental HTML output equivalence with full deterministic rebuild output.

- [x] TODO-0216: Deterministic projection/site builder and frontend toolchain reproducibility
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 3
  - depends_on: TODO-0210, TODO-0212, TODO-0208
  - scope: Implement deterministic HTML renderer, Tailwind build integration, and strict Node/package-manager reproducibility rules.
  - acceptance:
    - Build consumes canonical JSON only and never invokes LLM.
    - Build fails on unresolved template/link/conversion errors.
    - `package.json`, single lockfile, Node pin, and frozen install mode are enforced.
  - evidence: Implemented canonical-JSON projection + deterministic HTML build pipeline in
    `sapi/build/projection.py`, `sapi/build/site_builder.py`, and `scripts/build_site.py`,
    including hard-fail validation for unresolved topic source links and malformed template/section
    payloads; added frontend-toolchain reproducibility enforcement (declared `packageManager`,
    single lockfile, node pin, and package-manager-specific frozen install command) with
    build-manifest toolchain metadata; updated `package.json` to declare package-manager family;
    and added `tests/unit/build/test_site_builder_contracts.py` plus wrapper contract adjustments
    in `tests/unit/contracts/test_regenerate_web_wrapper_contract.py` proving deterministic output
    and acceptance-criteria failure modes.

- [x] TODO-0271: Enforce ingest comment-enrichment boundary contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0214, TODO-0211
  - scope: Ensure ingest does not implicitly trigger comment generation and preserves explicit pipeline boundaries for comment enrichment.
  - acceptance:
    - Default ingest path invokes only ingest/topic semantic flows and never `comment_section_generation`.
    - Any optional enrichment path requires explicit operator opt-in and preserves Section 7.6 comment pipeline contracts.
    - Run metadata/tests verify `semantic_flows`/invocation counts remain boundary-correct for ingest modes.
  - evidence: Enforced ingest boundary preflight in `scripts/ingest_source.py` via
    `plan_ingest_semantic_execution` so inline comment parameters require explicit opt-in, contract
    bounds/target validation are applied, and inline enrichment attempts fail fast with an explicit
    follow-up workflow requirement (`create_comments.sh`). Added CLI-mode tests in
    `tests/unit/ingest/test_ingest_mode_handling.py` covering default/source-only boundary metadata,
    opt-in requirement enforcement, contract-bound validation (`count` range and target scope), and
    non-mutating failure behavior before ingest writes.

- [x] TODO-0270: Enforce ingest date/title resolution and strict-date mode contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210, TODO-0211, TODO-0214
  - scope: Implement and validate recovered ingest date/title policies, warning semantics, and strict-date behavior.
  - acceptance:
    - Source title resolution follows the five-step priority contract exactly.
    - Missing publication date behavior emits `missing_publication_date` warning and persists compliant `source_date_inference` fields.
    - `--require-source-date` strict mode fails ingest when publication date cannot be resolved.
  - evidence: Wired strict-date/date-resolution policy in `scripts/ingest_source.py` using `resolve_publication_date` with new `--require-source-date`, persisted normalized publication date + compliant `source_date_inference`/`missing_publication_date` warnings via ingest extraction output, extended source-title hint extraction and five-step priority wiring in `sapi/ingest/records_writer.py`, and added contract tests in `tests/unit/ingest/test_source_acquisition.py` and `tests/unit/ingest/test_ingest_mode_handling.py` for title-priority ordering, missing-date warning persistence, and strict-date failure behavior.

- [x] TODO-0278: Enforce relation-type matrix semantics and normalization invariants
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0211, TODO-0213
  - scope: Implement relation semantics beyond storage-key hashing, including type-specific canonical ID formation and normalization rules.
  - acceptance:
    - Relation ID generation follows the canonical matrix for directed/undirected relation types.
    - Undirected relations sort claim IDs lexicographically; directed relations preserve semantic source/target order.
    - Canonical relation-write normalization includes required status/field handling and deterministic merge behavior for duplicate relation IDs.
  - evidence: Hardened duplicate relation merge normalization in `sapi/ingest/relation_store.py` so omitted incoming status/confidence-band fields no longer overwrite explicit existing values, while keeping canonical relation ID/hash mapping and matrix semantics intact; expanded `tests/unit/ingest/test_relation_store_matrix.py` with explicit `falsify/not_falsify/ambiguous` status handling and deterministic duplicate-merge preservation checks.

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

- [x] TODO-0212: Topic generation semantic flow and canonical topic persistence
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0211, TODO-0203, TODO-0204
  - scope: Implement topic semantic generation and canonical topic artifact writes including structure-type support.
  - acceptance:
    - Topic flow resolves spec/schema from authoritative map.
    - Canonical topic JSON writes to `topics/<topic_id>.json`.
    - Deterministic post-processing/build triggers run per policy.
  - evidence: Implemented canonical topic-generation flow in `sapi/ingest/topic_generator.py` using
    generation-spec flow-map resolution and strict semantic validation, integrated topic generation +
    deterministic `build_site` trigger into `scripts/ingest_source.py`, and validated behavior with
    `tests/unit/ingest/test_topic_generation_flow.py` (spec/schema resolution assertions, canonical
    `topics/<topic_id>.json` persistence, and deterministic build-manifest emission).

- [x] TODO-0214: Ingest mode handling (`--source-only`, `--force`, deferred build)
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210, TODO-0211, TODO-0212, TODO-0205
  - scope: Implement ingest mode-specific behavior for skipping semantic flows, rollback overrides, and bootstrap deferred-build metadata.
  - acceptance:
    - `--source-only` skips semantic generation, normalizes compatibility alias `--query-only`, and writes empty semantic-flow metadata accordingly.
    - `--force` may preserve failed invocation artifacts and writes `force_mode/rollback_skipped`.
    - Deferred-build runs include required metadata and are trackable for backfill.
  - evidence: Extended `scripts/ingest_source.py` to normalize script-level `--query-only` aliasing,
    persist ingest run metadata with empty semantic-flow fields for source-only mode, write
    force-mode failure run metadata (`force_mode=true`, `rollback_skipped=true`) when rollback is
    intentionally skipped, and support bootstrap deferred-build runs with
    `build_deferred/deferred_build_reason` tracking; validated by
    `tests/unit/ingest/test_ingest_mode_handling.py` and companion regressions in
    `tests/unit/contracts/test_wrapper_alias_normalization.py` and
    `tests/unit/ingest/test_topic_generation_flow.py`.

- [x] TODO-0215: Reference extraction, structured normalization, and local link backfill
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 2
  - depends_on: TODO-0210
  - scope: Implement reference extraction and matching pipeline for reference-heavy sources.
  - acceptance:
    - References normalize to structured rows.
    - Local source matching in same space persists `linked_source_ids`.
    - Backfill links runs for older records after new ingest.
  - evidence: Replaced `sapi/ingest/citations.py` stub with deterministic reference extraction,
    structured row normalization (`title/authors/year/doi/arxiv/url`), same-space source matching,
    and older-record backfill of `linked_source_ids`; integrated the flow into
    `scripts/ingest_source.py` for every ingest run, and validated contracts via
    `tests/unit/ingest/test_reference_linking.py` (structured rows, local matching persistence,
    and backfill behavior on new ingest).

- [x] TODO-0243: Track reconstruction-plan phase/slice progress explicitly
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0102
  - scope: Add a lightweight phase/slice tracker so each backlog item maps to MVP Slice A/B and
    Phase 1-6 progress checkpoints.
  - acceptance:
    - Progress tracker includes MVP Slice A/B and Phase 1-6 checkpoints.
    - Each phase has explicit entry/exit criteria tied to TODO IDs.
    - Deferred-build backlog and phase-gate blockers are visible in one place.
  - evidence: Added `docs/reconstruction_tracker.md` with explicit MVP Slice A/B entry/exit gates,
    Phase 1-6 entry/exit checkpoint mapping to TODO IDs, a dedicated deferred-build backlog section
    (`build_deferred: true` policy checkpoint), and consolidated phase-gate blockers. Added
    `tests/unit/contracts/test_reconstruction_tracker.py` to enforce tracker presence, phase/slice
    coverage, TODO-linked entry/exit criteria for each phase, and visible deferred-build/backlog
    blocker sections in one document.

- [x] TODO-0222: Repository-seeded persona catalog loading and validation
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 5
  - depends_on: TODO-0201, TODO-0209
  - scope: Implement strict loading/validation for shared persona catalog and profile image
    resolution.
  - acceptance:
    - Loader reads only `<repo_root>/personas/social_users.json`.
    - `persona_id` normalization and alias validation rules are enforced.
    - Profile image paths resolve at runtime; invalid rows fail fast.
  - evidence: Added `sapi/profiles/persona_catalog.py` with canonical-path-first catalog loading
    (`personas/social_users.json`), persona alias normalization (`id` -> `persona_id`) with mismatch
    rejection, duplicate/slug validation, and runtime profile-image path enforcement under
    `personas/profile_images/`. Wired
    `scripts/generate_profiles.py` to run catalog preflight validation before execution and reject
    unknown `--persona-id` values. Added `tests/unit/profiles/test_persona_catalog_loader.py` with
    explicit acceptance-criteria coverage for canonical loading behavior, alias normalization/mismatch
    rejection, persona-id invariants, and profile-image path resolution failures.

- [x] TODO-0220: Query pipeline core contracts and preflight rules
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0204, TODO-0206, TODO-0207, TODO-0213
  - scope: Implement query semantic flow, retrieval contracts, strict/non-strict mode behavior, and
    rollback semantics.
  - acceptance:
    - Mode validation rejects explicit `strict + include-disputed`.
    - Query writes only under `outputs/query/<query_id>/...` plus run/lint metadata.
    - Query never mutates canonical knowledge artifacts or triggers site rebuild.
    - Terminal query failures rollback invocation-scoped query outputs and run/lint artifacts.
  - evidence: Replaced `scripts/query.py` scaffold with a query pipeline implementation that enforces
    strict-mode preflight (`--mode strict --include-disputed` fails before retrieval), resolves
    deterministic mode defaults, writes query artifacts only under
    `<space_root>/outputs/query/<query_id>/` (`query.json` and `answer.md`), emits canonical
    `query_pipeline` run/lint metadata via shared pipeline policy, and applies default terminal
    rollback using invocation-scoped artifact transactions. Added deterministic retrieval helper in
    `sapi/query/retrieval.py` and acceptance tests in
    `tests/unit/query/test_query_pipeline_core_contract.py` covering preflight failure behavior,
    query-write path boundaries/no site rebuild mutation, and rollback cleanup on simulated terminal
    failure.

- [x] TODO-0259: Implement query mode defaults and retrieval-budget policy contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220
  - scope: Implement recovered mode defaults and retrieval-budget policy behavior for
    strict/exploratory/comparative query execution.
  - acceptance:
    - Mode defaults for `include_disputed` are implemented exactly by mode.
    - `include_warnings` defaults to `true` unless explicitly overridden and is reflected in output
      metadata.
    - Retrieval budget defaults and override behavior are deterministic and auditable in outputs.
    - Invalid mode/flag combinations fail fast before retrieval/generation.
  - evidence: Extended `scripts/query.py` mode policy metadata to include effective
    `execution.retrieval_budget` (`max_claims`, `max_sources`) alongside effective
    `include_disputed`/`include_warnings` flags. Added
    `tests/unit/query/test_query_mode_defaults_policy.py` to validate strict/exploratory/comparative
    include-disputed defaults, include-warnings default/override reflection in query JSON metadata,
    deterministic budget defaults/overrides with auditable retrieval counts and truncation fields,
    and fail-fast invalid `strict + include-disputed` behavior before retrieval/generation writes.

- [x] TODO-0221: Query artifact modes and deterministic manifest assembly
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220
  - scope: Implement deterministic non-markdown query output modes and manifest generation without extra LLM steps.
  - acceptance:
    - `mermaid/images/slides/pdf` modes emit canonical `manifest.json`.
    - `markdown` mode emits no manifest and keeps `manifest_path` null/omitted.
    - Manifest keys and artifact hash contracts match doc requirements.
  - evidence: Added deterministic query artifact assembly in `sapi/query/renderers.py` for
    `mermaid/images/slides/pdf` output modes with canonical manifest payload fields and
    `artifact_hashes` computed from emitted artifact contents. Extended `scripts/query.py` to
    support non-markdown output modes, write manifest/artifact files under
    `<space_root>/outputs/query/<query_id>/`, and enforce `query.json` `manifest_path` parity with
    canonical `manifest.json` while preserving markdown mode behavior (`manifest_path` null and no
    manifest file). Added `tests/unit/query/test_query_artifact_modes_contract.py` to verify
    non-markdown manifest emission, markdown no-manifest behavior, required manifest keys, declared
    hash integrity against actual artifact bytes, and mode-specific artifact row fields.

- [x] TODO-0255: Implement query citation-coverage and deterministic truncation policies
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220, TODO-0213
  - scope: Enforce mode-specific citation coverage targets and deterministic truncation/tie-break
    behavior in query outputs.
  - acceptance:
    - Coverage policies for `strict`, `exploratory`, and `comparative` modes are implemented and
      auditable.
    - Truncation order and tie-break behavior are deterministic and consistent with contracts.
    - `omitted_due_to_budget` is populated whenever truncation occurs.
  - evidence: Updated `scripts/query.py` to emit auditable citation coverage metadata including
    mode-specific thresholds (`strict=0.9`, non-strict=0.7), policy version, cited counts, and
    pass/fail evaluation. Updated `sapi/query/retrieval.py` to enforce deterministic truncation
    ordering by retrieval rank (descending) with lexical canonical ID tie-breaks, then budget
    slicing and omitted-count tracking. Added
    `tests/unit/query/test_query_citation_truncation_policy.py` to verify mode-specific citation
    coverage policy fields and deterministic rank/tie-break truncation with non-zero
    `omitted_due_to_budget` when budgets truncate results.

- [x] TODO-0277: Enforce query result JSON shape and execution-metadata contracts
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0220, TODO-0221, TODO-0255, TODO-0259
  - scope: Implement and validate full recovered query result-shape contract including execution,
    warnings, and optional fields.
  - acceptance:
    - Query JSON includes required high-signal keys (`query_id`, `answer`,
      retrieval/falsification counters, mode/scope, run/timestamp, lint/execution blocks).
    - Optional fields (`ancestor_pages_used`, `inherited_conflicts`, `synthesis_claim_ids`)
      follow deterministic presence/absence rules.
    - `manifest_path` behavior is consistent with output format contract and validated by tests.
  - evidence: Tightened query-shape validation in `sapi/query/query_pipeline.py` to enforce RFC3339
    UTC `query_timestamp_utc`, required retrieval/omission counter keys, required lint-summary keys,
    and required execution metadata keys with type checks. Expanded
    `tests/unit/query/test_query_result_shape_contract.py` with negative cases for missing execution
    and lint keys, invalid timestamp format, and missing required counter keys. Expanded
    `tests/unit/query/test_query_pipeline_core_contract.py` to assert required high-signal keys and
    required execution/lint/retrieval subkeys in pipeline-produced `query.json`. Existing
    manifest-path and optional-field contract tests remain green in
    `tests/unit/query/test_query_result_shape_contract.py` and
    `tests/unit/query/test_query_artifact_modes_contract.py`.

- [x] TODO-0242: Enforce ingest/query capability ownership boundaries
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 4
  - depends_on: TODO-0201, TODO-0211, TODO-0220
  - scope: Encode capability boundaries so ingest owns canonical mutations and query remains
    read/synthesize-only.
  - acceptance:
    - Ingest-owned components are the only paths that mutate canonical
      `sources/claims/relations/topics/profiles`.
    - Query pipeline cannot write canonical knowledge artifacts by contract and tests.
    - Boundary violations fail CI through contract tests/static checks.
  - evidence: Added a canonical-mutation ownership guardrail in `sapi/lint/guardrails.py` that
    flags non-ingest code paths writing canonical space artifacts (`sources/claims/relations/topics/
    profiles`) while allowing ingest-owned write paths (`sapi/ingest/`, `scripts/ingest_source.py`).
    Expanded `tests/unit/lint/test_guardrail_checks.py` to prove ownership violations fail guardrails,
    ingest-owned canonical writes are allowed, and query canonical mutation patterns remain blocked.
    Query non-mutation behavior remains enforced by
    `tests/unit/query/test_query_pipeline_core_contract.py`, and guardrail failures are enforced by
    the lint entrypoint (`scripts/lint.py`) during validation gates.

- [x] TODO-0227: Runtime safety guards for cleanup and file operations
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0205
  - scope: Implement destructive-operation safeguards and path restrictions in all cleanup and
    rollback paths.
  - acceptance:
    - Cleanup blocks dangerous roots (`/`, home, repo root, empty).
    - Deletion stays within explicit staging/temp roots.
    - Safety behavior has dedicated tests for reject cases.
  - evidence: Hardened rollback/cleanup safety in `sapi/core/transactions.py` by adding guarded
    delete validation that rejects dangerous cleanup targets (filesystem root, home, repo root,
    empty/current directory) and allows deletion only for explicit transaction/run cleanup targets.
    Wired the safe-delete checks through rollback, commit backup cleanup, restore-from-backup, and
    terminal-failure run-container removal paths. Added reject-case tests in
    `tests/unit/core/test_transactions.py` for home/repo-root cleanup targets and kept rollback
    coverage green for canonical/derived/run artifacts under explicit temporary roots.

- [x] TODO-0226: Observability and LLM trace artifact pipeline
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0204, TODO-0209
  - scope: Implement verbose mode behavior, trace-dir output, and trace artifact persistence for all semantic calls.
  - acceptance:
    - `--verbose` prints prompt, stream output, and trace dir early.
    - Trace artifacts are written under `<site_path>/outputs/llm_traces/...`.
    - Trace file set includes prompt/context/response/meta files per contract.
  - evidence: Implemented concrete per-attempt trace persistence in `sapi/llm/trace.py` and
    extended `sapi/llm/semantic_executor.py` to emit trace lifecycle hooks before/after each
    semantic attempt, including request/raw response payload capture and metadata validation
    outcomes. Wired verbose trace context through ingest semantic calls in
    `scripts/ingest_source.py`, `sapi/ingest/records_writer.py`, and `sapi/ingest/topic_generator.py`
    so trace directories are announced early and prompt/stream output is printed in verbose mode.
    Added deterministic tests in `tests/unit/semantic/test_llm_trace_artifacts.py` and
    `tests/unit/ingest/test_ingest_mode_handling.py` to assert canonical site-root trace paths,
    required trace file sets, and verbose output ordering/visibility.

- [x] TODO-0282: Resolve compatibility-reader sunset policy into a concrete contract update
  - owner: human
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Cross-cutting
  - depends_on: TODO-0280
  - scope: Resolve the unresolved compatibility-reader sunset recommendation into an explicit policy decision and update the canonical contract destination section.
  - acceptance:
    - Decision outcome is recorded in `design.md` decision register with resolved status and final contract location.
    - Contract update lands in `design.md` Section 4.1.3 with explicit compatibility-reader sunset policy and enforcement boundaries.
    - Any affected TODO dependencies/docs coverage references are synchronized.
  - evidence: Updated `design.md` decision register entry for compatibility-reader sunset policy to
    `resolved` in Section 1.3 with final contract location set to Section 4.1.3, and added explicit normative
    Section 4.1.3 policy text defining scope boundaries (read/import/CLI compatibility only), write
    boundary requirements (canonical names only), and phased enforcement behavior across
    reconstruction and post-reconstruction phases. Synchronized open-backlog references in
    `docs/todo.md` by removing `TODO-0282` from open tasks, ready/backlog queues, and coverage
    snapshot mapping.

- [x] TODO-0254: Implement runtime-flag surface parity and validation across wrappers/entrypoints
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-12
  - phase: Phase 6
  - depends_on: TODO-0235, TODO-0226, TODO-0240
  - scope: Ensure high-signal runtime/control flags are exposed consistently, validated, and forwarded from wrappers to entrypoints.
  - acceptance:
    - Wrapper flag surface includes required runtime/tracing/testing controls with consistent behavior.
    - Invalid/unsupported flag combinations fail fast with clear errors.
    - Runtime defaults and forwarding behavior are documented and tested end-to-end.
  - evidence: Added shared runtime/control flag contract wiring in `sapi/core/runtime_flags.py`
    and integrated it into semantic entrypoints (`scripts/ingest_source.py`, `scripts/query.py`,
    `scripts/create_comments.py`, `scripts/generate_profiles.py`, `scripts/evaluate_source.py`)
    so high-signal runtime/tracing/testing flags are parsed with consistent defaults and validation.
    Added wrapper forwarding support for value-bearing runtime flags in `create_comments.sh`.
    Documented defaults and forwarding/validation expectations in `README.md`. Added tests for
    parser surface/defaults and invalid trace-dir combination failures in
    `tests/unit/contracts/test_runtime_flag_surface.py`, wrapper forwarding/fast-fail integration
    coverage in `tests/integration/wrappers/test_wrapper_runtime_flags.py`, and end-to-end
    evaluate harness forwarding assertions in
    `tests/integration/wrappers/test_evaluate_source_harness.py`.

## 2026-04-13

- [x] TODO-0224: Persona profile generation and space-local accountability history
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0222, TODO-0223, TODO-0216
  - scope: Implement profile semantic flow, canonical profile writes, and history update semantics per space.
  - acceptance:
    - Profiles write to `profiles/persona-<persona_id>.json`.
    - History writes to `outputs/persona_profile_history/<persona_id>.json` with same-day/new-day semantics.
    - Profile/page projection stats and run-envelope fields are emitted.
  - notes: source `design.md` Section 7.5
  - evidence: Replaced `scripts/generate_profiles.py` scaffold with a full
    `persona_profile_pipeline` implementation that executes semantic flow
    `persona_profile_generation`, writes canonical profile records to
    `profiles/persona-<persona_id>.json`, and persists run metadata with canonical
    pipeline/semantic flow fields and history counters. Implemented
    space-local history update semantics in `sapi/profiles/history.py` with
    first-write generate behavior, same-day overwrite-on-change, new-day
    append-on-change, and unchanged reuse behavior. Added persona selection and
    semantic payload validation helpers in `sapi/profiles/profiles_pipeline.py`.
    Added integration coverage in `tests/integration/pipelines/test_profiles_pipeline.py`
    and history-semantics unit coverage in
    `tests/unit/profiles/test_history_update_semantics.py`.

- [x] TODO-0266: Implement Tier 3 comments/profiles integration test coverage
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0224, TODO-0228
  - scope: Add social-pipeline integration tests from Tier 3 after comments/profiles
    behaviors are implemented.
  - acceptance:
    - `tests/integration/pipelines/test_comments_pipeline.py` covers target defaults, count
      bounds, merge stability, and evidence snapshot behavior.
    - `tests/integration/pipelines/test_profiles_pipeline.py` covers profile outputs, history
      updates, and run/lint metadata.
    - Tier 3 social tests run in deterministic mock-LLM mode and are included in PR-required suites.
  - notes: source `testing_plan.md` Tier 3; `design.md` Sections 7.5, 7.6
  - evidence: Added explicit count-bounds failure coverage to
    `tests/integration/pipelines/test_comments_pipeline.py` while preserving existing
    default-target, merge-stability (`comment_uid`), and evidence-snapshot assertions.
    Expanded `tests/integration/pipelines/test_profiles_pipeline.py` to assert run-envelope lint
    totals, `runs/<run_id>/lint.json` metadata, and same-day history `updated` semantics when
    persona metrics change. Added `tests/unit/contracts/test_tier3_social_pr_suite_wiring.py`
    to assert PR-required suite wiring includes `tests/integration/pipelines`, that Tier 3
    testing-plan entries list both social modules, and that both integration modules run in
    deterministic `--mock-llm` mode.

- [x] TODO-0275: Enforce site-root `New` refresh exclusions for non-mutating flows
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0217, TODO-0220, TODO-0223, TODO-0224
  - scope: Enforce and test cross-flow site-root refresh policy so query/comment/profile
    flows do not refresh `New` unless they mutate canonical source/topic artifacts.
  - acceptance:
    - Query flow never refreshes site-root `New`.
    - Comment/profile flows only refresh site-root `New` when canonical source/topic mutation occurs.
    - Deterministic tests validate policy across ingest/query/comment/profile execution paths.
  - notes: source `design.md` Sections 2.2, 7.3, 7.5, 7.6; `low_level.md` Section 9
  - evidence: Added `tests/integration/pipelines/test_site_new_refresh_policy.py` with
    deterministic integration coverage validating that a second ingest refreshes site-root
    `site/new/index.html` while query, comments, and profiles pipeline executions leave the same
    site-root `New` artifact untouched for the same site. Existing ingest/query/comments/profiles
    integration suites remain green under mock-LLM mode with this refresh-policy coverage added.

- [x] TODO-0250: Implement run-truth advancement and reconciliation-state semantics
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0206, TODO-0214, TODO-0220, TODO-0223, TODO-0224
  - scope: Implement run-truth rules so only successful runs advance reconciliation/verification state across pipelines.
  - acceptance:
    - Only `success` and `success_with_warnings` runs advance reconciliation state.
    - `failed` and `aborted` runs are excluded from consecutive-run resolution logic.
    - Advancement behavior is tested for ingest/query/comment/profile pipelines.
  - notes: source `design.md` Section 10
  - evidence: Added centralized run-truth reconciliation advancement logic in
    `sapi/core/run_truth.py` and integrated it into successful pipeline finalization via
    `sapi/core/pipeline_policy.py`. Reconciliation state now advances only on
    `success` and `success_with_warnings` statuses and tracks per-pipeline consecutive advanced
    run counts and last advanced run metadata under
    `outputs/run_truth/reconciliation_state.json`. Added unit coverage in
    `tests/unit/core/test_run_truth.py` to enforce status advancement rules and integration
    coverage in `tests/integration/pipelines/test_run_truth_advancement.py` validating
    advancement/non-advancement semantics across ingest/query/comment/profile pipelines.

- [x] TODO-0230: CI matrix and test execution wiring
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0229
  - scope: Wire test tiers to PR/nightly jobs exactly as specified in the testing checklist.
  - acceptance:
    - PR CI runs required tiers (Tier 1-3).
    - Nightly CI runs Tier 4-6.
    - `live_llm` marker is excluded from default PR jobs and included only where intended.
  - notes: source `testing_plan.md` Sections 4-5
  - evidence: Added CI workflow wiring in `.github/workflows/ci.yml` with a PR-required job
    running Tier 1-3 (`npm run test:pr`) and a nightly/manual job running Tier 4-5
    (`npm run test:tier4-5`) plus Tier 6 live canary (`npm run test:live`) as a
    non-blocking step. Updated `package.json` scripts to use the checklist’s pytest tier
    commands with explicit marker policy (`-m "not live_llm"` for PR and deterministic/golden
    suites; `-m "live_llm"` for live canary). Added live canary module
    `tests/live/test_live_llm_canary.py`, marker registration in `pytest.ini`, and contract
    coverage in `tests/unit/contracts/test_ci_tier_matrix_wiring.py`.

- [x] TODO-0229: Tier 4-6 determinism, golden, and live-canary tests
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0266, TODO-0216, TODO-0220, TODO-0223
  - scope: Implement slower determinism/golden/live checks after core pipelines are stable.
  - acceptance:
    - Tier 4 tests cover deterministic rebuild and incremental/full equivalence.
    - Tier 5 snapshots exist for site/query/run envelope outputs.
    - Tier 6 live canary exists and is non-blocking.
  - notes: source `testing_plan.md` Tier 4-6
  - evidence: Added Tier 4 integration coverage in
    `tests/integration/build/test_build_determinism.py` and
    `tests/integration/build/test_incremental_vs_full_equivalence.py` to validate repeated
    deterministic rebuild stability and full-vs-incremental rendered-output equivalence.
    Replaced the temporary build placeholder with concrete assertions. Added Tier 5 golden
    snapshot coverage in `tests/golden/test_query_snapshot.py` and
    `tests/golden/test_run_envelope_snapshot.py` with snapshot fixtures under
    `tests/golden/query_snapshot/` and `tests/golden/run_envelope_snapshot/`, complementing the
    existing site snapshot suite. Updated `tests/live/test_live_llm_canary.py` into an opt-in
    live-mode query smoke test marked `@pytest.mark.live_llm`; nightly CI continues to run
    this marker in a non-blocking step (`continue-on-error: true`) from
    `.github/workflows/ci.yml`.

- [x] TODO-0256: Implement comment moderator/outcome blocks and deterministic social-vote rendering
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 5
  - depends_on: TODO-0223, TODO-0247, TODO-0233
  - scope: Implement moderator checks, outcome summaries, and deterministic social-vote/permalink behavior for rendered comment threads.
  - acceptance:
    - Moderator check keys and outcome sections are generated per contract.
    - Deterministic social-vote rendering uses stable inputs and preserves repeatable output.
    - Thread permalinks/expansion state remain keyed by `comment_uid`.
  - notes: source `design.md` Sections 7.6, 8
  - evidence: Extended comment merge/normalization contracts in
    `sapi/comments/merge_normalize.py` to deterministically attach social-vote fields
    (`upvotes`, `downvotes`, `score`), canonical permalink/thread keys
    (`permalink`, `thread_state_key`, `thread_expansion_key`) keyed by immutable
    `comment_uid`, and canonical moderator/outcome summary blocks including
    `- Moderator Check:` with guardrail check keys (`claim_citation`, `anti_repetition`,
    `strongest_opposing_point_ack`) plus outcome sections (`Consensus`, `Open Disagreements`,
    `Missing Evidence Priorities`). Updated deterministic page rendering in
    `sapi/build/site_builder.py` to render comment threads, moderator blocks, and score rows
    using these canonical keys/values. Added focused validation in
    `tests/unit/comments/test_turn_marker_validation.py` and end-to-end pipeline/render
    coverage in `tests/integration/pipelines/test_comments_pipeline.py`, including
    repeat-run determinism checks.

- [x] TODO-0263: Enforce testing-plan exit criteria gates before DoD closure
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0266, TODO-0229, TODO-0230
  - scope: Implement explicit checks for testing-plan exit criteria and block DoD completion when any test-gate condition is open.
  - acceptance:
    - Verification step asserts PR-required tiers are green and determinism checks have passing evidence.
    - Verification step enforces no rollback/leak regressions and no deferred-build backlog before DoD.
    - `TODO-0231` cannot be marked complete while any exit-criteria gate fails.
  - notes: source `testing_plan.md` Section 6; `design.md` Sections 11, 13
  - evidence: Added `scripts/verify_testing_exit_criteria.py` to run explicit exit-gate
    verification for PR-required tiers (`npm run test:pr`), determinism/golden checks
    (`npm run test:tier4-5`), rollback/leakage regression coverage
    (`pytest -q tests/integration/failure -m "not live_llm"`), and per-space deferred-build
    backlog audits. The script now writes both a machine-readable manifest under
    `<site_path>/outputs/verification/testing_exit_criteria/<verification_id>/manifest.json`
    and canonical gate evidence at
    `verification/testing_exit_criteria.latest.json`. Added focused coverage in
    `tests/unit/contracts/test_verify_testing_exit_criteria.py` for pass/fail gate behavior and
    `tests/unit/contracts/test_dod_exit_gate_closure.py` to enforce that closing `TODO-0231`
    requires a committed passing exit-gate evidence artifact.

- [x] TODO-0261: Enforce MVP Slice B exit gates before social/full hardening handoff
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0260, TODO-0217, TODO-0228, TODO-0229
  - scope: Convert MVP Slice B exit criteria into explicit verification checks and block downstream milestone closure until all pass.
  - acceptance:
    - Slice B reliability/determinism/operator-usability exit criteria are represented as verifiable checks.
    - Checks run in CI or scripted local verification path with evidence artifacts.
    - Slice B cannot be marked complete while any gate remains open.
  - notes: source `design.md` Section 12.1
  - evidence: Added `scripts/verify_slice_b.py` as a scripted verification path that
    encodes Slice B gates as explicit checks for (1) repeated-run reliability/determinism via
    deterministic build equivalence tests, (2) ingest/build/query contract signal via targeted
    pipeline + run-envelope + golden coverage, and (3) operator wrapper usability via wrapper
    contract suites. The verifier writes a manifest under
    `<site_path>/outputs/verification/slice_b/<verification_id>/manifest.json` and committed
    latest evidence at `verification/slice_b_exit_criteria.latest.json`. Added unit
    coverage in `tests/unit/contracts/test_verify_slice_b.py` and closure gating in
    `tests/unit/contracts/test_slice_b_exit_gate_closure.py` so `TODO-0261` cannot be treated
    as complete when any Slice B gate is open.

- [x] TODO-0231: Definition-of-Done sweep and release readiness verification
  - owner: ai
  - created_at: 2026-04-12
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0228, TODO-0229, TODO-0230, TODO-0243, TODO-0263, TODO-0261
  - scope: Execute final DoD verification across wrappers, runtime behavior, deferred-build backlog, and contract tests before first implementation milestone is considered complete.
  - acceptance:
    - All wrapper commands in DoD execute successfully on a representative site/space.
    - No runs remain with `build_deferred: true`.
    - DoD bullets from `docs/design.md` Section 13 are checked explicitly with evidence links.
  - notes: source `design.md` Section 13
  - evidence: Added `scripts/verify_dod.py` to execute a representative full wrapper sweep
    (`create_site.sh`, `create_space.sh`, `ingest.sh`, `query.sh`, `create_comments.sh`,
    `generate_profiles.sh`, `regenerate_web.sh`, `validate.sh`, `evaluate_source.sh`) and
    emit a machine-readable DoD manifest with explicit per-bullet Section 13 checks and evidence
    links at `<site_path>/outputs/verification/dod/<verification_id>/manifest.json`. Added
    committed latest DoD evidence at `verification/dod_verification.latest.json` plus
    updated upstream gate evidence at `verification/testing_exit_criteria.latest.json` and
    `verification/slice_b_exit_criteria.latest.json`, including refreshed execution of
    `scripts/verify_testing_exit_criteria.py` before final DoD closure. Added closure contract coverage in
    `tests/unit/contracts/test_dod_exit_gate_closure.py` and end-to-end verifier coverage in
    `tests/integration/wrappers/test_verify_dod.py`.

- [x] TODO-0276: Add dedicated query mode preflight test module
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0218
  - scope: Align query preflight contract coverage with testing-plan module ownership by
    placing strict/include-disputed fail-fast checks in a dedicated
    `tests/unit/query/test_query_mode_preflight.py` module.
  - acceptance:
    - Dedicated unit test module `tests/unit/query/test_query_mode_preflight.py` exists.
    - Test coverage proves `--mode strict --include-disputed` fails fast before query artifacts
      or run metadata are written.
    - `docs/testing_plan.md` Tier 1 query preflight checklist item is marked complete.
  - notes: source `docs/testing_plan.md` Tier 1; `docs/design.md` Section 7.3
  - evidence: Added `tests/unit/query/test_query_mode_preflight.py` with an explicit
    fail-fast contract test asserting exit code `2`, expected error text, and no new query/run
    artifact directories. Moved the same invalid-combination assertion out of
    `tests/unit/query/test_query_mode_defaults_policy.py` so preflight behavior is owned by
    the dedicated module, and marked the Tier 1 query preflight checklist item complete in
    `docs/testing_plan.md`.

- [x] TODO-0284: Close Tier 1 warning-budget checklist with boundary matrix tests
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0218
  - scope: Finalize the Tier 1 warning-threshold checklist item by proving threshold-boundary
    behavior across all lint-gated workflows and preserving query non-blocking semantics.
  - acceptance:
    - `tests/unit/lint/test_warning_budget_gate.py` includes explicit threshold-boundary checks
      for lint-gated workflows.
    - Test coverage confirms query remains non-blocking regardless of lint totals.
    - `docs/testing_plan.md` marks the warning-threshold Tier 1 item complete.
  - notes: source `docs/testing_plan.md` Tier 1; `docs/design.md` Section 5.8
  - evidence: Extended `tests/unit/lint/test_warning_budget_gate.py` with
    subtest-based threshold-boundary assertions for `ingest_source`, `create_comments`,
    `generate_profiles`, and `rebuild_topic_collection` (`warning_count == threshold` =>
    `success`; `warning_count > threshold` => `success_with_warnings`) and added an explicit
    high-count query assertion proving non-blocking `success` status even with errors/warnings.
    Updated `docs/testing_plan.md` to mark the Tier 1 warning-threshold checklist item complete.

- [x] TODO-0285: Close Tier 1 run-envelope semantic-flow cardinality checklist
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0206
  - scope: Finalize Tier 1 run-envelope semantic-flow-cardinality coverage by adding explicit
    invalid-shape contract checks for `semantic_flows` and
    `semantic_flow_invocation_counts`.
  - acceptance:
    - `tests/unit/contracts/test_run_envelope_semantic_flows.py` proves duplicate
      `semantic_flows` are rejected.
    - Tests prove missing/extra/non-positive invocation-count map entries are rejected.
    - `docs/testing_plan.md` marks the run-envelope-cardinality Tier 1 item complete.
  - notes: source `docs/testing_plan.md` Tier 1; `docs/design.md` Section 10
  - evidence: Extended
    `tests/unit/contracts/test_run_envelope_semantic_flows.py` with explicit negative-path
    assertions for duplicate semantic-flow entries, missing invocation-count keys, extra
    invocation-count keys not present in `semantic_flows`, and non-positive invocation counts.
    Updated `docs/testing_plan.md` to mark the Tier 1 run-envelope semantic-flow-cardinality
    checklist item complete.

- [x] TODO-0286: Close Tier 1 semantic-spec flow-map and alias-normalization checklist
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 2
  - depends_on: TODO-0203
  - scope: Finalize Tier 1 semantic-spec resolution checklist coverage by asserting canonical
    flow-key handling does not emit alias-deprecation warnings while preserving mapped alias
    behavior and flow-map pinning.
  - acceptance:
    - `tests/unit/semantic/test_spec_resolution.py` explicitly covers canonical-key no-warning behavior.
    - Existing flow-map resolution/version-pinning/alias-normalization coverage remains green.
    - `docs/testing_plan.md` marks the semantic-spec Tier 1 item complete.
  - notes: source `docs/testing_plan.md` Tier 1; `docs/design.md` Section 4.1.3
  - evidence: Extended `tests/unit/semantic/test_spec_resolution.py` with
    `test_canonical_flow_key_does_not_emit_alias_deprecation_warning`, asserting canonical
    `comment_section_generation` input remains unchanged, resolves successfully through the
    authoritative flow map, and does not produce deprecation warnings reserved for compatibility
    aliases. Updated `docs/testing_plan.md` to mark the Tier 1 semantic-spec checklist item
    complete.

- [x] TODO-0287: Close Tier 1 retry-budget checklist with explicit custom-loop coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 2
  - depends_on: TODO-0203
  - scope: Finalize Tier 1 retry-budget checklist evidence by explicitly validating custom
    `max_repair_loops` behavior and returned attempt counts used for run-level
    `llm_attempt_count` accounting.
  - acceptance:
    - `tests/unit/semantic/test_retry_budget.py` verifies `max_repair_loops` controls
      `max_attempts`.
    - Tests verify returned semantic attempt count matches expected total attempts for the
      configured repair-loop budget.
    - `docs/testing_plan.md` marks the retry-budget Tier 1 item complete.
  - notes: source `docs/testing_plan.md` Tier 1; `docs/design.md` Section 2.1
  - evidence: Added
    `test_custom_repair_loop_budget_controls_max_attempts_and_returned_attempt_count` to
    `tests/unit/semantic/test_retry_budget.py`, asserting `max_repair_loops=1` yields
    `max_attempts=2`, the semantic call succeeds on the final allowed attempt, and returned
    `attempt_count` equals the configured total-attempt budget used by pipeline-level
    `llm_attempt_count` aggregation. Updated `docs/testing_plan.md` to mark the Tier 1
    retry-budget checklist item complete.

- [x] TODO-0288: Close Tier 1 registry-path checklist with explicit relative-path resolution test
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 1
  - depends_on: TODO-0205
  - scope: Finalize Tier 1 registry-path checklist evidence with an explicit test for resolving
    relative `--registry-path` arguments against the current working directory while preserving
    the no-home-fallback contract.
  - acceptance:
    - `tests/unit/contracts/test_registry_paths.py` covers relative registry-path resolution.
    - Existing coverage for relative `space_root` resolution and no implicit home fallback
      remains green.
    - `docs/testing_plan.md` marks the Tier 1 registry-path checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 1; `docs/design.md` Section 5.5
  - evidence: Added
    `test_relative_registry_path_resolves_against_cwd_without_home_fallback` to
    `tests/unit/contracts/test_registry_paths.py`, asserting `resolve_registry_path("spaces.toml")`
    resolves to an absolute path under the active working directory. Existing no-fallback tests
    continue to validate that missing explicit registry paths fail and `~/.sapi/spaces.toml`
    is not used implicitly. Updated `docs/testing_plan.md` to mark the Tier 1 registry-path
    checklist item complete.

- [x] TODO-0289: Close Tier 1 ID/format/path checklist with explicit suffix and UTC-normalization checks
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 1
  - depends_on: TODO-0206
  - scope: Finalize Tier 1 ID/format/path checklist coverage with explicit checks for provided
    execution/comment suffix constraints and timezone-aware timestamp normalization to UTC.
  - acceptance:
    - `tests/unit/contracts/test_id_contracts.py` covers invalid explicit suffix values for
      query/comment IDs.
    - Temporal format tests assert timezone-aware input normalizes to RFC3339 UTC with trailing `Z`.
    - `docs/testing_plan.md` marks the Tier 1 ID/format/path checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 1; `docs/design.md` Section 5.4
  - evidence: Extended `tests/unit/contracts/test_id_contracts.py` to assert
    `make_query_id(..., suffix=\"short123\")` and
    `make_comment_uid(..., suffix=\"short123\")` fail fast for violating minimum
    suffix-length constraints, and added a timezone-offset timestamp case proving
    `format_timestamp_rfc3339_utc` normalizes to canonical UTC (`...Z`). Updated
    `docs/testing_plan.md` to mark the Tier 1 ID/format/path checklist item complete.

- [x] TODO-0290: Close Tier 2 failed-run container cleanup checklist across comment/profile flows
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 2
  - depends_on: TODO-0223, TODO-0224
  - scope: Finalize Tier 2 failed-run cleanup coverage by proving default-mode terminal
    failures in comment/profile pipelines do not persist committed run containers.
  - acceptance:
    - `tests/integration/failure/test_run_container_not_persisted.py` covers comment pipeline
      terminal failure run-container non-persistence.
    - The same module covers profile pipeline terminal failure run-container non-persistence.
    - `docs/testing_plan.md` marks the Tier 2 run-container checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 2; `docs/design.md` Sections 2.1, 10
  - evidence: Extended
    `tests/integration/failure/test_run_container_not_persisted.py` with
    `test_comments_terminal_failure_does_not_persist_new_run_container` (asserting no new
    `runs/run-*` directory is committed after simulated comment failure) and
    `test_profiles_terminal_failure_does_not_persist_run_container` (asserting no committed
    run container for simulated profile failure with default persona selection). Updated
    `docs/testing_plan.md` to mark the Tier 2 run-container checklist item complete.

- [x] TODO-0291: Close Tier 2 repair-loop exhaustion rollback checklist across ingest/profile flows
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 2
  - depends_on: TODO-0203, TODO-0224
  - scope: Finalize Tier 2 repair-loop exhaustion evidence by proving terminal semantic
    retry exhaustion causes rollback for both ingest and profile pipelines.
  - acceptance:
    - `tests/integration/failure/test_semantic_repair_exhaustion_rollback.py` retains ingest
      rollback coverage for schema-repair exhaustion.
    - The same module covers profile semantic-repair exhaustion rollback behavior.
    - `docs/testing_plan.md` marks the Tier 2 repair-loop exhaustion checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 2; `docs/design.md` Section 2.1
  - evidence: Extended
    `tests/integration/failure/test_semantic_repair_exhaustion_rollback.py` with
    `test_semantic_repair_exhaustion_rolls_back_default_profile_writes`, patching
    profile semantic generation to return schema-invalid payloads until retry budget
    exhaustion and asserting rollback leaves no committed profile/history/run artifacts.
    Existing ingest exhaustion rollback assertions remain intact. Updated
    `docs/testing_plan.md` to mark the Tier 2 repair-loop exhaustion item complete.

- [x] TODO-0292: Close Tier 2 deterministic post-processing rollback checklist for ingest/query
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 2
  - depends_on: TODO-0220, TODO-0222
  - scope: Finalize Tier 2 deterministic post-processing failure evidence by proving
    rollback semantics for invocation-scoped writes in both ingest and query paths.
  - acceptance:
    - `tests/integration/failure/test_postprocess_failure_rollback.py` retains ingest
      deterministic post-processing failure rollback coverage.
    - The same module covers query non-markdown deterministic post-processing failure
      rollback behavior.
    - `docs/testing_plan.md` marks the Tier 2 deterministic post-processing checklist
      item complete.
  - notes: source `docs/testing_plan.md` Tier 2; `docs/design.md` Section 2.1
  - evidence: Extended
    `tests/integration/failure/test_postprocess_failure_rollback.py` with
    `test_query_non_markdown_postprocess_failure_rolls_back_query_outputs`,
    patching query deterministic artifact rendering to fail and asserting rollback
    removes invocation-scoped query outputs and leaves no committed run container.
    Existing ingest post-processing rollback coverage remains intact. Updated
    `docs/testing_plan.md` to mark the Tier 2 deterministic post-processing item
    complete.

- [x] TODO-0293: Close Tier 3 ingest happy-path pipeline checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0210
  - scope: Finalize Tier 3 ingest happy-path integration evidence by proving canonical
    artifact writes plus committed run/lint metadata invariants in one mock-mode ingest run.
  - acceptance:
    - `tests/integration/pipelines/test_ingest_pipeline.py` covers canonical ingest
      artifacts across source, claim, relation, and topic records.
    - The same module verifies committed ingest run metadata includes flow identity,
      invocation counts, changed-count fields, and lint totals.
    - `docs/testing_plan.md` marks the Tier 3 ingest happy-path checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Sections 2.1, 10
  - evidence: Extended
    `tests/integration/pipelines/test_ingest_pipeline.py` to assert relation artifact
    contract pathing and changed-count consistency, run-frontmatter source/lint fields, run-id directory
    alignment, and lint artifact warning/info totals in addition to existing canonical
    artifact and semantic-flow checks. Updated `docs/testing_plan.md` to mark the
    Tier 3 ingest happy-path item complete.

- [x] TODO-0294: Close Tier 3 ingest source-only semantic bypass checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0210
  - scope: Finalize Tier 3 source-only ingest evidence by proving semantic generation is
    skipped while source ingestion and run/lint metadata still commit successfully.
  - acceptance:
    - `tests/integration/pipelines/test_ingest_source_only.py` verifies
      `semantic_flows=[]` and empty `semantic_flow_invocation_counts` for `--source-only`.
    - The same module asserts semantic artifact writes (claims/relations/topics) are skipped.
    - `docs/testing_plan.md` marks the Tier 3 ingest source-only checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Sections 2.2, 10
  - evidence: Added
    `tests/integration/pipelines/test_ingest_source_only.py` with
    `test_ingest_source_only_skips_semantic_writes_and_records_empty_semantic_flows`,
    asserting source record persistence, no claim/relation/topic writes, no build manifest,
    and committed run metadata with empty semantic flow fields plus zero changed-count and
    `llm_attempt_count` values. Updated `docs/testing_plan.md` to mark the Tier 3
    source-only item complete.

- [x] TODO-0295: Close Tier 3 ingest force-mode failure retention checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0210
  - scope: Finalize Tier 3 ingest `--force` evidence by proving terminal failure preserves
    invocation artifacts and commits failed-run metadata with force retention fields.
  - acceptance:
    - `tests/integration/pipelines/test_ingest_force_mode.py` verifies failed ingest with
      `--force` preserves partial artifacts instead of rolling them back.
    - The same module verifies run metadata records `force_mode=true` and
      `rollback_skipped=true`.
    - `docs/testing_plan.md` marks the Tier 3 ingest force-mode checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Sections 2.1, 7.1, 10
  - evidence: Added
    `tests/integration/pipelines/test_ingest_force_mode.py` with
    `test_force_mode_failure_preserves_partial_artifacts_and_force_flags`,
    asserting simulated terminal ingest failure with `--force` keeps source record and
    committed run/lint artifacts, and run frontmatter captures failed status with
    `force_mode=true` and `rollback_skipped=true`. Updated `docs/testing_plan.md` to
    mark the Tier 3 ingest force-mode item complete.

- [x] TODO-0296: Close Tier 3 query output-mode manifest contract checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0220
  - scope: Finalize Tier 3 query output-mode evidence by proving markdown and non-markdown
    query runs persist manifest metadata consistently across query artifacts and run records.
  - acceptance:
    - `tests/integration/pipelines/test_query_pipeline_outputs.py` verifies markdown mode
      omits manifest artifacts and keeps run/query `manifest_path` null.
    - The same module verifies non-markdown mode writes `manifest.json` and records the
      canonical manifest path in run frontmatter.
    - `docs/testing_plan.md` marks the Tier 3 query output-mode checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Sections 7.3, 10
  - evidence: Extended
    `tests/integration/pipelines/test_query_pipeline_outputs.py` to assert run-frontmatter
    `manifest_path` behavior for both markdown and mermaid output modes. Updated
    `scripts/query.py` to propagate the canonical non-markdown manifest path into
    `QueryRunFields.manifest_path` so run metadata matches the emitted query artifact
    contract. Updated `docs/testing_plan.md` to mark the Tier 3 query output-mode item
    complete.

- [x] TODO-0297: Close Tier 3 profiles pipeline checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0224
  - scope: Finalize Tier 3 persona profiles evidence by proving profile JSON/history writes
    alongside committed run/lint metadata invariants for multi-persona runs.
  - acceptance:
    - `tests/integration/pipelines/test_profiles_pipeline.py` verifies canonical profile JSON
      and profile-history writes for selected personas.
    - The same module verifies committed run metadata includes flow identity, status,
      execution mode, semantic invocation counts, and lint totals.
    - `docs/testing_plan.md` marks the Tier 3 profiles checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Sections 7.5, 10
  - evidence: Extended
    `tests/integration/pipelines/test_profiles_pipeline.py` with explicit run-envelope
    assertions (`status`, `execution_mode`, `run_id` alignment, and `llm_attempt_count`)
    in the multi-persona profile generation scenario while retaining existing profile/history
    and lint artifact checks. Updated `docs/testing_plan.md` to mark the Tier 3 profiles
    item complete.

- [x] TODO-0298: Close Tier 3 comments pipeline checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 3
  - depends_on: TODO-0223
  - scope: Finalize Tier 3 comments pipeline evidence by strengthening explicit contract
    assertions for semantic artifact page targeting while preserving existing bounds, merge,
    and evidence snapshot coverage.
  - acceptance:
    - `tests/integration/pipelines/test_comments_pipeline.py` verifies default topic targeting
      and per-page semantic artifact pathing contracts.
    - The same module continues to cover count bounds, comment UID merge stability, and
      web-augmented evidence snapshot path/schema contracts.
    - `docs/testing_plan.md` marks the Tier 3 comments checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Sections 7.6, 10
  - evidence: Extended
    `tests/integration/pipelines/test_comments_pipeline.py` to assert run-envelope
    `semantic_flows`/`requested_count` and to validate each semantic artifact payload's
    `page_ref` and `requested_count` against canonical topic targets. Existing integration
    tests in the same module continue to enforce count bounds, merge stability for
    `comment_uid`, and web-augmented snapshot path/schema behavior. Updated
    `docs/testing_plan.md` to mark the Tier 3 comments item complete.

- [x] TODO-0299: Close Tier 3 evaluate_source default artifact-pack checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0273
  - scope: Finalize Tier 3 default `evaluate_source.sh` evidence by ensuring manifest linkage
    includes strict-query run metadata in addition to ingest linkage for the default pack flow.
  - acceptance:
    - `tests/integration/wrappers/test_evaluate_source_harness.py` verifies default run emits
      required markdown artifact pack and manifest linkage.
    - Manifest linkage includes committed ingest and query run IDs for the default flow.
    - `docs/testing_plan.md` marks the Tier 3 default evaluate_source checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Sections 7.3, 10
  - evidence: Updated `scripts/evaluate_source.py` to capture strict-query `run_id` from query
    output and persist it to manifest `run_ids.query`. Extended default harness integration
    assertions in `tests/integration/wrappers/test_evaluate_source_harness.py` to require both
    ingest and query run IDs resolve to committed run containers. Updated
    `docs/testing_plan.md` to mark the default evaluate_source checklist item complete.

- [x] TODO-0300: Close Tier 3 evaluate_source comments-mode checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0273
  - scope: Finalize Tier 3 comments-enabled evaluate_source coverage by ensuring comments-mode
    runs produce `comments_review.md` with valid comment target handling, while invalid
    comments counts still fail fast with clear errors.
  - acceptance:
    - `tests/integration/wrappers/test_evaluate_source_harness.py` comments-mode run emits
      `comments_review.md` and manifests effective per-page/per-user requested counts.
    - Invalid comments count arguments continue to fail fast without partial artifact packs.
    - `docs/testing_plan.md` marks the Tier 3 comments-mode evaluate_source checklist item
      complete.
  - notes: source `docs/testing_plan.md` Tier 3; `docs/design.md` Section 6.3
  - evidence: Updated `scripts/create_comments.py` bootstrap comment body generation to avoid
    embedding raw page refs that could trigger unclassified factual-claim validation for
    comments-mode harness runs. Updated comments integration fixture in
    `tests/integration/pipelines/test_comments_pipeline.py` accordingly. Extended
    `tests/integration/wrappers/test_evaluate_source_harness.py` comments-mode scenario to use
    canonical `--comment-page topic:<topic_id>` targeting with an explicit topic fixture and
    updated manifest/README/comments-review expectations. Verified full harness test module
    (including invalid `--comments` failure case) passes. Updated `docs/testing_plan.md` to
    mark the comments-mode item complete.

- [x] TODO-0301: Close Tier 4 full deterministic rebuild consistency checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0210
  - scope: Finalize Tier 4 deterministic rebuild evidence by strengthening explicit assertions
    that full build snapshots include canonical manifest/site outputs and remain identical
    across repeated rebuilds.
  - acceptance:
    - `tests/integration/build/test_build_determinism.py` verifies repeated full rebuilds
      produce identical deterministic output snapshots.
    - The same module explicitly asserts canonical snapshot coverage includes site-root index,
      space index, and build manifest outputs.
    - `docs/testing_plan.md` marks the Tier 4 full deterministic rebuild checklist item
      complete.
  - notes: source `docs/testing_plan.md` Tier 4; `docs/design.md` Sections 2.2, 8
  - evidence: Extended
    `tests/integration/build/test_build_determinism.py` with explicit snapshot-presence
    assertions for `site/index.html`, `spaces/alpha/site/index.html`, and
    `outputs/build_site/manifest.json` prior to deterministic snapshot equality checks.
    Verified the build determinism integration test passes and updated
    `docs/testing_plan.md` to mark the Tier 4 deterministic rebuild item complete.

- [x] TODO-0302: Close Tier 4 site-root New refresh policy checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0210, TODO-0220, TODO-0223, TODO-0224
  - scope: Finalize Tier 4 site-root `New` refresh policy evidence by placing integration
    coverage in the build determinism suite location defined by the testing plan and verifying
    flow-scoped refresh/no-refresh behavior.
  - acceptance:
    - `tests/integration/build/test_site_new_refresh_policy.py` verifies query/profile/comments
      flows do not refresh site-root `New`.
    - The same module verifies subsequent ingest refreshes site-root `New`.
    - `docs/testing_plan.md` marks the Tier 4 site-root refresh policy checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 4; `docs/design.md` Section 2.2
  - evidence: Moved site-root refresh policy integration coverage from
    `tests/integration/pipelines/test_site_new_refresh_policy.py` to canonical Tier 4 path
    `tests/integration/build/test_site_new_refresh_policy.py` and verified the module passes.
    Updated `docs/testing_plan.md` to mark the Tier 4 site-root refresh policy item complete.

- [x] TODO-0303: Close Tier 4 incremental-vs-full build equivalence checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0210
  - scope: Finalize Tier 4 incremental build equivalence evidence by strengthening explicit
    assertions for canonical rendered outputs in the full snapshot before equivalence checks.
  - acceptance:
    - `tests/integration/build/test_incremental_vs_full_equivalence.py` verifies incremental
      build snapshots equal full build snapshots.
    - The same module asserts canonical site-root and space index outputs are present in the
      compared snapshot set.
    - `docs/testing_plan.md` marks the Tier 4 incremental equivalence checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 4; `docs/design.md` Sections 2.2, 8
  - evidence: Extended
    `tests/integration/build/test_incremental_vs_full_equivalence.py` with explicit snapshot
    presence assertions for `site/index.html` and `spaces/alpha/site/index.html` prior to full
    vs incremental rendered-output equality checks. Verified test pass and updated
    `docs/testing_plan.md` to mark the Tier 4 incremental equivalence item complete.

- [x] TODO-0304: Close Tier 5 site snapshot checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0251
  - scope: Finalize Tier 5 site-page snapshot evidence by extending golden coverage for core
    navigation/content contracts beyond space-home-only assertions.
  - acceptance:
    - `tests/golden/test_site_snapshot.py` validates a site-root navigation/content snapshot.
    - Existing space-home snapshot coverage remains in the same module.
    - `docs/testing_plan.md` marks the Tier 5 site snapshot checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 5; `docs/design.md` Section 8
  - evidence: Added golden fixture
    `tests/golden/site_snapshot/site_root_index_empty.html` and extended
    `tests/golden/test_site_snapshot.py` with a deterministic assertion for
    `site/index.html` while preserving the existing `spaces/alpha/site/index.html`
    snapshot assertion. Verified the golden module passes and updated
    `docs/testing_plan.md` to mark the Tier 5 site snapshot item complete.

- [x] TODO-0305: Close Tier 5 query artifact snapshot checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0220
  - scope: Finalize Tier 5 query artifact golden evidence by snapshotting key output modes
    instead of a single default-mode payload.
  - acceptance:
    - `tests/golden/test_query_snapshot.py` verifies normalized query payload output for
      markdown mode.
    - The same module verifies normalized artifact-manifest output for a non-markdown mode.
    - `docs/testing_plan.md` marks the Tier 5 query artifact snapshot checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 5; `docs/design.md` Sections 2.2, 7.3
  - evidence: Extended `tests/golden/test_query_snapshot.py` with an additional mermaid-mode
    golden assertion and added fixture
    `tests/golden/query_snapshot/empty_space_mermaid_manifest.normalized.json` with normalized
    `query_id`/`run_id` and hash placeholders. Existing markdown payload snapshot coverage
    remains in the same module. Updated `docs/testing_plan.md` to mark the Tier 5 query
    artifact snapshot item complete.

- [x] TODO-0306: Close Tier 5 run-envelope snapshot checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0210, TODO-0220, TODO-0223, TODO-0224
  - scope: Finalize Tier 5 run-envelope golden evidence by covering all pipeline frontmatter
    envelopes instead of query-only snapshots.
  - acceptance:
    - `tests/golden/test_run_envelope_snapshot.py` validates normalized ingest, query,
      comments, and profiles run frontmatter snapshots.
    - Golden fixtures exist for each covered pipeline envelope.
    - `docs/testing_plan.md` marks the Tier 5 run-envelope snapshot checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 5; `docs/design.md` Section 10
  - evidence: Extended `tests/golden/test_run_envelope_snapshot.py` with new snapshot tests for
    `ingest_pipeline`, `comment_section_pipeline`, and `persona_profile_pipeline`, while
    preserving query coverage. Added
    `tests/golden/run_envelope_snapshot/ingest_run_frontmatter.normalized.json`,
    `tests/golden/run_envelope_snapshot/comments_run_frontmatter.normalized.json`, and
    `tests/golden/run_envelope_snapshot/profiles_run_frontmatter.normalized.json`, and
    normalized dynamic fields (`run_id`, timestamps, source IDs, target page refs, python
    version) in assertions. Updated `docs/testing_plan.md` to mark the run-envelope item
    complete.

- [x] TODO-0307: Close Tier 6 live LLM canary checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 6
  - depends_on: TODO-0210, TODO-0220
  - scope: Finalize Tier 6 non-blocking live-canary coverage with a minimal real-backend
    end-to-end smoke path and explicit opt-in execution controls.
  - acceptance:
    - `tests/live/test_live_llm_canary.py` is marked `@pytest.mark.live_llm`.
    - Live canary executes a minimal real-backend smoke for integration drift detection.
    - `docs/testing_plan.md` marks the Tier 6 live canary checklist item complete.
  - notes: source `docs/testing_plan.md` Tier 6; `docs/design.md` Sections 2, 11
  - evidence: Updated `tests/live/test_live_llm_canary.py` to run opt-in
    `ingest_source.py -> query.py` live smoke execution (no `--mock-llm`) with gating on
    `SAPI_RUN_LIVE_CANARY=1` and `OPENAI_API_KEY` presence, and assertions on newly created
    run envelopes for `ingest_pipeline` and `query_pipeline` with `execution_mode=live_llm`.
    Updated `docs/testing_plan.md` to mark Tier 6 live canary complete.

- [x] TODO-0308: Close Tier 0 isolated fixture-factory checklist coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 4
  - depends_on: TODO-0200
  - scope: Add a dedicated site/space fixture factory for tests that guarantees isolated
    registry roots and explicit fixture metadata for downstream contract tests.
  - acceptance:
    - `tests/conftest.py` provides a site/space temp fixture factory with isolated registries.
    - Tests prove separate fixture instances do not share registry resolution scope.
    - `docs/testing_plan.md` marks the Tier 0 fixture-factory item complete.
  - notes: source `docs/testing_plan.md` Tier 0; `docs/design.md` Sections 5, 11
  - evidence: Added `IsolatedSiteSpaceFixture` and
    `create_isolated_site_space_fixture(...)` to `tests/conftest.py`, plus optional
    site-name/site-dir parameters for `bootstrap_site_and_space(...)` while preserving default
    behavior. Added focused coverage in
    `tests/unit/contracts/test_harness_fixture_factory.py` to assert isolated fixture roots,
    distinct registry files, and registry-scoped `resolve_space_root(...)` behavior for
    multiple fixtures. Updated `docs/testing_plan.md` to mark the Tier 0 fixture-factory item
    complete.

- [x] TODO-0309: Track rebuilt Tier 0 foundation queue after open TODO reset
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Cross-cutting
  - scope: Reconstitute open TODO queue from unchecked testing-plan work after clearing
    `docs/todo.md`.
  - acceptance:
    - `docs/todo.md` contains concrete open task blocks mapped to unchecked testing-plan work.
    - Ready/queue/coverage snapshot sections reflect those open tasks consistently.
    - New tasks use stable IDs and dependency ordering.
  - notes: source `docs/todo.md` operating rules; `docs/testing_plan.md` unchecked items
  - evidence: Rebuilt `docs/todo.md` open queue around remaining unchecked testing-plan work
    (`TODO-0310`, `TODO-0311`, `TODO-0312`), moved `TODO-0310` into Ready Now after removing
    the resolved dependency on `TODO-0309`, and synchronized priority lanes, execution queue,
    and design/low-level/testing-plan coverage snapshots to the remaining open IDs. Added
    `tests/unit/contracts/test_todo_0309_queue_reconstitution.py` to lock these queue and
    dependency invariants.

- [x] TODO-0310: Add deterministic mock LLM fixture modes for contract tests
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-13
  - phase: Phase 4
  - scope: Add mock LLM fixture utilities in `tests/conftest.py` for `valid`,
    `invalid_then_repair`, and `repair_exhausted` modes.
  - acceptance:
    - Fixture factory exposes all three required modes with deterministic payloads.
    - Existing semantic retry/spec tests can consume the fixture utilities without behavior regressions.
    - Tier 0 mock fixture checklist item is marked complete in `docs/testing_plan.md`.
  - notes: source `docs/testing_plan.md` Tier 0; `docs/design.md` Section 11
  - evidence: Added `DeterministicMockLlmFixture` and
    `create_deterministic_mock_llm_fixture(...)` in `tests/conftest.py` with the required
    modes and deterministic outputs. Updated `tests/unit/semantic/test_retry_budget.py` to
    consume the shared fixture utilities and added dedicated fixture-mode coverage in
    `tests/unit/semantic/test_mock_llm_fixture_modes.py`. Updated `docs/testing_plan.md` to
    mark the Tier 0 mock-fixture item complete.

- [x] TODO-0340: Render overview article on space/subspace front pages
  - owner: ai
  - created_at: 2026-04-16
  - finished_at: 2026-04-24
  - phase: Phase 6
  - depends_on: TODO-0339
  - scope: Surface generated overview content directly on each space/subspace landing page and
    expose a dedicated full overview route.
  - acceptance:
    - `sapi/build/site_builder.py` (or delegated render modules) renders a prominent overview
      section on each space/subspace index page when overview artifacts exist.
    - Full article route is generated at canonical location
      `spaces/<space_name>/site/overview/index.html`.
    - Space/subspace navigation links to overview route with stable semantics and accessibility
      labels.
    - If overview artifact is missing, rendering degrades gracefully without broken links.
  - notes: source `docs/todo.md`; `docs/design.md` Section 8; `docs/testing_plan.md` Tier 4-6
  - evidence: Completed the builder-side overview render path in `sapi/build/site_builder.py`
    by adding the missing home-card and full-article helpers, generating
    `site/overview/index.html` for every space, and wiring a stable `Overview` nav tab with an
    explicit accessibility label plus empty-state fallback when no overview artifact exists.
    Expanded `tests/unit/build/test_site_builder_contracts.py` for empty-state, space, and
    subspace overview rendering, and extended
    `tests/integration/build/test_build_determinism.py` so the overview route participates in
    deterministic build snapshots.

- [x] TODO-0341: Add change-detection and refresh policy for overview regeneration
  - owner: ai
  - created_at: 2026-04-16
  - finished_at: 2026-04-25
  - phase: Phase 6
  - depends_on: TODO-0339
  - scope: Ensure overview generation is refreshed only when relevant canonical inputs change,
    while preserving explicit force-regeneration behavior for debugging/recovery.
  - acceptance:
    - Overview pipeline computes and persists an input signature derived from canonical records
      used for synthesis (`sources/records`, `claims`, `relations`, and source dossiers).
    - Re-running overview generation with unchanged signature skips LLM synthesis and records a
      deterministic “no content change” path.
    - A force mode bypasses signature skip behavior and re-synthesizes overview artifacts.
    - Run metadata records refresh decision details (signature, skip/refresh reason, flow
      invocation counts).
  - notes: source `docs/todo.md`; `docs/design.md` Section 7.2.1 and run-envelope section;
    `docs/low_level.md` Section 8.5
  - evidence: Added `OverviewRefreshDecision` and canonical artifact/signature comparison logic in
    `sapi/overview/overview_pipeline.py`, then updated `scripts/generate_overview.py` to skip
    semantic regeneration when the persisted signature matches current inputs, honor a local
    `--force` override, and record `input_signature`, `refresh_decision`, `refresh_reason`, and
    `force_mode` in overview run metadata. Expanded
    `tests/integration/pipelines/test_overview_pipeline.py` with unchanged-signature skip and
    force-regeneration coverage, added helper-level unit coverage in
    `tests/unit/overview/test_overview_pipeline.py`, and updated run-envelope/doc contract tests
    to lock the new metadata and documented refresh policy.

- [x] TODO-0342: Add overview synthesis tests, wrappers, and live-canary coverage
  - owner: ai
  - created_at: 2026-04-16
  - finished_at: 2026-04-25
  - phase: Phase 6
  - depends_on: TODO-0339
  - scope: Add comprehensive coverage and wrapper-level ergonomics for space-overview generation
    and rendering across local and live modes.
  - acceptance:
    - Unit/integration tests validate overview artifact schema compliance, reference integrity
      (claims/sources), and deterministic rebuild behavior.
    - Wrapper contract tests cover canonical invocation path for overview generation (including
      target space/subspace selection and failure semantics).
    - Live canary coverage includes overview generation for at least one seeded space and asserts
      canonical artifacts are present and parseable.
    - `docs/testing_plan.md` is updated with explicit overview-flow coverage expectations.
  - notes: source `docs/todo.md`; `docs/testing_plan.md` Sections 2-6; wrapper/operator ergonomics
    per `AGENTS.md`
  - evidence: Added repo-root wrapper `generate_overview.sh`, updated repo metadata/docs to treat
    it as the canonical operator entrypoint, and expanded
    `tests/integration/wrappers/test_bootstrap_registry_exception.py` plus new
    `tests/integration/wrappers/test_generate_overview_wrapper.py` to cover registry routing,
    subspace targeting, and propagated terminal-failure semantics. Extended
    `tests/live/test_live_llm_canary.py` to execute live overview generation and validate
    canonical `overview.json` / `article.md` artifacts, and updated `docs/testing_plan.md` with
    explicit wrapper and live-canary overview coverage checkpoints.

- [x] TODO-0327: Purge compatibility/deprecation tests and add strict no-legacy coverage
  - owner: ai
  - created_at: 2026-04-13
  - finished_at: 2026-04-25
  - phase: Cross-cutting
  - depends_on: TODO-0313, TODO-0314, TODO-0315, TODO-0316, TODO-0317, TODO-0318, TODO-0319, TODO-0320, TODO-0321, TODO-0322, TODO-0323
  - scope: Remove compatibility/deprecation-only test expectations and replace them with strict canonical-only behavior checks.
  - acceptance:
    - Tests no longer assert deprecation warnings or legacy alias acceptance for removed pathways.
    - New/updated tests assert legacy inputs fail fast with clear errors.
    - `docs/testing_plan.md` is updated where test contract expectations changed.
  - evidence: Updated `docs/testing_plan.md` so the Tier 1 checklist now describes removed-flow-key
    fail-fast handling and explicit no-legacy coverage across flow-map, wrapper/parser, persona,
    comment, and relation boundaries. Added
    `tests/unit/contracts/test_no_legacy_test_coverage.py` to lock those coverage expectations and
    to assert the compatibility-purge suite does not reintroduce deprecation-warning or
    legacy-alias-acceptance assertions. Refreshed
    `tests/unit/contracts/test_canonical_only_doc_contracts.py` to follow the current
    `docs/low_level.md` section anchors, then reran the focused canonical-only suite covering
    semantic spec resolution, runtime flag surfaces, persona loading, comment validation, relation
    normalization, comment pipeline fail-fast behavior, and wrapper alias rejection.

- [x] TODO-0351: Route semantic pipeline finalization through the shared lint gate
  - owner: ai
  - created_at: 2026-04-25
  - finished_at: 2026-04-25
  - phase: Cross-cutting
  - scope: Ensure semantic pipeline entrypoints derive committed lint totals and warning-budget
    status from the shared lint-gate path instead of stamping literal zero-count metadata.
  - acceptance:
    - Shared pipeline policy exposes one helper that stamps `RunEnvelopeBase.lint_*` fields from a
      `LintSummary` and merges warning-budget status into terminal run state.
    - `scripts/ingest_source.py`, `scripts/create_comments.py`, `scripts/generate_profiles.py`,
      `scripts/query.py`, and `scripts/generate_overview.py` use that shared helper on both
      success and retained-failure paths.
    - Docs and tests explicitly cover the shared-finalization contract.
  - evidence: Added `apply_lint_gate_to_run_base()` in `sapi/core/pipeline_policy.py`, which
    evaluates the workflow-specific lint gate, stamps committed `lint_error_count`,
    `lint_warning_count`, and `lint_info_count`, and merges warning-budget status into the run
    envelope before `finalize_pipeline_run()`. Updated the five semantic pipeline entrypoints to
    use that helper instead of hardcoded `lint_error_count=0 lint_warning_count=0
    lint_info_count=0` strings, expanded `tests/unit/core/test_pipeline_policy.py` with
    warning-budget, preserved-warning-status, and query-nonblocking cases, added
    `tests/unit/contracts/test_pipeline_lint_contracts.py` for design/low-level/testing-plan sync,
    and updated `docs/design.md`, `docs/low_level.md`, and `docs/testing_plan.md` to require the
    shared lint-gate finalization path. Focused validation also exposed a flaky `latest_run_directory()`
    helper when two runs landed in the same second, so `tests/conftest.py` now sorts run
    directories by committed `run.md` mtime and `tests/unit/contracts/test_run_directory_helper.py`
    locks that behavior.

- [x] TODO-0352: Run deterministic social post-processing before comment/profile success exit
  - owner: ai
  - created_at: 2026-04-25
  - finished_at: 2026-04-25
  - phase: Cross-cutting
  - scope: Ensure comment and persona-profile pipelines execute the required deterministic space
    build/post-processing before reporting success, so affected HTML/views are current without a
    manual follow-up `build_site.py`.
  - acceptance:
    - `scripts/create_comments.py` triggers deterministic space build after canonical comment merge
      and before successful exit.
    - `scripts/generate_profiles.py` triggers deterministic space build after canonical
      profile/history updates and before successful exit.
    - Integration tests assert the commands themselves leave built HTML/assets/manifests behind
      without an extra explicit build step.
  - evidence: Added shared helper `sapi/core/postprocess.py::run_space_build_postprocess()` and
    routed ingest's existing deterministic build call through it. Updated `scripts/create_comments.py`
    and `scripts/generate_profiles.py` to invoke that helper before success finalization and to
    surface `build_manifest_path` in command output. Tightened
    `tests/integration/pipelines/test_comments_pipeline.py` and
    `tests/integration/pipelines/test_profiles_pipeline.py` so they assert built HTML/assets and
    `outputs/build_site/manifest.json` directly from the comment/profile commands, and added
    `tests/unit/core/test_postprocess_helpers.py` for shared helper success/failure behavior.
    Focused validation required normalizing a few seeded topic fixtures so they satisfy the
    deterministic build input contract (`sections` array present) now that the pipelines no longer
    skip the build step.

- [x] TODO-0353: Refresh example site runner for current pipeline surface
  - owner: ai
  - created_at: 2026-04-25
  - finished_at: 2026-04-25
  - phase: Cross-cutting
  - scope: Keep the bundled example-site runner aligned with the current primary wrapper surface so
    a resumed example run exercises more than ingest-plus-comments.
  - acceptance:
    - `tests/example/run_example_site.sh` runs the canonical repo-root wrappers for ingest,
      overview generation, comment generation, and profile generation.
    - Example-runner resume state tracks the added overview/profile phases.
    - Bundle docs and contract tests describe the updated flow.
  - evidence: Updated `tests/example/run_example_site.sh` so the resumable example flow now runs
    `generate_overview.sh` after ingest and `generate_profiles.sh` after comments, with
    `OVERVIEW_INDEX` and `PROFILE_INDEX` persisted in the runner status file. Updated
    `tests/example/README.md` to describe the broader run surface and resume behavior, and
    expanded `tests/unit/contracts/test_example_bundle_contract.py` to lock wrapper usage plus the
    added overview/profile resume state. Focused validation passed via the example-bundle contract
    suite.
