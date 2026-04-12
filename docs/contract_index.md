# Sapi Cross-Document Contract Index

Purpose: provide one fast lookup table for where each contract is authoritative.

Rules:
- `docs/design.md` is the default contract authority.
- `docs/low_level.md` is authoritative only where `design.md` explicitly delegates (module/package topology).
- `docs/testing_plan.md` is authoritative for test-tier wiring and exit-gate definitions.

## Canonical Contract Authority Map

| Contract area | Authoritative source | Section pointer | Notes |
| --- | --- | --- | --- |
| Semantic/runtime invariants | [docs/design.md](./design.md) | [Section 2](./design.md#2-non-negotiable-runtime-policy) | LLM-only semantic policy, repair loops, and runtime controls. |
| Filesystem, IDs, registry targeting, lint gates | [docs/design.md](./design.md) | [Section 5](./design.md#5-storage-ids-and-file-contracts) | Canonical paths, ID/time formats, registry, lint severity/gating. |
| Pipeline behavior by subsystem | [docs/design.md](./design.md) | [Section 7](./design.md#7-pipeline-contracts-by-subsystem) | Ingest/query/comments/profiles behavior and boundaries. |
| Run status and output-envelope semantics | [docs/design.md](./design.md) | [Section 10](./design.md#10-run-status-and-output-envelopes) | Run lifecycle vocabulary and required envelope fields. |
| Canonical reconstruction module/package topology | [docs/low_level.md](./low_level.md) | [Section 3](./low_level.md#3-target-package-layout) | Explicitly delegated by `docs/design.md` Section 1.2. |
| Implementation control-flow mechanics (executor, rollback, pipeline state machine) | [docs/low_level.md](./low_level.md) | [Sections 2, 6, 7, 8](./low_level.md#2-runtime-model) | Code-structure-level contracts that refine design behavior. |
| Tiered test module coverage and CI tier mapping | [docs/testing_plan.md](./testing_plan.md) | [Sections 3-4](./testing_plan.md#3-tiered-checklist) | PR/nightly test tiers and module-level coverage checklist. |
| Reconstruction verification exit gates | [docs/testing_plan.md](./testing_plan.md) | [Section 6](./testing_plan.md#6-exit-criteria) | Required quality gates before closure claims. |

## Fast Navigation by Task

| If you need to answer... | Jump to |
| --- | --- |
| "Is this runtime/semantic behavior allowed?" | [docs/design.md §2](./design.md#2-non-negotiable-runtime-policy) |
| "Where does this artifact/ID/path live?" | [docs/design.md §5](./design.md#5-storage-ids-and-file-contracts) |
| "What should ingest/query/comments/profiles do?" | [docs/design.md §7](./design.md#7-pipeline-contracts-by-subsystem) |
| "What must a run envelope contain?" | [docs/design.md §10](./design.md#10-run-status-and-output-envelopes) |
| "Which module should own this code?" | [docs/low_level.md §3](./low_level.md#3-target-package-layout) |
| "Which tests must exist and which tiers gate PRs?" | [docs/testing_plan.md §§3-4](./testing_plan.md#3-tiered-checklist) |
| "Can this milestone be closed yet?" | [docs/testing_plan.md §6](./testing_plan.md#6-exit-criteria) |
