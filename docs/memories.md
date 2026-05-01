# Repository Memories

This file stores durable session-derived facts that are useful in later work. Keep it short, factual, and easy to diff.

## Active Memories

### test-pr-scope
- Updated: 2026-05-01
- Tags: tests, workflow
- Fact: `npm run test:pr` runs unit, failure, and pipeline integration suites, but it does not include `tests/integration/wrappers`.
- Evidence: `package.json` defines `test:pr` as `pytest -q tests/unit tests/integration/failure tests/integration/pipelines -m "not live_llm"`, so wrapper changes in this run were verified with an explicit wrapper test invocation.

### tier4-5-scope
- Updated: 2026-05-01
- Tags: tests, workflow
- Fact: `npm run test:tier4-5` is the separate golden/determinism gate and is not covered by `npm run test:pr`.
- Evidence: This run needed `npm run test:tier4-5` to catch stale run-envelope goldens and a site-root `New` refresh policy regression after the PR gate passed.

### validation-entrypoint
- Updated: 2026-04-27
- Tags: tests, workflow
- Fact: This repo does not have `./scripts/compile.sh`; the practical PR validation command is `npm run test:pr`.
- Evidence: `./scripts/compile.sh --release` failed with "No such file or directory", and `npm run test:pr` is the package-script gate that passed for this change.

## Maintenance Notes
- Keep entries sorted by slug within the section.
- Delete wrong entries instead of leaving contradictory facts behind.
- Prefer updating an existing entry over adding a near-duplicate.
- Avoid copying obvious facts from `AGENTS.md` or canonical design docs unless the shorter memory adds unique operational value.
