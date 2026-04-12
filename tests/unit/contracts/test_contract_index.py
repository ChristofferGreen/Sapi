from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_INDEX_PATH = REPO_ROOT / "docs" / "contract_index.md"


class ContractIndexTests(unittest.TestCase):
    def _parse_authority_rows(self) -> list[tuple[str, str, str, str]]:
        text = CONTRACT_INDEX_PATH.read_text()
        self.assertIn("## Canonical Contract Authority Map", text)

        start = text.index("## Canonical Contract Authority Map")
        end = text.find("\n## ", start + 1)
        if end == -1:
            end = len(text)
        section = text[start:end]

        table_lines = [line for line in section.splitlines() if line.strip().startswith("|")]
        self.assertGreaterEqual(len(table_lines), 3)

        rows: list[tuple[str, str, str, str]] = []
        for line in table_lines[2:]:
            stripped = line.strip()
            if set(stripped) <= {"|", "-", ":", " "}:
                continue
            parts = [cell.strip() for cell in stripped.strip("|").split("|")]
            self.assertEqual(len(parts), 4)
            rows.append((parts[0], parts[1], parts[2], parts[3]))
        return rows

    def test_index_exists_and_is_consolidated(self) -> None:
        self.assertTrue(CONTRACT_INDEX_PATH.is_file())
        text = CONTRACT_INDEX_PATH.read_text()
        self.assertEqual(text.count("## Canonical Contract Authority Map"), 1)

        rows = self._parse_authority_rows()
        self.assertGreaterEqual(len(rows), 6)

    def test_no_duplicate_authority_claims_for_same_contract_area(self) -> None:
        rows = self._parse_authority_rows()
        areas = [row[0] for row in rows]
        self.assertEqual(len(areas), len(set(areas)))

    def test_every_row_has_single_authority_doc_and_explicit_section_pointer(self) -> None:
        rows = self._parse_authority_rows()
        allowed_docs = {
            "./design.md",
            "./low_level.md",
            "./testing_plan.md",
        }

        for _area, source_cell, section_cell, _notes in rows:
            matches = re.findall(r"\(([^)]+)\)", source_cell)
            self.assertEqual(len(matches), 1)
            self.assertIn(matches[0], allowed_docs)
            self.assertRegex(section_cell, r"Section")


if __name__ == "__main__":
    unittest.main()
