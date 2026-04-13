from __future__ import annotations

import unittest
from pathlib import Path

from sapi.contracts.semantic_specs import (
    SkillSemanticContract,
    resolve_semantic_contract_with_precedence,
    resolve_semantic_invocation_spec,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


class PromptAssetPrecedenceTests(unittest.TestCase):
    def test_generation_spec_contract_resolution_has_no_conflicts_without_skill_text(self) -> None:
        result = resolve_semantic_contract_with_precedence(
            "topic_generation",
            repo_root=REPO_ROOT,
        )
        self.assertEqual(result.conflict_fields, [])
        self.assertEqual(result.conflict_details, {})
        self.assertEqual(
            result.resolved_spec.output_json_path_template,
            "<space_root>/runs/<run_id>/semantic/topic_generation.json",
        )

    def test_semantic_output_contract_is_sourced_from_generation_specs_not_skill_text(self) -> None:
        result = resolve_semantic_contract_with_precedence(
            "query_synthesis",
            repo_root=REPO_ROOT,
            skill_contract=SkillSemanticContract(
                schema_path="schemas/overridden.schema.json",
                output_json_path="<space_root>/outputs/query/override.json",
                context_paths=["<space_root>/bogus"],
            ),
        )

        resolved = result.resolved_spec
        self.assertEqual(
            resolved.schema_path,
            (REPO_ROOT / "schemas/query_synthesis.v1.schema.json").resolve(),
        )
        self.assertEqual(
            resolved.output_json_path_template,
            "<space_root>/outputs/query/<query_id>/query.json",
        )
        self.assertEqual(
            resolved.context_paths,
            ["<space_root>/topics", "<space_root>/claims", "<space_root>/sources"],
        )

    def test_skill_and_generation_spec_disagreement_resolves_in_favor_of_generation_spec(self) -> None:
        result = resolve_semantic_contract_with_precedence(
            "ingest_extraction",
            repo_root=REPO_ROOT,
            skill_contract=SkillSemanticContract(
                schema_path="schemas/different.schema.json",
                output_json_path="<space_root>/runs/<run_id>/semantic/custom.json",
                context_paths=["<space_root>/other"],
            ),
        )

        self.assertEqual(
            result.conflict_fields,
            ["context_paths", "output_json_path", "schema_path"],
        )
        self.assertEqual(
            result.conflict_details["schema_path"]["authoritative"],
            "schemas/ingest_extraction.v1.schema.json",
        )
        self.assertEqual(
            result.conflict_details["output_json_path"]["authoritative"],
            "<space_root>/runs/<run_id>/semantic/ingest_extraction.json",
        )

    def test_deterministic_render_build_logic_cannot_override_semantic_schema_contract(self) -> None:
        with self.assertRaises(ValueError):
            resolve_semantic_contract_with_precedence(
                "topic_generation",
                repo_root=REPO_ROOT,
                deterministic_schema_override="schemas/attempted-override.schema.json",
            )

    def test_deterministic_schema_override_is_rejected_for_invocation_resolution_too(self) -> None:
        with self.assertRaises(ValueError):
            resolve_semantic_invocation_spec(
                "topic_generation",
                repo_root=REPO_ROOT,
                path_tokens={
                    "space_root": REPO_ROOT / ".tmp/tests/space",
                    "run_id": "run-001",
                },
                deterministic_schema_override="schemas/attempted-override.schema.json",
            )


if __name__ == "__main__":
    unittest.main()
