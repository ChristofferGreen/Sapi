from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    assert_lint_artifact,
    bootstrap_site_and_space,
    latest_run_directory,
    parse_run_frontmatter,
    run_command,
    write_source_fixture,
)


class RefreshQuestionsWrapperTests(unittest.TestCase):
    def test_wrapper_rejects_invalid_arguments(self) -> None:
        result = run_command(["bash", str(REPO_ROOT / "refresh_questions.sh")])

        self.assertEqual(result.returncode, 2)
        self.assertIn("Usage: refresh_questions.sh", result.stderr)

    def test_wrapper_refreshes_stale_questions_and_records_run_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            questions_tsv = tmp_root / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
            )
            create_result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                ]
            )
            self.assertEqual(create_result.returncode, 0, msg=create_result.stderr)
            source_path = write_source_fixture(
                tmp_root,
                content="protein intake fixture for question refresh\n",
            )
            ingest_result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "ingest.sh"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)

            stale_only_result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "refresh_questions.sh"),
                    str(site_path),
                    "alpha",
                    "--mock-llm",
                ]
            )

            self.assertEqual(stale_only_result.returncode, 0, msg=stale_only_result.stderr)
            self.assertIn("question_syntheses_unchanged=1", stale_only_result.stdout)
            space_root = site_path / "spaces" / "alpha"
            stale_only_run = latest_run_directory(space_root)
            stale_only_frontmatter = parse_run_frontmatter(stale_only_run / "run.md")
            self.assertEqual(stale_only_frontmatter["flow_key"], "question_pipeline")
            self.assertEqual(stale_only_frontmatter["semantic_flows"], [])
            self.assertEqual(stale_only_frontmatter["question_syntheses_changed"], 0)
            self.assertEqual(stale_only_frontmatter["question_syntheses_unchanged"], 1)
            assert_lint_artifact(
                stale_only_run / "lint.json",
                expected_workflow="refresh_questions",
                expected_error_count=0,
            )

            force_result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "refresh_questions.sh"),
                    str(site_path),
                    "alpha",
                    "--question-id",
                    "question-protein-intake",
                    "--force",
                    "--mock-llm",
                ]
            )

            self.assertEqual(force_result.returncode, 0, msg=force_result.stderr)
            force_run = latest_run_directory(space_root)
            force_frontmatter = parse_run_frontmatter(force_run / "run.md")
            self.assertEqual(force_frontmatter["flow_key"], "question_pipeline")
            self.assertEqual(force_frontmatter["semantic_flows"], ["question_synthesis"])
            self.assertEqual(force_frontmatter["semantic_flow_invocation_counts"], {"question_synthesis": 1})
            self.assertEqual(force_frontmatter["question_syntheses_changed"], 1)
            question_payload = json.loads(
                (space_root / "questions" / "question-protein-intake.json").read_text()
            )
            self.assertEqual(
                question_payload["freshness"]["question_synthesis"]["run_id"],
                force_run.name,
            )


if __name__ == "__main__":
    unittest.main()
