from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import warnings

from sapi.contracts.semantic_specs import (
    FLOW_MAP,
    SemanticSpecMapEntry,
    normalize_semantic_flow_key,
    resolve_semantic_invocation_spec,
    resolve_semantic_spec,
    validate_map_entry_major_version,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


class SpecResolutionTests(unittest.TestCase):
    def test_specs_resolve_only_via_authoritative_flow_map(self) -> None:
        resolved = resolve_semantic_spec("ingest_extraction", repo_root=REPO_ROOT)
        self.assertEqual(
            resolved.spec_path,
            (REPO_ROOT / FLOW_MAP["ingest_extraction"].spec_relpath).resolve(),
        )
        self.assertEqual(
            resolved.schema_path,
            (REPO_ROOT / FLOW_MAP["ingest_extraction"].schema_relpath).resolve(),
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "ai_flows/generation_specs").mkdir(parents=True)
            (tmp_root / "schemas").mkdir(parents=True)
            (tmp_root / "ai_flows/generation_specs/new_flow.v1.md").write_text(
                "flow_key: new_flow\nversion: v1\nschema_path: schemas/new_flow.v1.schema.json\n"
                "output_json_path: <space_root>/x.json\ncontext_paths:\n  - <space_root>/x\n---\n"
            )
            (tmp_root / "schemas/new_flow.v1.schema.json").write_text("{}")

            with self.assertRaises(ValueError):
                resolve_semantic_spec("new_flow", repo_root=tmp_root)

    def test_persona_comment_alias_normalizes_to_comment_section_generation(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertEqual(
                normalize_semantic_flow_key("persona_comment_generation"),
                "comment_section_generation",
            )
            resolved = resolve_semantic_spec("persona_comment_generation", repo_root=REPO_ROOT)
        self.assertEqual(resolved.flow_key, "comment_section_generation")
        self.assertTrue(caught)
        self.assertIn("deprecated", str(caught[-1].message).lower())

    def test_canonical_flow_key_does_not_emit_alias_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            normalized = normalize_semantic_flow_key("comment_section_generation")
            resolved = resolve_semantic_spec("comment_section_generation", repo_root=REPO_ROOT)
        self.assertEqual(normalized, "comment_section_generation")
        self.assertEqual(resolved.flow_key, "comment_section_generation")
        alias_warnings = [
            warning
            for warning in caught
            if "deprecated" in str(warning.message).lower()
        ]
        self.assertEqual(alias_warnings, [])

    def test_alias_normalizes_at_invocation_input_boundary(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            resolved = resolve_semantic_invocation_spec(
                "persona_comment_generation",
                repo_root=REPO_ROOT,
                path_tokens={
                    "space_root": REPO_ROOT / ".tmp/tests/space",
                    "site_path": REPO_ROOT / ".tmp/tests/site",
                    "run_id": "run-001",
                    "page_ref_key": "topic--alpha",
                },
            )

        self.assertEqual(resolved.flow_key, "comment_section_generation")
        self.assertEqual(
            resolved.spec_path,
            (REPO_ROOT / FLOW_MAP["comment_section_generation"].spec_relpath).resolve(),
        )
        self.assertEqual(
            resolved.output_json_path,
            (REPO_ROOT / ".tmp/tests/space/runs/run-001/semantic/comment_section_generation/topic--alpha.json").resolve(),
        )
        self.assertTrue(caught)
        self.assertIn("deprecated", str(caught[-1].message).lower())

    def test_incompatible_schema_major_change_requires_explicit_flow_map_update(self) -> None:
        bad_entry = SemanticSpecMapEntry(
            flow_key="ingest_extraction",
            spec_relpath="ai_flows/generation_specs/ingest_extraction.v1.md",
            schema_relpath="schemas/ingest_extraction.v2.schema.json",
            output_json_path_template="<space_root>/runs/<run_id>/semantic/ingest_extraction.json",
        )
        with self.assertRaises(ValueError):
            validate_map_entry_major_version(bad_entry)

    def test_resolver_stays_pinned_to_mapped_major_until_flow_map_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            specs_dir = tmp_root / "ai_flows/generation_specs"
            schemas_dir = tmp_root / "schemas"
            specs_dir.mkdir(parents=True)
            schemas_dir.mkdir(parents=True)

            (specs_dir / "ingest_extraction.v1.md").write_text(
                "flow_key: ingest_extraction\n"
                "version: v1\n"
                "schema_path: schemas/ingest_extraction.v1.schema.json\n"
                "output_json_path: <space_root>/runs/<run_id>/semantic/ingest_extraction.json\n"
                "context_paths:\n"
                "  - <space_root>/sources\n"
                "---\n"
                "Generate ingest extraction JSON.\n"
            )
            (schemas_dir / "ingest_extraction.v1.schema.json").write_text("{}\n")

            # Presence of v2 files must not affect resolution while flow-map entry remains v1.
            (specs_dir / "ingest_extraction.v2.md").write_text(
                "flow_key: ingest_extraction\n"
                "version: v2\n"
                "schema_path: schemas/ingest_extraction.v2.schema.json\n"
                "output_json_path: <space_root>/runs/<run_id>/semantic/ingest_extraction-v2.json\n"
                "context_paths:\n"
                "  - <space_root>/sources\n"
                "---\n"
                "Generate ingest extraction JSON v2.\n"
            )
            (schemas_dir / "ingest_extraction.v2.schema.json").write_text("{}\n")

            resolved = resolve_semantic_spec("ingest_extraction", repo_root=tmp_root)
            self.assertEqual(
                resolved.spec_path,
                (tmp_root / FLOW_MAP["ingest_extraction"].spec_relpath).resolve(),
            )
            self.assertEqual(resolved.version, "v1")


if __name__ == "__main__":
    unittest.main()
