from __future__ import annotations

import json
import unittest

from scripts.generate_profiles import _BootstrapPersonaProfileClient


class BootstrapPersonaProfileClientTests(unittest.TestCase):
    def test_generate_semantic_json_includes_profile_biography_and_short_cv_sections(self) -> None:
        client = _BootstrapPersonaProfileClient(
            persona_row={
                "persona_id": "persona-test",
                "display_name": "Persona Test",
                "profile_image_path": "personas/profile_images/test.jpg",
                "biography_profile": (
                    "I am known for practical judgment and clear communication that helps teams make "
                    "defensible decisions under pressure."
                ),
                "short_cv": [
                    "Lead Analyst, Example Org (2021-present)",
                    "MSc, Example University (2019-2021)",
                ],
                "interests": ["risk analysis", "governance"],
                "prompt_fields": {"argument_style": "structured"},
            },
            space_name="alpha",
        )

        payload = json.loads(client.generate_semantic_json(request=object()))
        sections = {str(section["title"]): str(section["content"]) for section in payload["profile_sections"]}

        self.assertEqual(payload["persona_id"], "persona-test")
        self.assertEqual(payload["space_name"], "alpha")
        self.assertIn("Profile biography", sections)
        self.assertIn("Short CV", sections)
        self.assertIn("known for practical judgment", sections["Profile biography"])
        self.assertIn("- Lead Analyst, Example Org (2021-present)", sections["Short CV"])


if __name__ == "__main__":
    unittest.main()
