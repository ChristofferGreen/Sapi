from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TODO_DOC_PATH = REPO_ROOT / "docs" / "todo.md"
TODO_FINISHED_DOC_PATH = REPO_ROOT / "docs" / "todo_finished.md"
EXIT_GATE_EVIDENCE_PATH = REPO_ROOT / "verification" / "slice_b_exit_criteria.latest.json"


class SliceBExitGateClosureTests(unittest.TestCase):
    def test_todo_0231_declares_dependency_on_todo_0261(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        if _is_open_todo(todo_text=todo_text, todo_id="TODO-0231"):
            block = _open_task_block(todo_text, todo_id="TODO-0231")
            self.assertIn("depends_on:", block)
            self.assertIn("TODO-0261", block)

    def test_todo_0261_closure_requires_passing_exit_gate_evidence(self) -> None:
        if _is_open_todo(todo_text=TODO_DOC_PATH.read_text(), todo_id="TODO-0261"):
            return

        self.assertTrue(
            EXIT_GATE_EVIDENCE_PATH.is_file(),
            msg=(
                "Closing TODO-0261 requires committed exit-gate evidence at "
                "verification/slice_b_exit_criteria.latest.json."
            ),
        )
        evidence = json.loads(EXIT_GATE_EVIDENCE_PATH.read_text())
        checks = evidence.get("checks")
        self.assertIsInstance(checks, dict)
        self.assertEqual(evidence.get("status"), "success")
        for key in (
            "reliability_determinism_green",
            "ingest_build_query_contracts_green",
            "operator_wrapper_usability_green",
        ):
            self.assertEqual(checks.get(key), True, msg=f"Exit gate check must be true: {key}")

        finished_text = TODO_FINISHED_DOC_PATH.read_text()
        self.assertIn("TODO-0261", finished_text)
        finished_block = _finished_task_block(finished_text, todo_id="TODO-0261")
        self.assertIn("verify_slice_b.py", finished_block)


def _is_open_todo(*, todo_text: str, todo_id: str) -> bool:
    marker = f"- [ ] {todo_id}:"
    return marker in todo_text


def _finished_task_block(text: str, *, todo_id: str) -> str:
    marker = f"- [x] {todo_id}:"
    lines = text.splitlines()
    start_idx: int | None = None
    for idx, line in enumerate(lines):
        if line.startswith(marker):
            start_idx = idx
            break
    if start_idx is None:
        raise AssertionError(f"missing task block for {todo_id}")

    block_lines: list[str] = []
    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        if idx > start_idx and re.match(r"^- \[[ x]\] TODO-\d{4}:", line):
            break
        block_lines.append(line)
    return "\n".join(block_lines)


def _open_task_block(text: str, *, todo_id: str) -> str:
    marker = f"- [ ] {todo_id}:"
    lines = text.splitlines()
    start_idx: int | None = None
    for idx, line in enumerate(lines):
        if line.startswith(marker):
            start_idx = idx
            break
    if start_idx is None:
        raise AssertionError(f"missing open task block for {todo_id}")

    block_lines: list[str] = []
    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        if idx > start_idx and re.match(r"^- \[[ x]\] TODO-\d{4}:", line):
            break
        block_lines.append(line)
    return "\n".join(block_lines)


if __name__ == "__main__":
    unittest.main()
