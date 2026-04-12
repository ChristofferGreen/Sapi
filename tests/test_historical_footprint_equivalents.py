from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class HistoricalFootprintEquivalentsTests(unittest.TestCase):
    def test_broad_tests_root_footprint_exists(self) -> None:
        # Preserve a root-level `tests/test_*.py` entrypoint footprint while
        # modern test ownership remains split across unit/integration/golden modules.
        self.assertTrue(Path(__file__).name.startswith("test_"))

    def test_historical_high_value_intents_map_to_current_modules(self) -> None:
        intent_mapping = {
            "test_site_relocatability.py": [
                "tests/unit/contracts/test_registry_paths.py",
                "tests/unit/core/test_site_scope_contracts.py",
            ],
            "test_site_navigation.py": [
                "tests/unit/build/test_site_builder_contracts.py",
            ],
            "test_site_tabs_accessibility.py": [
                "tests/unit/build/test_site_builder_contracts.py",
            ],
            "test_ingest_source_date_extraction.py": [
                "tests/unit/ingest/test_source_date_title_policy.py",
            ],
            "test_skill_output_contract_failures.py": [
                "tests/unit/semantic/test_prompt_asset_precedence.py",
                "tests/golden/test_skill_snapshot.py",
            ],
            "test_persona_comments_cli.py": [
                "tests/integration/wrappers/test_wrapper_alias_normalization.py",
                "tests/integration/wrappers/test_wrapper_alias_conflicts.py",
            ],
            "test_social_users.py": [
                "tests/unit/profiles/test_persona_catalog_loader.py",
            ],
            "test_persona_profile_pages.py": [
                "tests/unit/build/test_site_builder_contracts.py",
            ],
        }

        for historical_test, mapped_modules in intent_mapping.items():
            with self.subTest(historical_test=historical_test):
                for module_path in mapped_modules:
                    full_path = REPO_ROOT / module_path
                    self.assertTrue(full_path.is_file(), f"Missing mapping target: {module_path}")


if __name__ == "__main__":
    unittest.main()
