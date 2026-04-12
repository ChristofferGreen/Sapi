from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TRACKER_PATH = REPO_ROOT / "docs" / "reconstruction_tracker.md"


class ReconstructionTrackerTests(unittest.TestCase):
    def test_tracker_exists_with_mvp_slice_and_phase_checkpoints(self) -> None:
        self.assertTrue(TRACKER_PATH.is_file())
        text = TRACKER_PATH.read_text()

        self.assertIn("## MVP Slices", text)
        self.assertIn("### MVP Slice A (core vertical slice)", text)
        self.assertIn("### MVP Slice B (core hardening before social)", text)

        for phase_no in range(1, 7):
            self.assertIn(f"### Phase {phase_no}:", text)

    def test_every_phase_has_entry_exit_criteria_tied_to_todo_ids(self) -> None:
        text = TRACKER_PATH.read_text()
        for phase_no in range(1, 7):
            section = _heading_section(text, heading=f"### Phase {phase_no}:")
            self.assertIn("Entry Criteria (TODO-linked):", section)
            self.assertIn("Exit Criteria (TODO-linked):", section)

            entry_section = _subsection_between(
                section,
                start_label="Entry Criteria (TODO-linked):",
                end_label="Exit Criteria (TODO-linked):",
            )
            exit_section = _subsection_between(
                section,
                start_label="Exit Criteria (TODO-linked):",
                end_label="Current Checkpoint:",
            )
            self.assertRegex(entry_section, r"TODO-\d{4}")
            self.assertRegex(exit_section, r"TODO-\d{4}")

    def test_deferred_build_backlog_and_gate_blockers_are_visible_in_one_place(self) -> None:
        text = TRACKER_PATH.read_text()
        deferred_section = _heading_section(text, heading="## Deferred-Build Backlog")
        blockers_section = _heading_section(text, heading="## Phase Gate Blockers")

        self.assertIn("build_deferred: true", deferred_section)
        self.assertRegex(deferred_section, r"TODO-\d{4}")
        self.assertRegex(blockers_section, r"TODO-\d{4}")
        self.assertIn("Open gate blockers", blockers_section)


def _heading_section(text: str, *, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    if end == -1:
        end = len(text)
    return text[start:end]


def _subsection_between(section: str, *, start_label: str, end_label: str) -> str:
    start = section.index(start_label)
    end = section.index(end_label, start + 1)
    return section[start:end]


if __name__ == "__main__":
    unittest.main()
