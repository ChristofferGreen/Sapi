from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class Todo0201ModuleTopologyTests(unittest.TestCase):
    def test_sapi_package_topology_matches_low_level_contract(self) -> None:
        expected_package_dirs = [
            "sapi/contracts",
            "sapi/core",
            "sapi/llm",
            "sapi/ingest",
            "sapi/query",
            "sapi/comments",
            "sapi/profiles",
            "sapi/overview",
            "sapi/build",
            "sapi/lint",
        ]
        for rel in expected_package_dirs:
            self.assertTrue((REPO_ROOT / rel).is_dir(), rel)
            self.assertTrue((REPO_ROOT / rel / "__init__.py").is_file(), f"{rel}/__init__.py")

        expected_modules = [
            "sapi/contracts/ids.py",
            "sapi/contracts/paths.py",
            "sapi/contracts/run_envelopes.py",
            "sapi/contracts/schemas.py",
            "sapi/contracts/semantic_specs.py",
            "sapi/core/registry.py",
            "sapi/core/site_scope.py",
            "sapi/core/fs_store.py",
            "sapi/core/transactions.py",
            "sapi/core/locks.py",
            "sapi/llm/client.py",
            "sapi/llm/trace.py",
            "sapi/llm/semantic_executor.py",
            "sapi/ingest/ingest_pipeline.py",
            "sapi/ingest/source_content.py",
            "sapi/ingest/records_writer.py",
            "sapi/ingest/relation_store.py",
            "sapi/ingest/citations.py",
            "sapi/ingest/topic_generator.py",
            "sapi/query/query_pipeline.py",
            "sapi/query/retrieval.py",
            "sapi/query/renderers.py",
            "sapi/comments/comments_pipeline.py",
            "sapi/comments/merge_normalize.py",
            "sapi/comments/controls.py",
            "sapi/profiles/profiles_pipeline.py",
            "sapi/profiles/history.py",
            "sapi/overview/overview_pipeline.py",
            "sapi/build/projection.py",
            "sapi/build/site_builder.py",
            "sapi/build/projection_index.py",
            "sapi/lint/lint_engine.py",
            "sapi/lint/severity.py",
        ]
        for rel in expected_modules:
            self.assertTrue((REPO_ROOT / rel).is_file(), rel)

    def test_wrapper_target_scripts_exist_with_stub_entrypoints(self) -> None:
        wrapper_target_scripts = [
            "scripts/ingest_source.py",
            "scripts/query.py",
            "scripts/create_comments.py",
            "scripts/generate_profiles.py",
            "scripts/generate_overview.py",
            "scripts/build_site.py",
            "scripts/lint.py",
            "scripts/evaluate_source.py",
        ]

        for rel in wrapper_target_scripts:
            path = REPO_ROOT / rel
            self.assertTrue(path.is_file(), rel)
            content = path.read_text()
            self.assertIn("def main()", content, rel)
            self.assertIn('if __name__ == "__main__":', content, rel)

    def test_module_boundaries_are_documented_in_package_init_files(self) -> None:
        root_init = (REPO_ROOT / "sapi/__init__.py").read_text()
        self.assertIn("Module boundaries", root_init)
        for token in [
            "contracts",
            "core",
            "llm",
            "ingest",
            "query",
            "comments",
            "profiles",
            "overview",
            "build",
            "lint",
        ]:
            self.assertIn(token, root_init)

        scripts_init = (REPO_ROOT / "scripts/__init__.py").read_text()
        self.assertIn("Wrapper-target entrypoints", scripts_init)
        for mapping in [
            "ingest.sh -> scripts/ingest_source.py",
            "query.sh -> scripts/query.py",
            "create_comments.sh -> scripts/create_comments.py",
            "generate_profiles.sh -> scripts/generate_profiles.py",
            "generate_overview.sh -> scripts/generate_overview.py",
            "regenerate_web.sh -> scripts/build_site.py",
            "validate.sh -> scripts/lint.py",
            "evaluate_source.sh -> scripts/evaluate_source.py",
        ]:
            self.assertIn(mapping, scripts_init)


if __name__ == "__main__":
    unittest.main()
