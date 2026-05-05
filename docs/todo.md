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

1. TODO-0378

### Immediate Next 10 (After Ready Now)

1. TODO-0379
2. TODO-0380
3. TODO-0381
4. TODO-0382
5. TODO-0383
6. TODO-0388
7. TODO-0384
8. TODO-0385
9. TODO-0386
10. TODO-0387

### Priority Lanes (Current)

- P0 Foundation/contracts: TODO-0378, TODO-0379
- P1 Core product behavior: TODO-0380, TODO-0381, TODO-0382, TODO-0383, TODO-0388, TODO-0384, TODO-0385
- P2 Social/eval/hardening: TODO-0386
- P3 Continuous docs governance: TODO-0387

### Execution Queue (Recommended)

Wave A (bootstrap + contracts):
1. TODO-0378
2. TODO-0379

Wave B (ingest + projection + lint):
1. TODO-0380
2. TODO-0381
3. TODO-0382
4. TODO-0383
5. TODO-0388
6. TODO-0384
7. TODO-0385

Wave C (query + social + hardening + release):
1. TODO-0386

Wave D (space/subspace AI overview article):
1. (none currently)

Cross-cutting docs backlog:
1. TODO-0387

### Design Coverage Snapshot

| Design area | Primary TODO IDs |
| --- | --- |
| Section 1 (scope/authority/reading) | - |
| Section 2 (runtime policy + semantic loop + mock mode) | TODO-0378, TODO-0381 |
| Section 3 (core concepts + identity invariants) | - |
| Section 4 (repo architecture/spec ownership/versioning/capability boundaries) | TODO-0378, TODO-0379, TODO-0380 |
| Section 5 (paths/storage/IDs/registry/metadata/lint contracts) | TODO-0378, TODO-0379, TODO-0380, TODO-0384 |
| Section 6 (wrapper UX + wrapper-to-entrypoint contract) | TODO-0382, TODO-0383, TODO-0384, TODO-0388 |
| Section 7.1 ingest pipeline | TODO-0383, TODO-0384, TODO-0388 |
| Section 7.2 references/linking | - |
| Section 7.3 query pipeline | - |
| Section 7.4 persona catalog | - |
| Section 7.5 profile pages/history | - |
| Section 7.6 comments pipeline/rendering | - |
| Section 7.7 comment quality harness | - |
| Section 8 site/UI/static build | TODO-0385 |
| Section 9 observability/safety/runtime controls | TODO-0381, TODO-0382, TODO-0383, TODO-0384 |
| Section 10 run envelopes/lifecycle status | TODO-0381, TODO-0383, TODO-0384 |
| Section 11 testing strategy | TODO-0386, TODO-0388 |
| Section 12 reconstruction plan | - |
| Section 13 definition of done | - |

### Low-Level Coverage Snapshot

| Low-level area | Primary TODO IDs |
| --- | --- |
| Section 2 (runtime model and flow namespaces) | TODO-0378, TODO-0381 |
| Section 4 (core data types/run envelope types) | TODO-0379, TODO-0381, TODO-0383, TODO-0384 |
| Section 5 (path + registry contracts) | TODO-0378, TODO-0380 |
| Section 6 (semantic execution engine + retry/repair) | TODO-0381 |
| Section 7 (transaction/rollback) | TODO-0382, TODO-0383, TODO-0384 |
| Section 8 (pipeline execution contracts) | TODO-0381, TODO-0382, TODO-0383, TODO-0388 |
| Section 9 (deterministic build/projection) | TODO-0385 |
| Section 10 (relation persistence) | - |
| Section 11 (lint/warning threshold) | - |
| Section 12 (wrapper/script interfaces) | TODO-0382, TODO-0383, TODO-0384, TODO-0388 |
| Section 13 (observability/runtime controls/safety) | TODO-0381, TODO-0383, TODO-0384 |
| Section 14 (anti-drift and PR guardrails) | TODO-0386 |
| Section 15 (test-plan binding) | TODO-0386 |
| Section 16 (change discipline) | TODO-0387 |

### Testing Plan Coverage Snapshot

| Testing plan area | Primary TODO IDs |
| --- | --- |
| Section 2 (test module layout) | TODO-0386, TODO-0388 |
| Tier 0-3 (fast contract/failure/pipeline suites) | TODO-0386, TODO-0388 |
| Tier 4-6 (determinism/golden/live canary) | TODO-0386, TODO-0388 |
| Section 4-5 (CI gating matrix + command wiring) | TODO-0386 |
| Section 6 (exit criteria gating) | - |

### Task Blocks

- [ ] TODO-0388: Wire example-site runner through scouting import
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0383
  - scope: Update the bundled example-site setup flow so it uses the source-scouting wrappers to
    find five candidate papers from a prepared question and then imports those five through the
    scouted-source ingest bridge.
  - acceptance:
    - `tests/example/run_example_site.sh` adds a resumable scouting/import phase that calls
      `scout_sources.sh` with `--count 5` for a configured example prepared question.
    - The runner calls `import_scouted_sources.sh --count 5` and lets that bridge invoke canonical
      `ingest.sh` for the selected public candidates.
    - Runner state tracks scouting/import progress so retries resume without re-scouting or
      re-ingesting already imported candidates.
    - Example fixtures or configuration identify the target space/subspace and `question_id` used
      for scouting without hardcoding hidden assumptions in the shell script.
    - Example-bundle docs and contract tests describe and verify the scouting/import phase.
    - Mock/test execution remains deterministic and auditable; live scouting is only used when the
      example runner is explicitly configured for live LLM operation.

- [ ] TODO-0387: Document source-scouting operator workflow
  - owner: ai
  - created_at: 2026-05-05
  - phase: Cross-cutting
  - depends_on: TODO-0386
  - scope: Add operator-facing docs for using source scouting as a sidecar queue, reviewing
    candidates, importing selected papers, and ingesting restricted sources without exposing source
    files publicly.
  - acceptance:
    - README or docs describe the scouting workflow from prepared question to candidate review to
      import bridge.
    - Docs explain when to use `--restricted-source`, what site output is hidden, and what remains
      visible.
    - Example commands use repo-root wrappers rather than direct Python entrypoints.
    - Docs explicitly state that scouting candidates are recommendations, not canonical ingested
      knowledge artifacts.

- [ ] TODO-0386: Add scouting slice end-to-end verification gates
  - owner: ai
  - created_at: 2026-05-05
  - phase: Cross-cutting
  - depends_on: TODO-0382, TODO-0383, TODO-0385, TODO-0388
  - scope: Add final slice-level verification that the implemented scouting and restricted-source
    workflows compose correctly across wrappers, import bridge, ingest, and deterministic rendering.
  - acceptance:
    - A mock-LLM end-to-end integration test scouts from a prepared question, imports one public
      candidate through the bridge, and verifies the resulting source reaches the deterministic site.
    - A restricted-source end-to-end test ingests a local paper with the restricted flag and verifies
      public download/source-text links remain hidden after rebuild.
    - Example-runner contract coverage verifies the example setup flow scouts five candidates and
      imports five selected public sources through the bridge.
    - Failure coverage proves a failed scouting/import invocation does not create canonical
      `sources/`, `claims/`, `relations/`, or `topics/` artifacts prematurely.
    - Test-plan docs and package-script wiring are updated if the slice adds new test groups or
      validation commands.

- [ ] TODO-0385: Hide restricted source artifacts in deterministic site rendering
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0384
  - scope: Teach deterministic projection and HTML rendering to honor canonical restricted-source
    access metadata by hiding public source-file and source-text views while preserving allowed
    metadata and provenance links.
  - acceptance:
    - Source detail pages omit PDF/download links, raw source artifact links, and extracted
      markdown/source-text displays when `access_policy.public_download=false` or
      `public_source_view=false`.
    - Source/feed/topic/claim pages may still render bibliographic metadata, DOI/landing-page links,
      and canonical claims/evidence according to the documented policy.
    - Renderers avoid broken links and empty restricted-source sections.
    - Deterministic build fails or emits lint errors for malformed source access-policy metadata.
    - Focused build/golden tests cover public-source output and restricted-source output.

- [ ] TODO-0384: Add restricted-source ingest access policy
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0378
  - scope: Add an explicit ingest wrapper/entrypoint flag for operator-supplied non-public papers,
    tentatively `--restricted-source`, and persist canonical access-policy metadata on source
    records and run envelopes.
  - acceptance:
    - `ingest.sh` and `scripts/ingest_source.py` accept the chosen restricted-source flag and
      reject unclear aliases.
    - Restricted-source ingest still requires a real source file or verified PDF input and never
      permits placeholder/binary stand-ins.
    - Source records persist an `access_policy` object that distinguishes public download, public
      source view, reason, DOI/landing URL, and operator responsibility fields.
    - Run metadata records restricted-source mode for audit.
    - Default ingest behavior remains public-source behavior unless the explicit flag is supplied.
    - Unit and wrapper tests cover flag parsing, source-record metadata, and rejection of placeholder
      restricted-source inputs.

- [ ] TODO-0383: Implement scouted-source import bridge to ingest
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0382
  - scope: Add an import bridge that selects `n` eligible scouting candidates and invokes the
    canonical ingest wrapper without making scouting itself a canonical-write ingest mode.
  - acceptance:
    - `import_scouted_sources.sh <site_path> <space_name> [--count n] [--question-id id]`
      selects candidates by status, ranking, duplicate checks, and public-access eligibility.
    - The bridge calls `ingest.sh` rather than Python ingest internals.
    - Candidates with no public PDF are skipped with a clear status unless restricted-source support
      from TODO-0384 is available and explicitly requested.
    - Successful imports write resulting `source_id`, run ID, and ingest status back to the
      scouting queue.
    - Partial import failures preserve completed candidate status updates and report failed
      candidates clearly without corrupting canonical source artifacts.
    - Integration tests cover public-candidate import selection and already-ingested duplicate
      suppression.

- [ ] TODO-0382: Add source-scouting wrappers and operator entrypoints
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0380, TODO-0381
  - scope: Expose the scouting sidecar through repo-root bash wrappers and Python entrypoints that
    follow the existing registry, runtime-flag, tracing, and run-envelope conventions.
  - acceptance:
    - `scout_sources.sh <site_path> <space_name> <question_id> [--count n]` resolves the site
      registry and delegates to `scripts/scout_sources.py`.
    - The entrypoint supports live LLM defaults, explicit `--mock-llm` test mode, runtime controls,
      warning budget, verbose tracing, and clear usage errors.
    - Scouting writes sidecar run metadata under `<site_path>/scouting/...` and does not write
      canonical `sources/`, `claims/`, `relations/`, or `topics/`.
    - Wrapper tests cover argument validation, registry resolution, and no implicit production mock
      mode.
    - Integration tests cover a mock-LLM scouting run that appends candidates for a prepared
      question.

- [ ] TODO-0381: Implement LLM paper-scouting semantic flow
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0379, TODO-0380
  - scope: Add a live LLM-backed source-scouting flow that starts from one prepared question,
    searches for high-quality papers, and returns schema-valid ranked candidate records.
  - acceptance:
    - Scouting uses a checked-in generation spec and schema-conformant JSON output; production
      scouting does not use deterministic candidate generation.
    - The prompt/ranking contract emphasizes clear answer fit, reputable journal or venue, citation
      signal with provider/as-of metadata, public PDF availability, and interestingness rationale.
    - Deterministic post-processing verifies required identifiers, DOI/URL shape, duplicate
      candidates, public-access status, and ranking fields without inventing semantic rationale.
    - Invalid LLM output uses the shared schema-repair path and records attempt counts in scouting
      run metadata.
    - Unit tests cover ranking validation, duplicate candidate normalization, and repair/exhaustion
      behavior.

- [ ] TODO-0380: Implement scouting candidate store and loaders
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0379
  - scope: Add a sidecar persistence layer for per-space, per-question source-scouting candidates
    that remains separate from canonical ingested knowledge artifacts.
  - acceptance:
    - Candidate queues live under `<site_path>/scouting/spaces/<space_name>/questions/<question_id>/`
      or the final documented sidecar path.
    - Loaders validate candidate IDs, question/space ownership, operator status, import status,
      DOI/URL duplicates, access status, ranking fields, and source provenance.
    - Candidate writes are transactional or otherwise rollback-safe for scouting/import
      invocations.
    - The store exposes deterministic selection helpers for top-ranked candidates and importable
      candidates.
    - Unit tests cover candidate loading, status transitions, duplicate DOI/URL handling, and
      selection ordering.

- [ ] TODO-0379: Add scouting schemas and generation specs
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - depends_on: TODO-0378
  - scope: Add checked-in JSON schemas and generation specs for source-scouting candidate output,
    candidate queue records, and any scouting run metadata needed outside canonical source records.
  - acceptance:
    - New schema files define candidate identity, question fit, journal/venue metadata, citation
      metadata, DOI/URL/PDF fields, public-access status, ranking rationale, operator status, and
      ingest linkage.
    - Generation specs declare schema path, output path, context paths, and repair-loop
      instructions consistent with existing semantic-flow contracts.
    - Spec resolution tests cover the new scouting flow without treating it as an ingest semantic
      flow.
    - Contract docs distinguish sidecar scouting artifacts from canonical source/claim/relation/topic
      artifacts.
    - Schema tests reject candidates missing DOI/URL provenance, access status, or ranking rationale.

- [ ] TODO-0378: Define source-scouting and restricted-source contracts
  - owner: ai
  - created_at: 2026-05-05
  - phase: Phase 4
  - scope: Extend the design, low-level design, and testing-plan contracts for a source-scouting
    sidecar plus an explicit restricted-source ingest policy.
  - acceptance:
    - `docs/design.md` defines scouting as a sidecar recommendation system that starts from a
      prepared question and never mutates canonical knowledge artifacts until the import bridge calls
      ingest.
    - Contracts define candidate ranking criteria: answer fit, reputable journal/venue, citation
      count with provenance/as-of date, public PDF availability, and interestingness rationale.
    - Contracts define restricted-source ingest semantics, including the chosen flag name,
      access-policy metadata, hidden public download/source-view behavior, and allowed metadata
      rendering.
    - `docs/low_level.md` assigns module ownership, paths, wrappers, run metadata, rollback behavior,
      and boundary rules for scouting and import.
    - `docs/testing_plan.md` identifies required unit, integration, build/golden, and live/mock
      coverage for scouting and restricted-source behavior.
