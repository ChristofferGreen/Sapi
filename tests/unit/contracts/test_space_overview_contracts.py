from __future__ import annotations

import json
import unittest
from pathlib import Path

from sapi.contracts.run_envelopes import _SEMANTIC_FLOW_KEYS
from sapi.contracts.semantic_specs import FLOW_MAP, resolve_semantic_spec


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"
LOW_LEVEL_DOC_PATH = REPO_ROOT / "docs" / "low_level.md"
SCHEMA_PATH = REPO_ROOT / "schemas" / "space_overview_generation.v1.schema.json"


class SpaceOverviewContractTests(unittest.TestCase):
    def test_space_overview_flow_map_entry_matches_canonical_contract(self) -> None:
        entry = FLOW_MAP["space_overview_generation"]
        self.assertEqual(
            entry.spec_relpath,
            "ai_flows/generation_specs/space_overview_generation.v1.md",
        )
        self.assertEqual(
            entry.schema_relpath,
            "schemas/space_overview_generation.v1.schema.json",
        )
        self.assertEqual(
            entry.output_json_path_template,
            "<space_root>/outputs/space_overview/<overview_id>/overview.json",
        )

        resolved = resolve_semantic_spec("space_overview_generation", repo_root=REPO_ROOT)
        self.assertEqual(
            resolved.context_paths[0],
            "<space_root>/outputs/space_overview/<overview_id>/context.json",
        )
        self.assertEqual(resolved.context_paths[-1], "<space_root>/subspaces.json")

    def test_space_overview_schema_enforces_required_keys_and_section_ids(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text())
        self.assertEqual(schema.get("type"), "object")
        self.assertFalse(schema.get("additionalProperties", True))
        self.assertEqual(
            set(schema["required"]),
            {"schema_version", "metadata", "sections", "references", "freshness", "warnings"},
        )

        sections = schema["properties"]["sections"]
        self.assertEqual(sections["minItems"], 5)
        self.assertEqual(sections["maxItems"], 5)
        section_ids = {
            rule["contains"]["properties"]["section_id"]["const"]
            for rule in sections["allOf"]
        }
        self.assertEqual(
            section_ids,
            {
                "topic_framing",
                "key_themes",
                "agreement_and_disagreement",
                "methods_and_evidence",
                "open_questions",
            },
        )

    def test_docs_define_overview_auditability_and_deterministic_boundaries(self) -> None:
        design_text = _normalize_ws(DESIGN_DOC_PATH.read_text())
        low_level_text = _normalize_ws(LOW_LEVEL_DOC_PATH.read_text())

        self.assertIn("### 7.2.1 Space/subspace overview synthesis", design_text)
        self.assertIn("semantic flow key is `space_overview_generation`", design_text)
        self.assertIn(
            "deterministic markdown/article projection path is",
            design_text,
        )
        self.assertIn(
            "overview generation MUST NOT mutate canonical knowledge artifacts under `sources/`, `claims/`, `relations/`, `topics/`, or `profiles/`",
            design_text,
        )
        self.assertIn("### 8.5 Overview Synthesis Contract (`scripts/generate_overview.py`)", low_level_text)
        self.assertIn("overview orchestration belongs in `sapi/overview/overview_pipeline.py`", low_level_text)
        self.assertIn(
            "overview rendering MUST NOT issue web requests or additional LLM calls",
            low_level_text,
        )

    def test_run_envelope_semantic_flow_key_set_includes_space_overview_generation(self) -> None:
        self.assertIn("space_overview_generation", _SEMANTIC_FLOW_KEYS)


def _normalize_ws(text: str) -> str:
    return " ".join(text.split())


if __name__ == "__main__":
    unittest.main()
