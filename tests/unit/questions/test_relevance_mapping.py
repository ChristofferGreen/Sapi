from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import create_deterministic_mock_llm_fixture

from sapi.core.transactions import ArtifactTransaction
from sapi.questions.prepared_questions import write_prepared_question_record
from sapi.questions.relevance_mapping import run_question_relevance_mapping_and_update


SOURCE_ID = "source-protein--123456789abc"
CLAIM_ID = "claim-protein-intake--123456789abc"
EVIDENCE_ID = "evidence-protein-intake--123456789abc"


class QuestionRelevanceMappingTests(unittest.TestCase):
    def test_no_active_questions_skips_semantic_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            fixture = create_deterministic_mock_llm_fixture(mode="valid")

            result = run_question_relevance_mapping_and_update(
                space_root=space_root,
                source_id=SOURCE_ID,
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=ArtifactTransaction(),
            )

            self.assertEqual(result.status, "no_active_questions")
            self.assertEqual(result.attempt_count, 0)
            self.assertEqual(fixture.call_count, 0)

    def test_mapping_updates_active_question_links_and_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-protein-intake", 1),
            )
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-inactive", 2, status="inactive"),
            )
            payload = {
                "schema_version": "question_relevance_mapping_v1",
                "source_id": SOURCE_ID,
                "question_matches": [
                    {
                        "question_id": "question-protein-intake",
                        "relevance": "high",
                        "rationale": "The fixture source directly discusses protein intake.",
                        "claim_ids": [CLAIM_ID],
                        "evidence_ids": [EVIDENCE_ID],
                    }
                ],
                "warnings": [],
            }
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)

            transaction = ArtifactTransaction()
            result = run_question_relevance_mapping_and_update(
                space_root=space_root,
                source_id=SOURCE_ID,
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=transaction,
            )
            transaction.commit()

            self.assertEqual(result.status, "mapped")
            self.assertEqual(result.matched_question_ids, ("question-protein-intake",))
            self.assertEqual(result.updated_question_paths, (question_path,))
            self.assertEqual(result.attempt_count, 1)
            updated = json.loads(question_path.read_text())
            self.assertEqual(updated["linked_source_ids"], [SOURCE_ID])
            self.assertEqual(updated["claim_ids"], [CLAIM_ID])
            self.assertEqual(updated["evidence_ids"], [EVIDENCE_ID])
            self.assertEqual(
                updated["freshness"]["question_relevance_mappings"][0]["source_id"],
                SOURCE_ID,
            )

    def test_mapping_rejects_inactive_or_invented_question_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-protein-intake", 1, status="inactive"),
            )
            fixture = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload={
                    "schema_version": "question_relevance_mapping_v1",
                    "source_id": SOURCE_ID,
                    "question_matches": [
                        {
                            "question_id": "question-protein-intake",
                            "relevance": "high",
                            "rationale": "Inactive questions cannot be mapped.",
                            "claim_ids": [CLAIM_ID],
                            "evidence_ids": [EVIDENCE_ID],
                        }
                    ],
                    "warnings": [],
                },
            )

            result = run_question_relevance_mapping_and_update(
                space_root=space_root,
                source_id=SOURCE_ID,
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=ArtifactTransaction(),
            )

            self.assertEqual(result.status, "no_active_questions")
            self.assertEqual(fixture.call_count, 0)

            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-active", 2),
            )
            with self.assertRaisesRegex(ValueError, "active prepared question"):
                run_question_relevance_mapping_and_update(
                    space_root=space_root,
                    source_id=SOURCE_ID,
                    run_id="run-20260501T120000Z--abcdefghij",
                    llm_client=fixture,
                    transaction=ArtifactTransaction(),
                )

    def test_mapping_rejects_claims_from_other_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root, claim_source_id="source-other--123456789abc")
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload("question-protein-intake", 1),
            )
            fixture = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload={
                    "schema_version": "question_relevance_mapping_v1",
                    "source_id": SOURCE_ID,
                    "question_matches": [
                        {
                            "question_id": "question-protein-intake",
                            "relevance": "high",
                            "rationale": "The claim belongs to another source.",
                            "claim_ids": [CLAIM_ID],
                            "evidence_ids": [],
                        }
                    ],
                    "warnings": [],
                },
            )

            with self.assertRaisesRegex(ValueError, "newly ingested source_id"):
                run_question_relevance_mapping_and_update(
                    space_root=space_root,
                    source_id=SOURCE_ID,
                    run_id="run-20260501T120000Z--abcdefghij",
                    llm_client=fixture,
                    transaction=ArtifactTransaction(),
                )


def _question_payload(question_id: str, display_order: int, *, status: str = "active") -> dict[str, object]:
    return {
        "schema_version": "prepared_question_v1",
        "question_id": question_id,
        "question": "What protein intake supports muscle growth?",
        "status": status,
        "display_order": display_order,
        "scope": {"space_name": "alpha"},
        "linked_source_ids": [],
        "claim_ids": [],
        "evidence_ids": [],
        "measurement_ids": [],
        "synthesis": {},
        "freshness": {},
        "warnings": [],
    }


def _write_linked_artifacts(space_root: Path, *, claim_source_id: str = SOURCE_ID) -> None:
    source_path = space_root / "sources" / "records" / f"{SOURCE_ID}.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(json.dumps({"source_id": SOURCE_ID}, indent=2, sort_keys=True) + "\n")
    claim_path = space_root / "claims" / f"{CLAIM_ID}.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps({"claim_id": CLAIM_ID, "source_id": claim_source_id}, indent=2, sort_keys=True) + "\n"
    )
    evidence_path = space_root / "evidence" / f"{EVIDENCE_ID}.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps({"evidence_id": EVIDENCE_ID, "source_id": SOURCE_ID}, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    unittest.main()
