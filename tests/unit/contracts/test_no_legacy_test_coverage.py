from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTING_PLAN_PATH = REPO_ROOT / "docs" / "testing_plan.md"


class NoLegacyTestCoverageContractTests(unittest.TestCase):
    def test_testing_plan_describes_canonical_only_fail_fast_coverage(self) -> None:
        testing_plan_text = TESTING_PLAN_PATH.read_text()
        self.assertIn(
            "removed-flow-key fail-fast handling",
            testing_plan_text,
        )
        self.assertIn(
            "Removed compatibility inputs fail fast across flow-map, wrapper/parser, persona, comment, and relation boundaries.",
            testing_plan_text,
        )
        self.assertNotIn("input alias normalization", testing_plan_text)

    def test_removed_compatibility_pathways_have_explicit_fail_fast_tests(self) -> None:
        expected_test_markers = {
            "tests/unit/semantic/test_spec_resolution.py": [
                "test_removed_persona_comment_alias_fails_as_unknown_flow_key",
            ],
            "tests/unit/contracts/test_runtime_flag_surface.py": [
                "test_ingest_entrypoint_does_not_expose_removed_mode_flags",
                "test_comments_entrypoint_rejects_removed_alias_flags_as_unknown_arguments",
            ],
            "tests/unit/profiles/test_persona_catalog_loader.py": [
                "test_loader_rejects_legacy_id_field_and_requires_explicit_persona_id",
            ],
            "tests/unit/comments/test_turn_marker_validation.py": [
                "test_legacy_turn_marker_fails_fast",
                "test_legacy_ordinal_parent_refs_fail_fast",
            ],
            "tests/unit/ingest/test_relation_store_matrix.py": [
                "test_closed_relation_status_fails_fast",
            ],
            "tests/integration/pipelines/test_comments_pipeline.py": [
                "test_legacy_turn_marker_fails_pipeline_preflight",
                "test_legacy_ordinal_parent_ref_fails_validation",
                "test_legacy_frontmatter_controls_fail_fast_without_writing_page_json",
            ],
            "tests/integration/wrappers/test_wrapper_alias_normalization.py": [
                "test_ingest_removed_source_only_flags_fail_fast",
                "test_comments_removed_aliases_and_legacy_positional_count_fail_fast",
            ],
        }

        for relpath, markers in expected_test_markers.items():
            with self.subTest(relpath=relpath):
                text = (REPO_ROOT / relpath).read_text()
                for marker in markers:
                    self.assertIn(marker, text)

    def test_removed_compatibility_suite_does_not_reintroduce_deprecation_expectations(self) -> None:
        checked_modules = [
            "tests/unit/semantic/test_spec_resolution.py",
            "tests/unit/contracts/test_runtime_flag_surface.py",
            "tests/unit/profiles/test_persona_catalog_loader.py",
            "tests/unit/comments/test_turn_marker_validation.py",
            "tests/unit/ingest/test_relation_store_matrix.py",
            "tests/integration/pipelines/test_comments_pipeline.py",
            "tests/integration/wrappers/test_wrapper_alias_normalization.py",
            "tests/integration/wrappers/test_wrapper_alias_conflicts.py",
        ]
        forbidden_phrases = [
            "deprecation warning",
            "deprecated alias",
            "compatibility alias accepted",
            "legacy alias accepted",
            "normalize compatibility aliases",
        ]

        for relpath in checked_modules:
            with self.subTest(relpath=relpath):
                text = (REPO_ROOT / relpath).read_text().lower()
                for phrase in forbidden_phrases:
                    self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
