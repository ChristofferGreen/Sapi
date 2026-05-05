from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.core.runtime_flags import RuntimeFlagSnapshot
from sapi.llm.semantic_executor import SemanticFlowError
from sapi.questions.prepared_questions import PreparedQuestion
from sapi.scouting.pipeline import run_source_scouting_and_store
from sapi.scouting.store import (
    append_scouted_candidates,
    candidate_queue,
    load_candidates,
    select_importable_candidates,
    update_candidate_status,
)
from tests.conftest import REPO_ROOT, create_deterministic_mock_llm_fixture


class SourceScoutingCandidateStoreTests(unittest.TestCase):
    def test_appends_candidates_and_selects_public_importables_by_rank(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = candidate_queue(
                site_path=Path(tmp) / "site",
                space_name="alpha",
                question_id="question-alpha",
            )

            append_scouted_candidates(
                queue=queue,
                semantic_payload=_semantic_payload(count=3),
                run_id="run-001",
                semantic_output_path=queue.runs_root / "run-001" / "source_scouting.json",
                scouted_at="2026-05-05T00:00:00Z",
            )

            candidates = load_candidates(queue)
            self.assertEqual([candidate["ranking"]["rank"] for candidate in candidates], [1, 2, 3])
            importable = select_importable_candidates(queue=queue, count=2)
            self.assertEqual(len(importable), 2)
            self.assertTrue(all(candidate["public_access"]["has_public_pdf"] for candidate in importable))
            self.assertTrue((queue.root / "queue.json").is_file())

    def test_duplicate_doi_candidates_are_normalized_to_one_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = candidate_queue(
                site_path=Path(tmp) / "site",
                space_name="alpha",
                question_id="question-alpha",
            )
            payload = _semantic_payload(count=2)
            payload["candidates"][1]["doi"] = payload["candidates"][0]["doi"]

            written = append_scouted_candidates(
                queue=queue,
                semantic_payload=payload,
                run_id="run-001",
                semantic_output_path=queue.runs_root / "run-001" / "source_scouting.json",
                scouted_at="2026-05-05T00:00:00Z",
            )

            self.assertEqual(len(written), 1)
            self.assertEqual(len(load_candidates(queue)), 1)

    def test_successful_import_status_clears_stale_failure_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            queue = candidate_queue(
                site_path=Path(tmp) / "site",
                space_name="alpha",
                question_id="question-alpha",
            )
            candidate = append_scouted_candidates(
                queue=queue,
                semantic_payload=_semantic_payload(count=1),
                run_id="run-001",
                semantic_output_path=queue.runs_root / "run-001" / "source_scouting.json",
                scouted_at="2026-05-05T00:00:00Z",
            )[0]

            update_candidate_status(
                queue=queue,
                candidate_id=candidate["candidate_id"],
                import_status="failed",
                failure_reason="transient validation failure",
            )
            updated = update_candidate_status(
                queue=queue,
                candidate_id=candidate["candidate_id"],
                import_status="imported",
            )

            self.assertIsNone(updated["failure_reason"])

    def test_semantic_repair_attempt_count_is_recorded_in_run_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site"
            space_root = site_path / "spaces" / "alpha"
            (space_root / "questions").mkdir(parents=True)
            question = _question(space_root=space_root)
            question.path.write_text("{}")
            queue = candidate_queue(site_path=site_path, space_name="alpha", question_id=question.question_id)
            client = create_deterministic_mock_llm_fixture(
                mode="invalid_then_repair",
                invalid_output="{}",
                valid_payload=_semantic_payload(count=1),
            )

            result = run_source_scouting_and_store(
                repo_root=REPO_ROOT,
                site_path=site_path,
                space_root=space_root,
                queue=queue,
                question=question,
                run_id="run-001",
                count=1,
                runtime_flags=_runtime_flags(mock_llm=True),
                llm_client=client,
            )

            run_payload = json.loads(result.run_record_path.read_text())
            self.assertEqual(result.attempt_count, 2)
            self.assertEqual(run_payload["llm_attempt_count"], 2)
            self.assertEqual(run_payload["semantic_flow_invocation_counts"], {"source_scouting": 1})

    def test_semantic_repair_exhaustion_writes_no_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site"
            space_root = site_path / "spaces" / "alpha"
            (space_root / "questions").mkdir(parents=True)
            question = _question(space_root=space_root)
            question.path.write_text("{}")
            queue = candidate_queue(site_path=site_path, space_name="alpha", question_id=question.question_id)
            client = create_deterministic_mock_llm_fixture(mode="repair_exhausted", invalid_output="{}")

            with self.assertRaises(SemanticFlowError):
                run_source_scouting_and_store(
                    repo_root=REPO_ROOT,
                    site_path=site_path,
                    space_root=space_root,
                    queue=queue,
                    question=question,
                    run_id="run-001",
                    count=1,
                    runtime_flags=_runtime_flags(mock_llm=True),
                    llm_client=client,
                )

            self.assertEqual(load_candidates(queue), [])


def _semantic_payload(*, count: int) -> dict[str, object]:
    return {
        "schema_version": "source_scouting_v1",
        "space_name": "alpha",
        "question_id": "question-alpha",
        "question_text": "Which papers answer alpha?",
        "candidates": [_candidate(index) for index in range(1, count + 1)],
        "warnings": [],
    }


def _candidate(index: int) -> dict[str, object]:
    return {
        "title": f"Alpha Paper {index}",
        "authors": ["A. Researcher"],
        "venue": {
            "name": "Journal of Alpha",
            "type": "journal",
            "publisher": "Alpha Press",
            "reputation_rationale": "Reputable fixture journal.",
        },
        "publication_year": 2024,
        "doi": f"10.1234/alpha-{index}",
        "landing_url": f"https://example.test/alpha-{index}",
        "pdf_url": f"https://example.test/alpha-{index}.pdf",
        "public_access": {
            "has_public_pdf": True,
            "access_status": "public_pdf",
            "evidence": "Fixture PDF URL is public.",
        },
        "citation_signal": {
            "count": 100 - index,
            "provider": "fixture",
            "as_of": "2026-05-05",
            "confidence": "high",
        },
        "ranking": {
            "rank": index,
            "answer_fit_score": 5,
            "venue_reputation_score": 4,
            "citation_score": 4,
            "interestingness_score": 4,
            "overall_score": 17,
            "answer_fit_rationale": "Answers the fixture question.",
            "interestingness_rationale": "Interesting fixture rationale.",
            "overall_rationale": "Strong fixture candidate.",
        },
    }


def _question(*, space_root: Path) -> PreparedQuestion:
    return PreparedQuestion(
        question_id="question-alpha",
        question="Which papers answer alpha?",
        status="active",
        display_order=1,
        scope_space_name="alpha",
        linked_source_ids=(),
        claim_ids=(),
        evidence_ids=(),
        measurement_ids=(),
        synthesis={},
        freshness={},
        warnings=(),
        path=space_root / "questions" / "question-alpha.json",
    )


def _runtime_flags(*, mock_llm: bool) -> RuntimeFlagSnapshot:
    return RuntimeFlagSnapshot(
        llm_backend="codex",
        llm_model="gpt-test",
        llm_reasoning_effort="low",
        llm_timeout_secs=None,
        llm_trace=False,
        llm_trace_dir=None,
        trace_llm_io=False,
        mock_llm=mock_llm,
        warning_budget=200,
        run_search_visibility="auto",
        site_presentation_mode="public",
        enable_source_index=False,
    )


if __name__ == "__main__":
    unittest.main()
