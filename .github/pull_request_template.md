## Summary

- [ ] Describe the user-visible behavior change (or state no behavior change).
- [ ] Link TODO IDs touched by this PR.

## Pipeline Change Checklist (required when pipeline-affecting files change)

- [ ] Q1 Which canonical artifacts can this command mutate?
- [ ] Q2 Which semantic flow keys can run, and in what order?
- [ ] Q3 What exactly is rolled back on terminal failure?
- [ ] Q4 Does run envelope include correct `flow_key`, ordered-unique `semantic_flows[]`, `semantic_flow_invocation_counts`, and required extension fields?
- [ ] Q5 Are manifest outputs conditional by query format as required?
- [ ] Q6 Are comments default-target rules, count bounds, and `comment_uid` stability preserved?
- [ ] Q7 Are profile/history links canonical in rendered output?
- [ ] Q8 Are site-root `New` refresh decisions correct for this flow?
- [ ] Docs Sync: Contract-level changes follow `design.md` -> `low_level.md` -> code/tests order.

## Test Evidence

- [ ] List unit/integration test commands run and outcomes.
