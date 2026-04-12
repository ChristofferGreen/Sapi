from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.ingest.records_writer import (
    ingest_source_artifacts_and_record,
    run_ingest_extraction_and_persist_canonical,
)
from sapi.ingest.relation_store import relation_file_id_from_relation_id
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.semantic_executor import SemanticFlowError


class _StaticSemanticClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        return json.dumps(self._payload)


class IngestExtractionCanonicalWriteTests(unittest.TestCase):
    def test_ingest_extraction_output_must_validate_against_schema_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            run_id = "run-schema-invalid"

            invalid_semantic_output = {
                "source_date_inference": None,
                "source": {},
                "claims": [],
                "relations": [],
            }
            with self.assertRaises(SemanticFlowError):
                run_ingest_extraction_and_persist_canonical(
                    space_root=space_root,
                    source_id=source_id,
                    run_id=run_id,
                    llm_client=_StaticSemanticClient(invalid_semantic_output),
                    max_repair_loops=0,
                )

            semantic_path = space_root / "runs" / run_id / "semantic" / "ingest_extraction.json"
            self.assertFalse(semantic_path.exists())
            self.assertFalse((space_root / "claims").exists())
            self.assertFalse((space_root / "relations").exists())

    def test_canonical_claim_and_relation_writes_follow_id_and_path_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            run_id = "run-claim-relation-contract"

            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": None,
                },
                "source": {"source_id": source_id, "title": "Contract Source"},
                "claims": [
                    {"text": "Cats purr when content."},
                    {"text": "Purring can indicate comfort in domestic cats."},
                ],
                "relations": [
                    {
                        "relation_type": "supports",
                        "src_claim_ref": "0",
                        "dst_claim_ref": "1",
                    }
                ],
                "summary": "Two claims extracted.",
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id=run_id,
                llm_client=_StaticSemanticClient(semantic_output),
            )

            self.assertTrue(result.semantic_output_path.is_file())
            self.assertEqual(len(result.claim_paths), 2)
            claim_ids: list[str] = []
            for claim_path in result.claim_paths:
                self.assertEqual(claim_path.parent, space_root / "claims")
                self.assertRegex(claim_path.name, r"^claim-[a-z0-9-]+--[0-9a-f]{12,}\.json$")
                claim_payload = json.loads(claim_path.read_text())
                claim_id = claim_payload["claim_id"]
                claim_ids.append(claim_id)
                self.assertEqual(claim_path.name, f"{claim_id}.json")
                self.assertEqual(claim_payload["source_id"], source_id)

            self.assertEqual(len(result.relation_paths), 1)
            relation_path = result.relation_paths[0]
            self.assertEqual(relation_path.parent, space_root / "relations")
            self.assertRegex(relation_path.name, r"^rel-[0-9a-f]{64}\.json$")
            relation_payload = json.loads(relation_path.read_text())
            self.assertEqual(
                relation_payload["relation_id"],
                f"supports:{claim_ids[0]}->{claim_ids[1]}",
            )
            self.assertEqual(
                relation_payload["relation_file_id"],
                relation_file_id_from_relation_id(relation_payload["relation_id"]),
            )
            self.assertEqual(relation_path.name, f"{relation_payload['relation_file_id']}.json")

    def test_relation_writes_align_with_canonical_relation_normalization_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))

            claim_alpha = "claim-alpha--111111111111"
            claim_beta = "claim-beta--222222222222"
            semantic_output = {
                "source_date_inference": {
                    "date": "2026-04-12",
                    "origin": "explicit",
                    "confidence": "high",
                    "rationale": None,
                },
                "source": {"source_id": source_id, "title": "Normalization Source"},
                "claims": [
                    {"claim_id": claim_alpha, "text": "Alpha statement."},
                    {"claim_id": claim_beta, "text": "Beta statement."},
                ],
                "relations": [
                    {
                        "relation_type": "contradictory",
                        "src_claim_id": claim_beta,
                        "dst_claim_id": claim_alpha,
                        "status": "closed",
                    }
                ],
                "summary": "Contradictory relation extracted.",
                "warnings": [],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-relation-normalization",
                llm_client=_StaticSemanticClient(semantic_output),
            )

            relation_payload = json.loads(result.relation_paths[0].read_text())
            self.assertEqual(relation_payload["src_claim_id"], claim_alpha)
            self.assertEqual(relation_payload["dst_claim_id"], claim_beta)
            self.assertEqual(
                relation_payload["relation_id"],
                f"contradictory:{claim_alpha}|{claim_beta}",
            )
            self.assertEqual(relation_payload["status"], "resolved")
            self.assertEqual(
                relation_payload["relation_file_id"],
                relation_file_id_from_relation_id(relation_payload["relation_id"]),
            )

    def test_ingest_extraction_persists_summary_warnings_and_source_date_inference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = self._bootstrap_source(Path(tmp))
            semantic_output = {
                "source_date_inference": {
                    "date": None,
                    "origin": "unknown",
                    "confidence": "unknown",
                    "rationale": "no publication date found",
                },
                "source": {"source_id": source_id, "title": "Summary Source"},
                "claims": [{"text": "One claim extracted."}],
                "relations": [],
                "summary": "Extraction summary text.",
                "warnings": [
                    {
                        "code": "missing_publication_date",
                        "message": "Publication date could not be resolved; continuing with date=null.",
                    }
                ],
            }

            result = run_ingest_extraction_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-source-summary",
                llm_client=_StaticSemanticClient(semantic_output),
            )

            source_record = json.loads(result.source_record_path.read_text())
            self.assertEqual(source_record["source_date_inference"], semantic_output["source_date_inference"])
            self.assertEqual(source_record["summary"], semantic_output["summary"])
            self.assertEqual(source_record["warnings"], semantic_output["warnings"])

    def _bootstrap_source(self, tmp_root: Path) -> tuple[Path, str]:
        space_root = tmp_root / "spaces" / "alpha"
        source_path = tmp_root / "source.txt"
        source_path.write_text("ingest extraction contract fixture\n")
        result = ingest_source_artifacts_and_record(
            space_root=space_root,
            source_path_or_url=str(source_path),
            source_title_override="Fixture Source",
        )
        return space_root, result.source_id


if __name__ == "__main__":
    unittest.main()
