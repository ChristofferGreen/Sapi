# AGENTS

## Runtime Notes

- Transient Codex reconnection warnings/errors are expected in this environment and are usually self-resolving.
- Do not treat reconnect messages alone as a hard failure; wait for final command status before retrying.
- Do not create new git branches, worktrees, or other workspace forks unless the user explicitly asks for it.
- For actual operator use, prefer the repo-root bash helper scripts (`create_site.sh`, `create_space.sh`,
  `create_subspaces.sh`, `create_questions.sh`, `refresh_questions.sh`, `ingest.sh`, `create_comments.sh`,
  `generate_profiles.sh`, `generate_overview.sh`, `query.sh`, `regenerate_web.sh`, `validate.sh`,
  `evaluate_source.sh`) over calling Python entrypoints in `scripts/` directly.
- Call Python entrypoints in `scripts/` directly only when no bash helper exists yet or when working on tests,
  internals, or wrapper implementation itself.

## Generation Policy

- Never generate user-facing content via deterministic code paths, templates, or mock/scaffold generators.
- Ingest requests for journal articles must ingest real journal-article PDFs (verified as actual PDFs), not
  placeholder/binary stand-ins.
- Always generate user-facing semantic content via live Codex/OpenAI LLM flows that return
  schema-conformant JSON.
- If an ingest or LLM generation step fails, fix the failure cause and retry the same live flow; do not bypass
  failures by switching to deterministic/mock generation for user-facing output.

## Commit Message Rules

Use this format for every commit:

```text
<type>(<scope>): <subject>

<body>

Refs: TODO-XXXX
```

### 1) Subject line

- Keep it under 72 characters.
- Use imperative mood (`add`, `fix`, `refactor`, `remove`), not past tense.
- Start lowercase after `:`.
- Describe behavior/change, not process.
- Do not end with a period.

### 2) Allowed `type` values

- `feat`: new user-visible behavior
- `fix`: bug fix or contract-correction
- `refactor`: internal restructuring with no behavior change
- `test`: tests only
- `docs`: docs only
- `chore`: tooling/build/maintenance

### 3) Scope

- Use a real subsystem, e.g. `ingest`, `query`, `comments`, `profiles`, `build`, `lint`, `docs`, `wrappers`.
- Keep scope stable across commits for the same area.

### 4) Body requirements

- Explain why the change is needed (context/problem).
- List key behavioral changes and important non-changes.
- Mention risks, migrations, or compatibility impact when relevant.
- Use real line breaks in commit bodies; do not write escaped `\n` sequences.
- Wrap body lines at ~100 chars.

### 5) Traceability

- Include at least one backlog reference: `Refs: TODO-XXXX`.
- If closing an item completely, use `Closes: TODO-XXXX`.
- If multiple TODOs are touched, list each explicitly.

### 6) Commit hygiene

- One logical change per commit.
- Do not mix unrelated refactors with behavior changes.
- Do not commit failing tests unless explicitly marked as intentional in body.
- Never use vague subjects like `update`, `stuff`, `fixes`.

### Good examples

- `feat(query): add deterministic manifest writer for slide output`
- `fix(ingest): enforce source-only semantic flow suppression`
- `test(comments): cover turn-marker normalization edge cases`
- `docs(todo): split query result-shape contract into explicit task`
