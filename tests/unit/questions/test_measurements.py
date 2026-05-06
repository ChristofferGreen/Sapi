from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import create_deterministic_mock_llm_fixture

from sapi.core.transactions import ArtifactTransaction
from sapi.llm.semantic_executor import SemanticFlowError
from sapi.questions.measurements import (
    build_question_measurement_context,
    refresh_question_measurements,
    run_question_measurement_extraction_and_update,
)
from sapi.questions.prepared_questions import load_prepared_questions, write_prepared_question_record


SOURCE_ID = "source-protein--123456789abc"
OTHER_SOURCE_ID = "source-other--123456789abc"
CLAIM_ID = "claim-protein-intake--123456789abc"
EVIDENCE_ID = "evidence-protein-intake--123456789abc"
MEASUREMENT_ID = "measurement-protein-intake--123456789abc"


class QuestionMeasurementTests(unittest.TestCase):
    def test_measurement_refresh_writes_rows_and_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _measurement_payload("question-protein-intake")
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)
            transaction = ArtifactTransaction()

            result = run_question_measurement_extraction_and_update(
                space_root=space_root,
                question_id="question-protein-intake",
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=transaction,
            )
            transaction.commit()

            self.assertEqual(result.status, "refreshed")
            self.assertEqual(result.attempt_count, 1)
            self.assertEqual(result.measurement_ids, (MEASUREMENT_ID,))
            self.assertEqual(result.chart_group_count, 1)
            self.assertTrue(result.semantic_output_path.is_file() if result.semantic_output_path else False)
            measurement = json.loads((space_root / "measurements" / f"{MEASUREMENT_ID}.json").read_text())
            self.assertEqual(measurement["source_id"], SOURCE_ID)
            self.assertEqual(measurement["claim_id"], CLAIM_ID)
            self.assertEqual(measurement["evidence_id"], EVIDENCE_ID)
            self.assertEqual(
                measurement["question_relevance"],
                "This range directly calibrates the answer for the prepared question.",
            )
            updated = json.loads(question_path.read_text())
            self.assertEqual(updated["measurement_ids"], [MEASUREMENT_ID])
            self.assertEqual(
                updated["freshness"]["question_measurement_extraction"]["semantic_output_path"],
                (
                    "runs/run-20260501T120000Z--abcdefghij/semantic/"
                    "question_measurement_extraction/question-protein-intake.json"
                ),
            )
            self.assertEqual(
                updated["freshness"]["question_measurement_extraction"]["input_signature"],
                result.input_signature,
            )

    def test_unchanged_signature_skips_semantic_regeneration_and_records_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            question = load_prepared_questions(space_root)[0]
            signature = build_question_measurement_context(
                space_root=space_root,
                question=question,
            ).input_signature
            seed = json.loads(question_path.read_text())
            seed["freshness"]["question_measurement_extraction"] = {
                "status": "refreshed",
                "run_id": "run-previous",
                "input_signature": signature,
                "semantic_output_path": (
                    "runs/run-previous/semantic/question_measurement_extraction/"
                    "question-protein-intake.json"
                ),
                "refreshed_at": "2026-05-01T12:00:00Z",
                "measurement_ids": [],
                "chart_groups": [],
                "warnings": [],
            }
            write_prepared_question_record(space_root=space_root, space_name="alpha", payload=seed)
            fixture = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload=_measurement_payload("question-protein-intake"),
            )
            transaction = ArtifactTransaction()

            result = run_question_measurement_extraction_and_update(
                space_root=space_root,
                question_id="question-protein-intake",
                run_id="run-20260501T130000Z--abcdefghij",
                llm_client=fixture,
                transaction=transaction,
            )
            transaction.commit()

            self.assertEqual(result.status, "unchanged")
            self.assertEqual(result.attempt_count, 0)
            self.assertEqual(fixture.call_count, 0)
            updated = json.loads(question_path.read_text())
            self.assertEqual(updated["freshness"]["question_measurement_extraction"]["status"], "unchanged")
            self.assertEqual(
                updated["freshness"]["question_measurement_extraction_checks"][-1]["status"],
                "unchanged",
            )

    def test_refresh_api_records_no_linked_context_without_calling_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(),
            )
            fixture = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload=_measurement_payload("question-protein-intake"),
            )
            transaction = ArtifactTransaction()

            results = refresh_question_measurements(
                space_root=space_root,
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client_factory=lambda _context: fixture,
                transaction=transaction,
                question_ids=["question-protein-intake"],
            )
            transaction.commit()

            self.assertEqual([result.status for result in results], ["no_linked_context"])
            self.assertEqual(fixture.call_count, 0)

    def test_empty_measurement_output_is_persisted_as_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            _write_measurement_record(space_root=space_root, question_id="question-protein-intake")
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                    measurement_ids=[MEASUREMENT_ID],
                ),
            )
            payload = _measurement_payload("question-protein-intake")
            payload["measurements"] = []
            payload["chart_groups"] = []
            payload["warnings"] = ["No numeric measurement was explicit."]
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)
            transaction = ArtifactTransaction()

            result = run_question_measurement_extraction_and_update(
                space_root=space_root,
                question_id="question-protein-intake",
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=transaction,
            )
            transaction.commit()

            self.assertTrue(result.refreshed)
            updated = json.loads(question_path.read_text())
            self.assertEqual(updated["measurement_ids"], [])
            self.assertEqual(
                updated["freshness"]["question_measurement_extraction"]["warnings"],
                ["No numeric measurement was explicit."],
            )
            self.assertFalse((space_root / "measurements" / f"{MEASUREMENT_ID}.json").exists())

    def test_measurement_refresh_remaps_foreign_measurement_id_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            _write_measurement_record(space_root=space_root, question_id="question-other")
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            fixture = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload=_measurement_payload("question-protein-intake"),
            )
            transaction = ArtifactTransaction()

            result = run_question_measurement_extraction_and_update(
                space_root=space_root,
                question_id="question-protein-intake",
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=transaction,
            )
            transaction.commit()

            measurement = json.loads((space_root / "measurements" / f"{MEASUREMENT_ID}.json").read_text())
            self.assertEqual(measurement["question_id"], "question-other")
            self.assertEqual(len(result.measurement_ids), 1)
            remapped_id = result.measurement_ids[0]
            self.assertNotEqual(remapped_id, MEASUREMENT_ID)
            self.assertTrue(remapped_id.startswith("measurement-protein-intake--"))
            remapped_measurement = json.loads((space_root / "measurements" / f"{remapped_id}.json").read_text())
            self.assertEqual(remapped_measurement["question_id"], "question-protein-intake")
            updated = json.loads(question_path.read_text())
            self.assertEqual(updated["measurement_ids"], [remapped_id])
            self.assertIn(
                "Remapped measurement IDs that collided with existing measurements owned by other questions.",
                updated["freshness"]["question_measurement_extraction"]["warnings"],
            )
            semantic_output = json.loads(result.semantic_output_path.read_text())
            self.assertEqual(semantic_output["measurements"][0]["measurement_id"], remapped_id)
            self.assertEqual(semantic_output["chart_groups"][0]["measurement_ids"], [remapped_id])

    def test_measurement_extraction_rejects_unlinked_rows_and_drops_incompatible_charts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _measurement_payload("question-protein-intake")
            payload["measurements"][0]["source_id"] = OTHER_SOURCE_ID  # type: ignore[index]
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)

            with self.assertRaisesRegex(ValueError, "unlinked source"):
                run_question_measurement_extraction_and_update(
                    space_root=space_root,
                    question_id="question-protein-intake",
                    run_id="run-20260501T120000Z--abcdefghij",
                    llm_client=fixture,
                    transaction=ArtifactTransaction(),
                )

        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _measurement_payload("question-protein-intake")
            payload["chart_groups"][0]["unit"] = "kg/day"  # type: ignore[index]
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)

            result = run_question_measurement_extraction_and_update(
                space_root=space_root,
                question_id="question-protein-intake",
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=ArtifactTransaction(),
            )

            self.assertEqual(result.chart_group_count, 0)
            question = json.loads((space_root / "questions" / "question-protein-intake.json").read_text())
            metadata = question["freshness"]["question_measurement_extraction"]
            self.assertEqual(metadata["chart_groups"], [])
            self.assertIn("Dropped incompatible question measurement chart group.", metadata["warnings"])

    def test_measurement_extraction_rejects_missing_question_relevance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _measurement_payload("question-protein-intake")
            payload["measurements"][0]["question_relevance"] = "   "  # type: ignore[index]
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)

            with self.assertRaisesRegex(ValueError, "question_relevance"):
                run_question_measurement_extraction_and_update(
                    space_root=space_root,
                    question_id="question-protein-intake",
                    run_id="run-20260501T120000Z--abcdefghij",
                    llm_client=fixture,
                    transaction=ArtifactTransaction(),
                )

    def test_measurement_extraction_rejects_too_many_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _measurement_payload("question-protein-intake")
            seed_measurement = payload["measurements"][0]  # type: ignore[index]
            payload["measurements"] = [
                {
                    **seed_measurement,
                    "measurement_id": f"measurement-protein-intake-{index}--123456789abc",
                    "value": 1.0 + index,
                }
                for index in range(7)
            ]
            payload["chart_groups"] = []
            fixture = create_deterministic_mock_llm_fixture(
                mode="repair_exhausted",
                invalid_output=json.dumps(payload),
            )

            with self.assertRaisesRegex(SemanticFlowError, "question_measurement_extraction"):
                run_question_measurement_extraction_and_update(
                    space_root=space_root,
                    question_id="question-protein-intake",
                    run_id="run-20260501T120000Z--abcdefghij",
                    llm_client=fixture,
                    transaction=ArtifactTransaction(),
                )

    def test_measurement_extraction_repair_exhausts_when_numeric_value_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _measurement_payload("question-protein-intake")
            del payload["measurements"][0]["value"]  # type: ignore[index]
            fixture = create_deterministic_mock_llm_fixture(
                mode="repair_exhausted",
                invalid_output=json.dumps(payload),
            )

            with self.assertRaisesRegex(SemanticFlowError, "question_measurement_extraction"):
                run_question_measurement_extraction_and_update(
                    space_root=space_root,
                    question_id="question-protein-intake",
                    run_id="run-20260501T120000Z--abcdefghij",
                    llm_client=fixture,
                    transaction=ArtifactTransaction(),
                )
            self.assertEqual(fixture.call_count, 4)


def _question_payload(
    *,
    linked_source_ids: list[str] | None = None,
    claim_ids: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    measurement_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "prepared_question_v1",
        "question_id": "question-protein-intake",
        "question": "What protein intake supports muscle growth?",
        "status": "active",
        "display_order": 1,
        "scope": {"space_name": "alpha"},
        "linked_source_ids": linked_source_ids or [],
        "claim_ids": claim_ids or [],
        "evidence_ids": evidence_ids or [],
        "measurement_ids": measurement_ids or [],
        "synthesis": {},
        "freshness": {},
        "warnings": [],
    }


def _measurement_payload(question_id: str) -> dict[str, object]:
    return {
        "schema_version": "question_measurement_extraction_v1",
        "question_id": question_id,
        "measurements": [
            {
                "measurement_id": MEASUREMENT_ID,
                "source_id": SOURCE_ID,
                "claim_id": CLAIM_ID,
                "evidence_id": EVIDENCE_ID,
                "measure_name": "protein intake",
                "value": 1.6,
                "value_max": 2.2,
                "unit": "g/kg/day",
                "population": "resistance-trained adults",
                "outcome": "muscle hypertrophy",
                "comparator": "lower intake",
                "uncertainty": "range depends on training context",
                "question_relevance": "This range directly calibrates the answer for the prepared question.",
            }
        ],
        "chart_groups": [
            {
                "chart_group_id": "chart-protein-intake",
                "measure_name": "protein intake",
                "unit": "g/kg/day",
                "outcome": "muscle hypertrophy",
                "population": "resistance-trained adults",
                "measurement_ids": [MEASUREMENT_ID],
            }
        ],
        "warnings": [],
    }


def _write_linked_artifacts(space_root: Path) -> None:
    source_path = space_root / "sources" / "records" / f"{SOURCE_ID}.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        json.dumps({"source_id": SOURCE_ID, "title": "Protein"}, indent=2, sort_keys=True) + "\n"
    )
    claim_path = space_root / "claims" / f"{CLAIM_ID}.json"
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    claim_path.write_text(
        json.dumps(
            {"claim_id": CLAIM_ID, "source_id": SOURCE_ID, "text": "Protein supports growth."},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    evidence_path = space_root / "evidence" / f"{EVIDENCE_ID}.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(
            {"evidence_id": EVIDENCE_ID, "source_id": SOURCE_ID, "excerpt": "Protein intake 1.6-2.2 g/kg/day."},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _write_measurement_record(*, space_root: Path, question_id: str) -> None:
    measurement_path = space_root / "measurements" / f"{MEASUREMENT_ID}.json"
    measurement_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _measurement_payload("question-protein-intake")["measurements"][0]  # type: ignore[index]
    measurement_path.write_text(
        json.dumps(
            {
                "schema_version": "question_measurement_v1",
                "question_id": question_id,
                **payload,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    unittest.main()
