# Sapi Reconstruction Testing Checklist

Status: implementation checklist for rebuilding from `docs/design.md` and `docs/low_level.md`.

## 1. Scope

This file turns the architecture/testing strategy into concrete test tasks with explicit module targets.

Legend:
- `[ ]` not started
- `[~]` in progress
- `[x]` done

## 2. Proposed Test Module Layout

```text
tests/
  unit/
    contracts/
      test_registry_paths.py
      test_id_contracts.py
    semantic/
      test_spec_resolution.py
      test_retry_budget.py
    lint/
      test_warning_budget_gate.py
    query/
      test_query_mode_preflight.py
  integration/
    failure/
      test_semantic_repair_exhaustion_rollback.py
      test_postprocess_failure_rollback.py
      test_run_container_not_persisted.py
    pipelines/
      test_ingest_pipeline.py
      test_ingest_source_only.py
      test_ingest_force_mode.py
      test_query_pipeline_outputs.py
      test_comments_pipeline.py
      test_profiles_pipeline.py
    build/
      test_build_determinism.py
      test_site_new_refresh_policy.py
      test_incremental_vs_full_equivalence.py
    wrappers/
      test_wrapper_alias_normalization.py
      test_wrapper_alias_conflicts.py
      test_bootstrap_registry_exception.py
      test_evaluate_source_harness.py
  golden/
    test_site_snapshot.py
    test_query_snapshot.py
    test_run_envelope_snapshot.py
  live/
    test_live_llm_canary.py
  conftest.py
```

## 3. Tiered Checklist

### Tier 0: Harness and Fixtures (foundation)

- [ ] Add site/space temp fixture factory with isolated registries.
  - Module: `tests/conftest.py`
- [ ] Add deterministic mock LLM fixture with modes: valid, invalid-then-repair, repair-exhausted.
  - Module: `tests/conftest.py`
- [ ] Add common assertions/helpers for `run.md`, `lint.json`, and rollback cleanup.
  - Module: `tests/conftest.py`

### Tier 1: Core Contract Unit Tests (fast PR gate)

- [x] Registry path resolution, relative `space_root`, and no implicit fallback.
  - Module: `tests/unit/contracts/test_registry_paths.py`
- [x] ID/format/path contract checks used by writes (including suffix-length and timestamp-format constraints).
  - Module: `tests/unit/contracts/test_id_contracts.py`
- [x] Semantic spec flow-map resolution, version pinning, and input alias normalization.
  - Module: `tests/unit/semantic/test_spec_resolution.py`
- [x] Retry budget math and attempt counting (`max_repair_loops`, `max_attempts`, `llm_attempt_count`).
  - Module: `tests/unit/semantic/test_retry_budget.py`
- [x] Warning-threshold (`--warning-budget`) and status mapping behavior.
  - Module: `tests/unit/lint/test_warning_budget_gate.py`
- [x] Query preflight mode checks (`strict + include-disputed` invalid).
  - Module: `tests/unit/query/test_query_mode_preflight.py`
- [x] Run-envelope semantic flow cardinality (`semantic_flows` ordered-unique + `semantic_flow_invocation_counts` consistency).
  - Module: `tests/unit/contracts/test_run_envelope_semantic_flows.py`

### Tier 2: Failure-Semantics Integration Tests

- [x] Repair-loop exhaustion causes terminal failure + rollback.
  - Module: `tests/integration/failure/test_semantic_repair_exhaustion_rollback.py`
- [x] Deterministic post-processing failure rolls back invocation-scoped writes.
  - Module: `tests/integration/failure/test_postprocess_failure_rollback.py`
- [x] Default-mode failed runs leave no committed `runs/<run_id>/` container.
  - Module: `tests/integration/failure/test_run_container_not_persisted.py`

### Tier 3: Pipeline Integration Tests (mock LLM, deterministic)

- [x] Ingest happy path writes canonical artifacts + run/lint metadata.
  - Module: `tests/integration/pipelines/test_ingest_pipeline.py`
- [x] Ingest `--source-only` keeps `semantic_flows=[]` and skips semantic writes.
  - Module: `tests/integration/pipelines/test_ingest_source_only.py`
- [x] Ingest `--force` preserves partial artifacts on terminal failure and marks run metadata (`force_mode=true`, `rollback_skipped=true`).
  - Module: `tests/integration/pipelines/test_ingest_force_mode.py`
- [x] Query output-mode behavior (`markdown` vs artifact manifest modes).
  - Module: `tests/integration/pipelines/test_query_pipeline_outputs.py`
- [x] Comments flow target defaults, count bounds, per-page semantic artifact pathing, merge stability (`comment_uid`), evidence snapshot contract.
  - Module: `tests/integration/pipelines/test_comments_pipeline.py`
- [x] Profiles flow writes profile JSON + history + run/lint metadata.
  - Module: `tests/integration/pipelines/test_profiles_pipeline.py`
- [x] `evaluate_source.sh` default run emits required markdown artifact pack + manifest linkage.
  - Module: `tests/integration/wrappers/test_evaluate_source_harness.py`
- [x] `evaluate_source.sh --comments <n>` emits `comments_review.md`; invalid comments args fail fast with clear errors.
  - Module: `tests/integration/wrappers/test_evaluate_source_harness.py`

### Tier 4: Build/Projection Determinism Tests

- [ ] Full deterministic rebuild consistency checks.
  - Module: `tests/integration/build/test_build_determinism.py`
- [ ] Site-root `New` refresh policy per flow.
  - Module: `tests/integration/build/test_site_new_refresh_policy.py`
- [ ] Incremental output equivalence with full rebuild output.
  - Module: `tests/integration/build/test_incremental_vs_full_equivalence.py`

### Tier 5: Golden Snapshot Tests

- [ ] Site page snapshot coverage for core navigation/content contracts.
  - Module: `tests/golden/test_site_snapshot.py`
- [ ] Query artifact snapshot coverage for key output modes.
  - Module: `tests/golden/test_query_snapshot.py`
- [ ] Run-envelope snapshot coverage for all pipelines.
  - Module: `tests/golden/test_run_envelope_snapshot.py`

### Tier 6: Live LLM Canary (non-blocking)

- [ ] Minimal real-backend smoke test for end-to-end integration drift detection.
  - Module: `tests/live/test_live_llm_canary.py`
  - Mark: `@pytest.mark.live_llm` and exclude from default PR runs.

## 4. CI Gating Matrix

- PR required:
  - Tier 1
  - Tier 2
  - Tier 3
- PR optional/slower:
  - Tier 4
- Nightly:
  - Tier 4
  - Tier 5
  - Tier 6

## 5. Suggested Pytest Commands

```bash
# fast PR contract suite
pytest -q tests/unit tests/integration/failure tests/integration/pipelines -m "not live_llm"

# determinism and golden (slower)
pytest -q tests/integration/build tests/golden -m "not live_llm"

# live canary (manual/nightly only)
pytest -q tests/live -m "live_llm"
```

## 6. Exit Criteria

- [ ] All PR-required tiers are green on CI.
- [ ] No rollback/leakage regressions in failure tests.
- [ ] Ingest `--force` behavior validated without regressing default rollback behavior.
- [ ] No deferred-build backlog before final DoD verification.
- [ ] Deterministic equivalence checks pass for build outputs.
