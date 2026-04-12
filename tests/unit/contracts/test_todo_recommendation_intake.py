from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"
TODO_DOC_PATH = REPO_ROOT / "docs" / "todo.md"
TODO_FINISHED_DOC_PATH = REPO_ROOT / "docs" / "todo_finished.md"


class TodoRecommendationIntakeTests(unittest.TestCase):
    def test_unresolved_design_recommendations_have_task_ids(self) -> None:
        todo_text = TODO_DOC_PATH.read_text()
        open_tasks_section = _open_tasks_section(todo_text)
        unresolved_decisions = _unresolved_decision_labels(DESIGN_DOC_PATH.read_text())
        self.assertGreaterEqual(len(unresolved_decisions), 1)

        for label in unresolved_decisions:
            decision_ref = _slugify_for_decision_ref(label)
            self.assertIn(
                f"decision_ref: {decision_ref}",
                open_tasks_section,
                msg=f"missing recommendation intake task for unresolved decision: {label}",
            )

    def test_recommendation_tasks_link_to_authoritative_sections(self) -> None:
        for block in _open_task_blocks(TODO_DOC_PATH.read_text()):
            if "decision_ref:" not in block:
                continue
            self.assertRegex(block, r"^- \[ \] TODO-\d{4}:", msg="missing TODO id in recommendation block")
            self.assertIn("notes: source `design.md` Section", block)
            self.assertIn("acceptance:", block)

    def test_open_tasks_avoid_ambiguous_do_later_placeholders(self) -> None:
        open_tasks_section = _open_tasks_section(TODO_DOC_PATH.read_text())
        self.assertNotRegex(open_tasks_section, r"\bdo later\b", msg="ambiguous 'do later' placeholder found")
        for block in _open_task_blocks(TODO_DOC_PATH.read_text()):
            if "acceptance:" not in block:
                continue
            self.assertNotIn("- ...", block, msg="placeholder acceptance bullet found in open task block")

    def test_todo_0280_completion_records_owner_outcome_path_and_authoritative_sections(self) -> None:
        finished_block = _task_block(
            text=TODO_FINISHED_DOC_PATH.read_text(),
            todo_id="TODO-0280",
            open_task=False,
        )
        self.assertIn("owner: ai", finished_block)
        self.assertIn("Section 1.3", finished_block)
        self.assertIn("Section 4.1.3", finished_block)

        successor_block = _task_block(
            text=TODO_DOC_PATH.read_text(),
            todo_id="TODO-0282",
            open_task=True,
        )
        self.assertIn("owner: human", successor_block)
        self.assertIn("decision_ref: compatibility-reader-sunset-policy-for-legacy-aliases", successor_block)
        self.assertIn("Section 4.1.3", successor_block)

    def test_todo_0281_completion_records_owner_outcome_path_and_authoritative_sections(self) -> None:
        finished_block = _task_block(
            text=TODO_FINISHED_DOC_PATH.read_text(),
            todo_id="TODO-0281",
            open_task=False,
        )
        self.assertIn("owner: ai", finished_block)
        self.assertIn("Section 1.3", finished_block)
        self.assertIn("Section 6.3", finished_block)

        successor_block = _task_block(
            text=TODO_DOC_PATH.read_text(),
            todo_id="TODO-0283",
            open_task=True,
        )
        self.assertIn("owner: ai", successor_block)
        self.assertIn("depends_on: TODO-0281", successor_block)
        self.assertIn("decision_ref: additional-query-modes-in-evaluate-source-sh-default-evaluation-pack", successor_block)
        self.assertIn("Section 6.3", successor_block)


def _open_tasks_section(todo_text: str) -> str:
    start = todo_text.index("## Open Tasks")
    return todo_text[start:]


def _unresolved_decision_labels(design_text: str) -> list[str]:
    start = design_text.index("### 1.3 Decision register")
    end = design_text.find("\n## ", start + 1)
    if end == -1:
        end = len(design_text)
    section = design_text[start:end]

    labels: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 6:
            continue
        decision_label, _options, status, _owner, _due, _final = cells
        if status == "unresolved":
            labels.append(decision_label)
    return labels


def _open_task_blocks(todo_text: str) -> list[str]:
    section = _open_tasks_section(todo_text)
    lines = section.splitlines()
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if re.match(r"^- \[ \] TODO-\d{4}:", line):
            if current:
                blocks.append(current)
            current = [line]
            continue
        if current is not None:
            if line.startswith("- [ ] TODO-"):
                blocks.append(current)
                current = [line]
            else:
                current.append(line)
    if current:
        blocks.append(current)
    return ["\n".join(block) for block in blocks]


def _task_block(*, text: str, todo_id: str, open_task: bool) -> str:
    marker = f"- [{' ' if open_task else 'x'}] {todo_id}:"
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


def _slugify_for_decision_ref(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-{2,}", "-", normalized)


if __name__ == "__main__":
    unittest.main()
