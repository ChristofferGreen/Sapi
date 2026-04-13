# Sapi Prompt Library (ChatGPT Codex)

This file contains 3 reusable prompts for working against `docs/todo.md`.

## Prompt 1: Implement A TODO Item

```text
Do not use or follow any external skills, skill files, or preset workflows; follow only this prompt and the repository docs it references.

Implement a todo item from `docs/todo.md` completely.

Requirements:
- Read in order: `docs/todo.md`, `docs/design.md`, `docs/low_level.md`, `docs/testing_plan.md`, `README.md`.
- Treat `docs/design.md` as contract authority.
- Make minimal, focused code changes tied to this TODO and direct dependencies.
- Add/update tests to prove each acceptance criterion.
- Make a commit when the todo item is finished.

Output format:
Implementation summary (file-by-file).
```

## Prompt 2: Verify Testing Quality And Coverage For A TODO

```text
You are a test-validation agent in `/Users/chrgre01/src/Sapi`.
Do not use or follow any external skills, skill files, or preset workflows; follow only this prompt and the repository docs it references.

Audit whether testing is sufficient for `TODO-<ID>` (or a specified change set).

Requirements:
- Read: `docs/todo.md`, `docs/testing_plan.md`, relevant sections of `docs/design.md`, and changed code/tests.
- Check that tests cover happy path, failure path, contract validation, and regression risk.
- Identify weak assertions, missing edge cases, flaky patterns, and untested acceptance criteria.
- Implement missing tests where needed.
- Run relevant test commands and report outcomes.

Output format:
1. Findings first, ordered by severity.
2. Test changes made (file-by-file).
3. Coverage of acceptance criteria (covered/partial/missing).
4. Commands run and results.
5. Residual risk list.
```

## Prompt 3: Find Problems (Code Review / Risk Hunt)

```text
You are a review agent in `/Users/chrgre01/src/Sapi`.
Do not use or follow any external skills, skill files, or preset workflows; follow only this prompt and the repository docs it references.

Review implementation for `TODO-<ID>` (or a specified diff) and find concrete problems.

Review focus:
- Correctness bugs and contract violations against `docs/design.md` / `docs/low_level.md`.
- Behavioral regressions and missing error handling.
- Data integrity/path/ID/time-format mistakes.
- Missing or insufficient tests.
- Determinism and rollback/safety issues where relevant.

Requirements:
- Prefer evidence-backed findings with file/line references.
- Prioritize high-severity issues first.
- If no issues are found, explicitly say so and list residual risks/test gaps.

Output format:
1. Findings (severity-ordered) with file/line references.
2. Open questions/assumptions.
3. Brief overall risk assessment.
```
