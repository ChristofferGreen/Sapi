# Sapi Reconstruction Tracker

Status: active phase/slice tracker for recovered reconstruction plan execution.

Purpose:
- keep MVP Slice A/B checkpoints visible in one place
- keep Phase 1-6 entry/exit gates mapped to TODO IDs
- keep deferred-build backlog and current phase-gate blockers explicit

## MVP Slices

### MVP Slice A (core vertical slice)

Entry Criteria (TODO-linked):
- bootstrap and wrapper baseline available (`TODO-0200`, `TODO-0209`)
- ingest canonical write path and relation contracts landed (`TODO-0210`, `TODO-0211`, `TODO-0213`)
- deterministic site build/projection baseline landed (`TODO-0216`)

Exit Criteria (TODO-linked):
- first full one-source vertical slice gates enforced (`TODO-0260`)
- query core contracts are landed for the slice (`TODO-0220`)
- no deferred-build backlog for Slice A verification runs (`TODO-0260`)

Current Checkpoint:
- status: complete
- closed by: `TODO-0220`, `TODO-0260`

### MVP Slice B (core hardening before social)

Entry Criteria (TODO-linked):
- Slice A exit gates passed (`TODO-0260`)
- core query contracts and output-shape hardening in place (`TODO-0259`, `TODO-0255`, `TODO-0277`)

Exit Criteria (TODO-linked):
- Slice B reliability/determinism/operator-usability gates enforced (`TODO-0261`)
- test and CI gates wired for required tiers (`TODO-0230`, `TODO-0263`)

Current Checkpoint:
- status: complete
- closed by: `TODO-0230`, `TODO-0263`, `TODO-0261`

## Phases

### Phase 1: Skeleton and contracts

Entry Criteria (TODO-linked):
- reconstruction baseline and contract index tasks are available (`TODO-0102`, `TODO-0200`)

Exit Criteria (TODO-linked):
- package topology and bootstrap wrappers/contracts are complete (`TODO-0201`, `TODO-0209`, `TODO-0235`)

Current Checkpoint:
- status: complete
- closed by: `TODO-0201`, `TODO-0209`, `TODO-0235`

### Phase 2: Ingest and core records

Entry Criteria (TODO-linked):
- Phase 1 contract/layout baseline complete (`TODO-0201`, `TODO-0209`)

Exit Criteria (TODO-linked):
- ingest semantic and canonical relation/reference contracts complete (`TODO-0210`, `TODO-0211`, `TODO-0212`, `TODO-0213`, `TODO-0214`)

Current Checkpoint:
- status: complete
- closed by: `TODO-0210`, `TODO-0211`, `TODO-0212`, `TODO-0213`, `TODO-0214`

### Phase 3: Projection and static site

Entry Criteria (TODO-linked):
- canonical ingest outputs available for projection/build (`TODO-0210`, `TODO-0212`)

Exit Criteria (TODO-linked):
- section-8 renderer/information-architecture contracts complete (`TODO-0253`, `TODO-0257`, `TODO-0234`, `TODO-0233`)

Current Checkpoint:
- status: pending
- blocking TODOs: `TODO-0253`, `TODO-0257`, `TODO-0234`, `TODO-0233`

### Phase 4: Query and core evaluation

Entry Criteria (TODO-linked):
- deterministic build/rebuild baseline complete (`TODO-0216`, `TODO-0217`)

Exit Criteria (TODO-linked):
- query core, mode defaults, truncation, artifact modes, and result-shape contracts complete (`TODO-0220`, `TODO-0259`, `TODO-0255`, `TODO-0221`, `TODO-0277`)

Current Checkpoint:
- status: pending
- blocking TODOs: `TODO-0220`, `TODO-0259`, `TODO-0255`, `TODO-0221`, `TODO-0277`

### Phase 5: Social subsystem

Entry Criteria (TODO-linked):
- query core pipeline contract available for downstream social workflows (`TODO-0220`)

Exit Criteria (TODO-linked):
- comments/personas/profiles/quality contracts complete (`TODO-0222`, `TODO-0258`, `TODO-0248`, `TODO-0249`, `TODO-0256`, `TODO-0224`, `TODO-0275`, `TODO-0266`, `TODO-0225`)

Current Checkpoint:
- status: pending
- blocking TODOs: `TODO-0222`, `TODO-0258`, `TODO-0248`, `TODO-0249`, `TODO-0256`, `TODO-0224`, `TODO-0275`, `TODO-0266`, `TODO-0225`

### Phase 6: Hardening

Entry Criteria (TODO-linked):
- social and query core contracts are landed (`TODO-0220`, `TODO-0224`)

Exit Criteria (TODO-linked):
- hardening gates and DoD closure checks complete (`TODO-0254`, `TODO-0228`, `TODO-0229`, `TODO-0230`, `TODO-0263`, `TODO-0260`, `TODO-0261`, `TODO-0250`, `TODO-0231`)

Current Checkpoint:
- status: pending
- blocking TODOs: `TODO-0254`, `TODO-0228`, `TODO-0229`, `TODO-0230`, `TODO-0263`, `TODO-0250`, `TODO-0231`

## Deferred-Build Backlog

Current Snapshot:
- expected backlog source: runs marked `build_deferred: true` from ingest bootstrap windows
- tracking gate TODO IDs: `TODO-0260`, `TODO-0263`, `TODO-0231`
- current policy checkpoint: backlog must be zero before Slice A/DoD exit gates can close

Operator Verification Hook:
- record latest deferred-build audit result and timestamp here once automated gate checks are wired by `TODO-0260`/`TODO-0263`.

## Phase Gate Blockers

Open gate blockers (by priority lane):
- query core gate: `TODO-0220`, `TODO-0259`, `TODO-0255`, `TODO-0221`, `TODO-0277`
- social subsystem gate: `TODO-0222`, `TODO-0224`, `TODO-0256`, `TODO-0275`, `TODO-0266`, `TODO-0225`
- hardening and release gate: `TODO-0254`, `TODO-0228`, `TODO-0229`, `TODO-0230`, `TODO-0263`, `TODO-0250`, `TODO-0231`
