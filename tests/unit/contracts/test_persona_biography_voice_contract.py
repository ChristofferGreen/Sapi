from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"


class PersonaBiographyVoiceContractTests(unittest.TestCase):
    def test_persona_biography_and_image_prompt_contract_requirements(self) -> None:
        design_text = DESIGN_DOC_PATH.read_text()
        section = _section_text(
            design_text,
            "### 7.4 Social users and persona catalog",
        )
        self.assertIn("`biography` MUST be written in first person voice", section)
        self.assertIn("`90..180` words (`220` hard upper bound)", section)
        self.assertIn("core worldview, evidence/decision style, priorities, and friction points", section)
        self.assertIn("`biography_profile` is required for profile-page display copy", section)
        self.assertIn("`biography_profile` MUST also be written in first person voice", section)
        self.assertIn("`short_cv` is required and MUST be a non-empty list", section)
        self.assertIn("`short_cv` entries MUST use fictional organizations and educational institutions", section)
        self.assertIn("required `profile_image_prompt` used for persona-image generation", section)
        self.assertIn("required `profile_image_path` (repo-relative `.jpg` path under `personas/profile_images/`)", section)
        self.assertIn("derive `name_slug` from `full_name`", section)
        self.assertIn("`persona_id` MUST equal `persona-<name_slug>`", section)
        self.assertIn("`profile_image_path` MUST equal `personas/profile_images/<name_slug>.jpg`", section)
        self.assertIn("`profile_image_path` MUST resolve to an existing `.jpg` image file at runtime", section)
        self.assertIn("`profile_image_thumb_path` SHOULD exist alongside `profile_image_path`", section)
        self.assertIn("`profile_image_prompt` MUST request a photorealistic single-person image", section)


def _section_text(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n### ", start + 1)
    if end == -1:
        end = text.find("\n## ", start + 1)
    if end == -1:
        end = len(text)
    return text[start:end]


if __name__ == "__main__":
    unittest.main()
