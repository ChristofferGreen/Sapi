from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import scripts.generate_profiles as generate_profiles
import scripts.create_prepared_questions as create_prepared_questions
import scripts.ingest_source as ingest_source
from tests.conftest import (
    assert_no_run_containers,
    bootstrap_site_and_space,
    write_source_fixture,
)


class SemanticRepairExhaustionRollbackIntegrationTests(unittest.TestCase):
    def test_semantic_repair_exhaustion_rolls_back_default_ingest_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(tmp_root, content="repair exhaustion fixture\n")

            stderr = io.StringIO()
            argv = [
                "ingest_source.py",
                "alpha",
                str(source_path),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--mock-llm",
            ]
            # Return schema-invalid semantic output for every attempt to force retry exhaustion.
            with patch.object(
                ingest_source._MockIngestExtractionClient,
                "generate_semantic_json",
                return_value=json.dumps({"claims": [], "relations": []}),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = ingest_source.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("semantic flow", stderr.getvalue().lower())

            self.assertEqual(list((space_root / "sources" / "records").glob("*.json")), [])
            self.assertEqual(list((space_root / "claims").glob("*.json")), [])
            self.assertEqual(list((space_root / "relations").glob("*.json")), [])
            self.assertEqual(list((space_root / "topics").glob("*.json")), [])
            assert_no_run_containers(space_root)

    def test_question_mapping_repair_exhaustion_rolls_back_default_ingest_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            questions_tsv = tmp_root / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
            )
            with patch(
                "sys.argv",
                [
                    "create_prepared_questions.py",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--questions-tsv",
                    str(questions_tsv),
                ],
            ):
                self.assertEqual(create_prepared_questions.main(), 0)
            question_path = space_root / "questions" / "question-protein-intake.json"
            original_question_text = question_path.read_text()
            source_path = write_source_fixture(tmp_root, content="question mapping repair exhaustion fixture\n")

            stderr = io.StringIO()
            argv = [
                "ingest_source.py",
                "alpha",
                str(source_path),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--mock-llm",
            ]
            with patch.object(
                ingest_source._MockQuestionRelevanceMappingClient,
                "generate_semantic_json",
                return_value=json.dumps({"question_matches": []}),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = ingest_source.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("question_relevance_mapping", stderr.getvalue())
            self.assertEqual(question_path.read_text(), original_question_text)
            self.assertEqual(list((space_root / "sources" / "records").glob("*.json")), [])
            self.assertEqual(list((space_root / "claims").glob("*.json")), [])
            self.assertEqual(list((space_root / "evidence").glob("*.json")), [])
            self.assertEqual(list((space_root / "topics").glob("*.json")), [])
            assert_no_run_containers(space_root)

    def test_question_synthesis_repair_exhaustion_rolls_back_default_ingest_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            questions_tsv = tmp_root / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
            )
            with patch(
                "sys.argv",
                [
                    "create_prepared_questions.py",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--questions-tsv",
                    str(questions_tsv),
                ],
            ):
                self.assertEqual(create_prepared_questions.main(), 0)
            question_path = space_root / "questions" / "question-protein-intake.json"
            original_question_text = question_path.read_text()
            source_path = write_source_fixture(tmp_root, content="question synthesis repair fixture\n")

            stderr = io.StringIO()
            argv = [
                "ingest_source.py",
                "alpha",
                str(source_path),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--mock-llm",
            ]
            with patch.object(
                ingest_source._MockQuestionSynthesisClient,
                "generate_semantic_json",
                return_value=json.dumps({"question_id": "question-protein-intake"}),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = ingest_source.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("question_synthesis", stderr.getvalue())
            self.assertEqual(question_path.read_text(), original_question_text)
            self.assertEqual(list((space_root / "sources" / "records").glob("*.json")), [])
            self.assertEqual(list((space_root / "claims").glob("*.json")), [])
            self.assertEqual(list((space_root / "evidence").glob("*.json")), [])
            self.assertEqual(list((space_root / "topics").glob("*.json")), [])
            assert_no_run_containers(space_root)

    def test_question_measurement_repair_exhaustion_rolls_back_default_ingest_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            questions_tsv = tmp_root / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
            )
            with patch(
                "sys.argv",
                [
                    "create_prepared_questions.py",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--questions-tsv",
                    str(questions_tsv),
                ],
            ):
                self.assertEqual(create_prepared_questions.main(), 0)
            question_path = space_root / "questions" / "question-protein-intake.json"
            original_question_text = question_path.read_text()
            source_path = write_source_fixture(tmp_root, content="question measurement repair fixture\n")

            stderr = io.StringIO()
            argv = [
                "ingest_source.py",
                "alpha",
                str(source_path),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--mock-llm",
            ]
            with patch.object(
                ingest_source._MockQuestionMeasurementClient,
                "generate_semantic_json",
                return_value=json.dumps({"question_id": "question-protein-intake"}),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = ingest_source.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("question_measurement_extraction", stderr.getvalue())
            self.assertEqual(question_path.read_text(), original_question_text)
            self.assertEqual(list((space_root / "sources" / "records").glob("*.json")), [])
            self.assertEqual(list((space_root / "claims").glob("*.json")), [])
            self.assertEqual(list((space_root / "evidence").glob("*.json")), [])
            self.assertEqual(list((space_root / "measurements").glob("*.json")), [])
            self.assertEqual(list((space_root / "topics").glob("*.json")), [])
            assert_no_run_containers(space_root)

    def test_semantic_repair_exhaustion_rolls_back_default_profile_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            stderr = io.StringIO()
            argv = [
                "generate_profiles.py",
                "alpha",
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--mock-llm",
            ]
            # Return schema-invalid semantic output for every attempt to force retry exhaustion.
            with patch.object(
                generate_profiles._MockPersonaProfileClient,
                "generate_semantic_json",
                return_value=json.dumps({"persona_id": "broken"}),
            ):
                with patch("sys.argv", argv):
                    with redirect_stderr(stderr):
                        exit_code = generate_profiles.main()

            self.assertNotEqual(exit_code, 0)
            self.assertIn("semantic flow", stderr.getvalue().lower())
            self.assertEqual(list((space_root / "profiles").glob("persona-*.json")), [])
            self.assertEqual(list((space_root / "outputs" / "persona_profile_history").glob("*.json")), [])
            assert_no_run_containers(space_root)


if __name__ == "__main__":
    unittest.main()
