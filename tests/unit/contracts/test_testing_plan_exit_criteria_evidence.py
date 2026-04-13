from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTING_PLAN_PATH = REPO_ROOT / "docs" / "testing_plan.md"
TODO_FINISHED_PATH = REPO_ROOT / "docs" / "todo_finished.md"


class TestingPlanExitCriteriaEvidenceTests(unittest.TestCase):
    def test_section6_exit_criteria_are_checked_with_linked_evidence_lines(self) -> None:
        section = _section_text(TESTING_PLAN_PATH.read_text(), "## 6. Exit Criteria")
        self.assertNotIn("- [ ]", section)

        lines = section.splitlines()
        checklist_indices = [idx for idx, line in enumerate(lines) if line.startswith("- [x] ")]
        self.assertEqual(len(checklist_indices), 5)

        for idx in checklist_indices:
            self.assertLess(idx + 1, len(lines), msg=f"Missing evidence line after: {lines[idx]}")
            evidence_line = lines[idx + 1]
            self.assertTrue(
                evidence_line.startswith("  - Evidence: "),
                msg=f"Expected linked evidence line after checklist item: {lines[idx]}",
            )
            self.assertRegex(evidence_line, r"\[[^\]]+\]\([^)]+\)")
            self.assertIn("`", evidence_line, msg="Evidence line must include a concrete command reference.")

        self.assertIn("./verification/testing_exit_criteria.latest.json", section)
        self.assertIn("./verification/testing_exit_criteria.latest/manifest.json", section)

    def test_todo_0312_completion_evidence_references_exit_gate_artifacts(self) -> None:
        block = _task_block(TODO_FINISHED_PATH.read_text(), "TODO-0312")
        self.assertIn("docs/testing_plan.md", block)
        self.assertIn("verify_testing_exit_criteria.py", block)
        self.assertIn("docs/verification/testing_exit_criteria.latest.json", block)
        self.assertIn("docs/verification/testing_exit_criteria.latest/manifest.json", block)


def _section_text(text: str, heading: str) -> str:
    start = text.index(heading)
    next_h2 = text.find("\n## ", start + 1)
    if next_h2 == -1:
        next_h2 = len(text)
    return text[start:next_h2]


def _task_block(todo_finished_text: str, todo_id: str) -> str:
    marker = f"- [x] {todo_id}:"
    lines = todo_finished_text.splitlines()
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
