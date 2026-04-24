from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TODO_DOC_PATH = REPO_ROOT / "docs" / "todo.md"
TODO_FINISHED_DOC_PATH = REPO_ROOT / "docs" / "todo_finished.md"


class CompatibilityPurgeTrackerClosureTests(unittest.TestCase):
    def test_todo_0313_is_no_longer_open_or_listed_in_queue_sections(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        self.assertNotIn("- [ ] TODO-0313:", todo_text)
        open_tasks_section = todo_text[todo_text.index("## Open Tasks") :]
        self.assertNotIn("TODO-0313", open_tasks_section)

    def test_todo_0313_finished_block_records_leaf_task_handoff(self) -> None:
        finished_block = _task_block(
            TODO_FINISHED_DOC_PATH.read_text(),
            todo_id="TODO-0313",
        )
        self.assertIn("TODO-0314..TODO-0327", finished_block)
        self.assertIn("Ready Now", finished_block)
        self.assertIn("coverage snapshots", finished_block)


def _task_block(text: str, *, todo_id: str) -> str:
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


if __name__ == "__main__":
    unittest.main()
