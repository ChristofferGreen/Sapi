# Sapi

Sapi is an LLM-driven knowledge graph and static site system.

It ingests sources into spaces, derives claims/relations via semantic generation, builds topic/query artifacts, renders a deterministic static web experience, and supports persona-based discussion/profile flows.

## Current Status

This repository is in reconstruction mode.

- code was lost
- design contracts were recovered
- implementation should follow docs-first reconstruction

Start with:

- [docs/contract_index.md](/Users/chrgre01/src/Sapi/docs/contract_index.md)
- [docs/design.md](/Users/chrgre01/src/Sapi/docs/design.md)
- [docs/low_level.md](/Users/chrgre01/src/Sapi/docs/low_level.md)
- [docs/testing_plan.md](/Users/chrgre01/src/Sapi/docs/testing_plan.md)

Python runtime dependencies:

- `python3 -m pip install -r requirements.txt`

## Product Model

Primary entities:

- Site
- Space
- Source
- Claim
- Relation
- Topic page
- Persona/profile
- Comment thread

High-level user flow:

1. create a site
2. create one or more spaces
3. ingest sources
4. build deterministic projections/site
5. run queries
6. optionally generate comments and persona profiles
7. validate/lint contracts

## Non-Negotiable Runtime Principles

From the recovered design contracts:

- semantic generation in operator/production mode is LLM-driven
- deterministic semantic fallback is not allowed in normal operation
- semantic outputs must validate against checked-in JSON schemas
- invalid semantic outputs use a schema-repair retry loop
- static build/projection stages are deterministic and must not call LLMs
- pipeline behavior is driven by CLI args, not environment variables

Notable ingest behavior:

- default terminal-failure behavior is rollback of invocation-scoped writes
- explicit `--force` in ingest may preserve partial artifacts on failure for forensics
- ingest extraction may persist a reader-facing `source_dossier` (short + long summaries and sectioned
  commentary) that the source detail page renders for users who want substance before opening the PDF
- ingest extraction also emits canonical `evidence_items[]` (LLM-authored IDs/titles/excerpts/link refs),
  which are persisted under `<space_root>/evidence/` and drive evidence pages without deterministic synthesis

## Target Wrapper Interface

Canonical operator wrappers (target interface during reconstruction):

- `create_site.sh <site_path> <site_name>`
- `create_space.sh <site_path> <space_name>`
- `create_questions.sh <site_path> <questions_tsv> [space_name]`
- `ingest.sh <site_path> <space_name> <source_path_or_url> [--revises-source-id <source_id>] [--force] [--verbose]`
- `query.sh <site_path> <space_name> <question> [--verbose]`
- `create_comments.sh <site_path> <space_name> --count <n> [--verbose] [...]`
- `generate_profiles.sh <site_path> <space_name> [--persona-id <persona_id> ...] [--verbose]`
- `regenerate_web.sh <site_path> [space_name] [--verbose]`
- `validate.sh <site_path> <space_name> [--workflow ...] [--run-id ...]`

Persona image generation utility:

- `python3 scripts/generate_profile_images.py [--persona-id <persona_id> ...] [--model imagen-4.0-generate-001] [--verbose]`
- requires `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in environment
- reads prompts from `personas/social_users.json` (`profile_image_prompt`) and writes `.jpg` profile photos plus smaller `-thumb.jpg` avatar companions under `personas/profile_images/`

Registry rule:

- non-bootstrap commands use explicit `--registry-path <site_path>/spaces.toml`

Runtime/control flag defaults and forwarding:

- semantic wrappers/entrypoints expose and forward common runtime controls:
  `--llm-backend`, `--llm-model`, `--llm-reasoning-effort`, `--llm-timeout-secs`,
  `--llm-trace`, `--llm-trace-dir`, `--trace-llm-io`, `--mock-llm`, `--warning-budget`,
  `--run-search-visibility`, `--site-presentation-mode`, `--enable-source-index`.
- defaults:
  - `--llm-backend codex`
  - `--llm-model` from `config/llm.json` (`default_live_model`)
  - `--llm-reasoning-effort` from `config/llm.json` (`default_live_reasoning_effort`)
  - `--llm-timeout-secs none`
  - `--warning-budget 200`
- invalid tracing combination guard:
  - `--llm-trace-dir` requires one of `--llm-trace`, `--trace-llm-io`, or `--verbose`.

## Architecture and Contracts

The project is contract-first. `docs/design.md` is authoritative for:

- runtime semantics
- storage and ID contracts
- pipeline behavior
- run metadata envelopes

`docs/low_level.md` provides implementation-level structure:

- package/module topology
- shared semantic executor behavior
- transaction/rollback design
- pipeline control flow and preflight checks
- observability and safety implementation guidance

## Testing Strategy

The canonical testing checklist is:

- [docs/testing_plan.md](/Users/chrgre01/src/Sapi/docs/testing_plan.md)

It defines:

- tiered test suites (unit, failure semantics, pipeline integration, determinism, golden, live canary)
- proposed test module layout under `tests/`
- CI gating expectations
- explicit exit criteria for reconstruction quality

## Change Discipline

When behavior changes are required:

1. update [docs/design.md](/Users/chrgre01/src/Sapi/docs/design.md) for contract-level changes
2. update [docs/low_level.md](/Users/chrgre01/src/Sapi/docs/low_level.md) for implementation-level implications
3. then implement code and tests

This order prevents architecture drift during reconstruction.
