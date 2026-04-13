from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"
LOW_LEVEL_DOC_PATH = REPO_ROOT / "docs" / "low_level.md"
TESTING_PLAN_PATH = REPO_ROOT / "docs" / "testing_plan.md"


class WebPresentationContractTests(unittest.TestCase):
    def test_design_section8_defines_canonical_presentation_contract(self) -> None:
        section = _section_text(DESIGN_DOC_PATH.read_text(), "## 8. Site/UI and Static Build Contracts")
        self.assertIn("Canonical presentation contract (normative):", section)
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', section)
        self.assertIn('<link rel="stylesheet" href=".../assets/site.css">', section)
        self.assertIn(
            "`site-shell`, `site-sidebar`, `site-main`, `content-card`, `feed-list`, `topic-section`, `source-summary`",
            section,
        )
        self.assertIn("build success MUST require emitted stylesheet asset presence plus HTML link references", section)
        self.assertIn(
            "`toolchain_versions.tailwind_cli` is declaration-only metadata and MUST NOT be treated as proof that stylesheet compilation occurred",
            section,
        )

    def test_low_level_section9_declares_asset_ownership_and_validation_boundaries(self) -> None:
        section = _section_text(LOW_LEVEL_DOC_PATH.read_text(), "## 9. Deterministic Build and Projection")
        self.assertIn("Presentation asset and ownership contracts (normative implementation boundary):", section)
        self.assertIn("deterministic build MUST emit canonical stylesheet assets at `<render_root>/assets/site.css`", section)
        self.assertIn("rendered pages MUST include one viewport meta tag and one stylesheet link to `assets/site.css`", section)
        self.assertIn("CSS toolchain stage owns stylesheet compilation; missing or failed stylesheet generation is a build error", section)
        self.assertIn(
            "build validation MUST assert stylesheet file existence and HTML link references before reporting success",
            section,
        )
        self.assertIn(
            "run/build metadata key `toolchain_versions.tailwind_cli` is informational only and MUST NOT be treated as compilation success evidence",
            section,
        )

    def test_testing_plan_includes_explicit_presentation_contract_coverage_requirements(self) -> None:
        section = _section_text(TESTING_PLAN_PATH.read_text(), "### Tier 4: Build/Projection Determinism Tests")
        self.assertIn("Presentation contract coverage requirements (Section 8 / Section 9):", section)
        self.assertIn("Tier 1 contract test MUST assert docs require canonical viewport meta", section)
        self.assertIn("tests/unit/contracts/test_web_presentation_contracts.py", section)
        self.assertIn("Tier 4 integration coverage MUST assert built HTML pages include canonical viewport meta", section)
        self.assertIn("Tier 4 failure coverage MUST assert site build fails when stylesheet emission", section)


def _section_text(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    if end == -1:
        end = len(text)
    return text[start:end]


if __name__ == "__main__":
    unittest.main()
