from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TODO_DOC_PATH = REPO_ROOT / "docs" / "todo.md"


class Todo0309QueueReconstitutionTests(unittest.TestCase):
    def test_open_task_blocks_are_reconstituted_for_remaining_work(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        open_ids = _open_task_ids(todo_text)
        self.assertEqual(open_ids, ["TODO-0312"])

    def test_ready_queue_and_snapshots_are_consistent_with_open_ids(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        self.assertIn("### Ready Now (No Unmet TODO Dependencies)\n\n1. `TODO-0312`", todo_text)
        self.assertIn("### Immediate Next 10 (After Ready Now)\n\n1. (none currently)", todo_text)
        self.assertIn("Wave A (bootstrap + contracts):\n1. (none currently)", todo_text)
        self.assertIn("Wave C (query + social + hardening + release):\n1. TODO-0312", todo_text)
        self.assertNotIn("TODO-0309:", todo_text)
        self.assertNotIn("TODO-0310:", todo_text)
        self.assertNotIn("TODO-0311:", todo_text)

    def test_open_task_ids_use_stable_format_and_dependency_ordering(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        for todo_id in _open_task_ids(todo_text):
            self.assertRegex(todo_id, r"^TODO-\d{4}$")

        block_0312 = _open_task_block(todo_text, "TODO-0312")
        self.assertIn("depends_on: TODO-0311", block_0312)


def _open_task_ids(todo_text: str) -> list[str]:
    return re.findall(r"^- \[ \] (TODO-\d{4}):", todo_text, flags=re.MULTILINE)


def _open_task_block(todo_text: str, todo_id: str) -> str:
    marker = f"- [ ] {todo_id}:"
    lines = todo_text.splitlines()
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
