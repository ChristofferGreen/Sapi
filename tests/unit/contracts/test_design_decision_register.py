from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"


class DesignDecisionRegisterTests(unittest.TestCase):
    def _decision_rows(self) -> list[tuple[str, str, str, str, str, str]]:
        text = DESIGN_DOC_PATH.read_text()
        self.assertEqual(text.count("### 1.3 Decision register"), 1)

        start = text.index("### 1.3 Decision register")
        end = text.find("\n## ", start + 1)
        if end == -1:
            end = len(text)
        section = text[start:end]

        table_lines = [line for line in section.splitlines() if line.strip().startswith("|")]
        self.assertGreaterEqual(len(table_lines), 3)

        rows: list[tuple[str, str, str, str, str, str]] = []
        for line in table_lines[2:]:
            stripped = line.strip()
            if set(stripped) <= {"|", "-", ":", " "}:
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            self.assertEqual(len(cells), 6)
            rows.append((cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]))
        return rows

    def test_decision_table_exists(self) -> None:
        rows = self._decision_rows()
        self.assertGreaterEqual(len(rows), 3)

    def test_unresolved_rows_define_owner_and_due_date(self) -> None:
        rows = self._decision_rows()
        unresolved = [row for row in rows if row[2] == "unresolved"]
        self.assertGreaterEqual(len(unresolved), 1)

        for _decision, _options, _status, owner, due_date, _location in unresolved:
            self.assertTrue(owner and owner != "-")
            self.assertRegex(due_date, r"^\d{4}-\d{2}-\d{2}$")

    def test_resolved_rows_link_to_final_contract_location(self) -> None:
        rows = self._decision_rows()
        resolved = [row for row in rows if row[2] == "resolved"]
        self.assertGreaterEqual(len(resolved), 1)

        for _decision, _options, _status, _owner, _due_date, final_location in resolved:
            link_targets = re.findall(r"\(([^)]+)\)", final_location)
            self.assertEqual(len(link_targets), 1)
            self.assertIn("#", link_targets[0])


if __name__ == "__main__":
    unittest.main()
