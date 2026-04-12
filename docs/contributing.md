# Contributing Guide

## Pipeline-Change Review Checklist

Pipeline-affecting pull requests must answer all eight review questions from the low-level contract:

1. Which canonical artifacts can this command mutate?
2. Which semantic flow keys can run, and in what order?
3. What exactly is rolled back on terminal failure?
4. Does run envelope include correct `flow_key`, ordered-unique `semantic_flows[]`,
   `semantic_flow_invocation_counts`, and required extension fields?
5. Are manifest outputs conditional by query format as required?
6. Are comments default-target rules, count bounds, and `comment_uid` stability preserved?
7. Are profile/history links canonical in rendered output?
8. Are site-root `New` refresh decisions correct for this flow?

Use the repository PR template (`.github/pull_request_template.md`) to provide checklist evidence.

## Docs-Sync Discipline (Required)

For contract-level behavior changes, updates must happen in this order:

1. Update `docs/design.md` first (contract authority).
2. Update `docs/low_level.md` second (implementation implications).
3. Update code and tests last.

Pipeline-affecting PRs without checklist or docs-sync evidence must fail quality gates.
