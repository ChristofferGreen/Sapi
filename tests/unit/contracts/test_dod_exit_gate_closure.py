from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TODO_DOC_PATH = REPO_ROOT / "docs" / "todo.md"
TODO_FINISHED_DOC_PATH = REPO_ROOT / "docs" / "todo_finished.md"
EXIT_GATE_EVIDENCE_PATH = REPO_ROOT / "verification" / "testing_exit_criteria.latest.json"
DOD_EVIDENCE_PATH = REPO_ROOT / "verification" / "dod_verification.latest.json"


class DodExitGateClosureTests(unittest.TestCase):
    def test_todo_0231_closure_requires_passing_exit_gate_evidence(self) -> None:
        if _is_open_todo(todo_text=TODO_DOC_PATH.read_text(), todo_id="TODO-0231"):
            return

        self.assertTrue(
            EXIT_GATE_EVIDENCE_PATH.is_file(),
            msg=(
                "Closing TODO-0231 requires committed exit-gate evidence at "
                "verification/testing_exit_criteria.latest.json."
            ),
        )
        evidence = json.loads(EXIT_GATE_EVIDENCE_PATH.read_text())
        checks = evidence.get("checks")
        self.assertIsInstance(checks, dict)
        self.assertEqual(evidence.get("status"), "success")
        for key in (
            "pr_required_tiers_green",
            "determinism_checks_green",
            "rollback_leakage_regressions_absent",
            "deferred_build_backlog_clear",
        ):
            self.assertEqual(checks.get(key), True, msg=f"Exit gate check must be true: {key}")

        finished_text = TODO_FINISHED_DOC_PATH.read_text()
        self.assertIn("TODO-0231", finished_text)
        finished_block = _finished_task_block(finished_text, todo_id="TODO-0231")
        self.assertIn("verify_testing_exit_criteria.py", finished_block)
        self.assertIn("verify_dod.py", finished_block)

        self.assertTrue(
            DOD_EVIDENCE_PATH.is_file(),
            msg=(
                "Closing TODO-0231 requires committed DoD verification evidence at "
                "verification/dod_verification.latest.json."
            ),
        )
        dod_evidence = json.loads(DOD_EVIDENCE_PATH.read_text())
        self.assertEqual(dod_evidence.get("status"), "success")
        dod_checks = dod_evidence.get("checks")
        self.assertIsInstance(dod_checks, dict)
        self.assertEqual(dod_checks.get("dod_13_1_wrappers_execute_successfully"), True)
        self.assertEqual(dod_checks.get("dod_13_10_no_deferred_build_backlog"), True)


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


if __name__ == "__main__":
    unittest.main()
