# Repository Memories

This file stores durable session-derived facts that are useful in later work. Keep it short, factual, and easy to diff.

## Active Memories

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
