from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import create_deterministic_mock_llm_fixture

from sapi.core.transactions import ArtifactTransaction
from sapi.questions.prepared_questions import load_prepared_questions, write_prepared_question_record
from sapi.questions.synthesis import (
    build_question_synthesis_context,
    refresh_question_syntheses,
    run_question_synthesis_and_update,
)


SOURCE_ID = "source-protein--123456789abc"
OTHER_SOURCE_ID = "source-other--123456789abc"
CLAIM_ID = "claim-protein-intake--123456789abc"
EVIDENCE_ID = "evidence-protein-intake--123456789abc"


class QuestionSynthesisTests(unittest.TestCase):
    def test_synthesis_refresh_writes_semantic_output_and_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    "question-protein-intake",
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _synthesis_payload("question-protein-intake")
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)
            transaction = ArtifactTransaction()

            result = run_question_synthesis_and_update(
                space_root=space_root,
                question_id="question-protein-intake",
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client=fixture,
                transaction=transaction,
            )
            transaction.commit()

            self.assertEqual(result.status, "refreshed")
            self.assertEqual(result.attempt_count, 1)
            self.assertTrue(result.refreshed)
            self.assertTrue(result.semantic_output_path.is_file() if result.semantic_output_path else False)
            updated = json.loads(question_path.read_text())
            self.assertEqual(updated["synthesis"]["short_answer"], payload["short_answer"])
            self.assertEqual(
                updated["freshness"]["question_synthesis"]["semantic_output_path"],
                "runs/run-20260501T120000Z--abcdefghij/semantic/question_synthesis/question-protein-intake.json",
            )
            self.assertEqual(updated["freshness"]["question_synthesis"]["input_signature"], result.input_signature)

    def test_unchanged_signature_skips_semantic_regeneration_and_records_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            question_path = write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    "question-protein-intake",
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            question = load_prepared_questions(space_root)[0]
            signature = build_question_synthesis_context(space_root=space_root, question=question).input_signature
            seed = json.loads(question_path.read_text())
            seed["freshness"]["question_synthesis"] = {
                "status": "refreshed",
                "run_id": "run-previous",
                "input_signature": signature,
                "semantic_output_path": "runs/run-previous/semantic/question_synthesis/question-protein-intake.json",
                "refreshed_at": "2026-05-01T12:00:00Z",
            }
            write_prepared_question_record(space_root=space_root, space_name="alpha", payload=seed)
            fixture = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload=_synthesis_payload("question-protein-intake"),
            )
            transaction = ArtifactTransaction()

            result = run_question_synthesis_and_update(
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
            self.assertEqual(updated["freshness"]["question_synthesis"]["status"], "unchanged")
            self.assertEqual(
                updated["freshness"]["question_synthesis"]["semantic_output_path"],
                "runs/run-previous/semantic/question_synthesis/question-protein-intake.json",
            )
            self.assertEqual(updated["freshness"]["question_synthesis_checks"][-1]["status"], "unchanged")

    def test_refresh_api_selects_stale_questions_without_forcing_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    "question-protein-intake",
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            fixture = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload=_synthesis_payload("question-protein-intake"),
            )
            transaction = ArtifactTransaction()

            results = refresh_question_syntheses(
                space_root=space_root,
                run_id="run-20260501T120000Z--abcdefghij",
                llm_client_factory=lambda _context: fixture,
                transaction=transaction,
                question_ids=["question-protein-intake"],
            )
            transaction.commit()

            self.assertEqual([result.status for result in results], ["refreshed"])
            self.assertEqual(fixture.call_count, 1)

    def test_synthesis_rejects_unlinked_canonical_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_linked_artifacts(space_root)
            write_prepared_question_record(
                space_root=space_root,
                space_name="alpha",
                payload=_question_payload(
                    "question-protein-intake",
                    linked_source_ids=[SOURCE_ID],
                    claim_ids=[CLAIM_ID],
                    evidence_ids=[EVIDENCE_ID],
                ),
            )
            payload = _synthesis_payload("question-protein-intake")
            payload["conclusions"][0]["source_ids"] = [OTHER_SOURCE_ID]  # type: ignore[index]
            fixture = create_deterministic_mock_llm_fixture(mode="valid", valid_payload=payload)

            with self.assertRaisesRegex(ValueError, "unlinked canonical ID"):
                run_question_synthesis_and_update(
                    space_root=space_root,
                    question_id="question-protein-intake",
                    run_id="run-20260501T120000Z--abcdefghij",
                    llm_client=fixture,
                    transaction=ArtifactTransaction(),
                )


def _question_payload(
    question_id: str,
    *,
    linked_source_ids: list[str] | None = None,
    claim_ids: list[str] | None = None,
    evidence_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "prepared_question_v1",
        "question_id": question_id,
        "question": "What protein intake supports muscle growth?",
        "status": "active",
        "display_order": 1,
        "scope": {"space_name": "alpha"},
        "linked_source_ids": linked_source_ids or [],
        "claim_ids": claim_ids or [],
        "evidence_ids": evidence_ids or [],
        "measurement_ids": [],
        "synthesis": {},
        "freshness": {},
        "warnings": [],
    }


def _synthesis_payload(question_id: str) -> dict[str, object]:
    return {
        "schema_version": "question_synthesis_v1",
        "question_id": question_id,
        "short_answer": "Current evidence supports a cautious protein-intake conclusion.",
        "conclusions": [
            {
                "text": "Protein intake is relevant when paired with resistance training.",
                "support": "moderate",
                "source_ids": [SOURCE_ID],
                "claim_ids": [CLAIM_ID],
                "evidence_ids": [EVIDENCE_ID],
            }
        ],
        "uncertainty": "Training status and diet context may change the estimate.",
        "disagreements": [],
        "citation_anchors": [
            {
                "anchor_id": "anchor-protein",
                "label": "[S1]",
                "source_id": SOURCE_ID,
                "claim_ids": [CLAIM_ID],
                "evidence_ids": [EVIDENCE_ID],
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
            {"evidence_id": EVIDENCE_ID, "source_id": SOURCE_ID, "excerpt": "Protein intake evidence."},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


if __name__ == "__main__":
    unittest.main()
