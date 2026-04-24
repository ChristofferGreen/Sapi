from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"
LOW_LEVEL_DOC_PATH = REPO_ROOT / "docs" / "low_level.md"
TESTING_PLAN_PATH = REPO_ROOT / "docs" / "testing_plan.md"


class SourceAnalysisAndRelatedLinkContractTests(unittest.TestCase):
    def test_design_doc_defines_source_markdown_and_related_link_contracts(self) -> None:
        design_text = DESIGN_DOC_PATH.read_text()
        artifact_section = _section_text(design_text, "### 5.3 Source artifact storage")
        reference_section = _section_text(design_text, "### 7.2 Reference extraction and linking")
        self.assertIn("source.md", artifact_section)
        self.assertIn("source_extraction.json", artifact_section)
        self.assertIn("analysis_policy", artifact_section)
        self.assertIn("markdown quality states MUST be explicit", artifact_section)
        self.assertIn("external_related_links[]", reference_section)
        self.assertIn("link_type", reference_section)
        self.assertIn("related_link_enrichment", reference_section)
        self.assertIn("topic and claim pages MUST inherit/aggregate curated external links", reference_section)

    def test_low_level_doc_wires_ingest_pipeline_to_markdown_first_analysis(self) -> None:
        section = _section_text(LOW_LEVEL_DOC_PATH.read_text(), "### 8.1 Ingest Pipeline (`scripts/ingest_source.py`)")
        self.assertIn("write canonical sibling artifacts `source.md` and `source_extraction.json`", section)
        self.assertIn("default source-reading input is `<space_root>/sources/artifacts/<source_id>/source.md`", section)
        self.assertIn("reference extraction prefers `source.md`", section)
        self.assertIn("external_related_links[]", section)

    def test_testing_plan_mentions_source_analysis_and_related_link_coverage(self) -> None:
        text = TESTING_PLAN_PATH.read_text()
        self.assertIn("test_source_analysis_and_related_link_contracts.py", text)
        self.assertIn("source.md", text)
        self.assertIn("source_extraction.json", text)
        self.assertIn("External Related Links", text)


def _section_text(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    if end == -1:
        end = len(text)
    return text[start:end]


if __name__ == "__main__":
    unittest.main()
