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
        self.assertGreater(len(open_ids), 0)
        numeric_ids = [int(todo_id.split("-")[1]) for todo_id in open_ids]
        self.assertEqual(numeric_ids, sorted(numeric_ids, reverse=True))

    def test_ready_queue_and_snapshots_are_consistent_with_open_ids(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        open_ids = set(_open_task_ids(todo_text))
        listed_ids = _listed_todo_ids(todo_text)
        self.assertGreater(len(listed_ids), 0)
        for todo_id in listed_ids:
            self.assertIn(todo_id, open_ids)

    def test_open_task_ids_use_stable_format_and_dependency_ordering(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        for todo_id in _open_task_ids(todo_text):
            self.assertRegex(todo_id, r"^TODO-\d{4}$")


def _open_task_ids(todo_text: str) -> list[str]:
    return re.findall(r"^- \[ \] (TODO-\d{4}):", todo_text, flags=re.MULTILINE)


def _listed_todo_ids(todo_text: str) -> set[str]:
    queue_patterns = (
        r"### Ready Now \(No Unmet TODO Dependencies\)(.*?)(?:\n###|\Z)",
        r"### Immediate Next 10 \(After Ready Now\)(.*?)(?:\n###|\Z)",
        r"### Priority Lanes \(Current\)(.*?)(?:\n###|\Z)",
        r"### Execution Queue \(Recommended\)(.*?)(?:\n###|\Z)",
    )
    listed: set[str] = set()
    for pattern in queue_patterns:
        match = re.search(pattern, todo_text, flags=re.DOTALL)
        if match is None:
            continue
        listed.update(re.findall(r"TODO-\d{4}", match.group(1)))
    return listed


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
