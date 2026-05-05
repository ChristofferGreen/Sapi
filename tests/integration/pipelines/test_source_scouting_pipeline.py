from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, run_command


class SourceScoutingPipelineIntegrationTests(unittest.TestCase):
    def test_mock_scouting_imports_public_candidate_into_deterministic_site(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            run_command(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "Example Site"], check=True)
            run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_space.sh"),
                    str(site_path),
                    "compilers",
                    "--seed-example-questions",
                ],
                check=True,
            )

            scout = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "scout_sources.sh"),
                    str(site_path),
                    "compilers",
                    "question-profile-guided-optimization",
                    "--count",
                    "1",
                    "--mock-llm",
                    "--mock-candidate-plan",
                    str(REPO_ROOT / "tests" / "example" / "scouting_plan.tsv"),
                ]
            )
            self.assertEqual(scout.returncode, 0, msg=scout.stderr)
            self.assertIn("candidate_count=1", scout.stdout)

            imported = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "import_scouted_sources.sh"),
                    str(site_path),
                    "compilers",
                    "--question-id",
                    "question-profile-guided-optimization",
                    "--count",
                    "1",
                    "--mock-llm",
                ]
            )
            self.assertEqual(imported.returncode, 0, msg=imported.stderr)
            self.assertIn("imported=['candidate-", imported.stdout)

            records = sorted((site_path / "spaces" / "compilers" / "sources" / "records").glob("source-*.json"))
            self.assertEqual(len(records), 1)
            source_id = records[0].stem
            source_page = site_path / "spaces" / "compilers" / "site" / "sources" / f"{source_id}.html"
            self.assertTrue(source_page.is_file())
            candidate = json.loads(
                sorted(
                    (
                        site_path
                        / "scouting"
                        / "spaces"
                        / "compilers"
                        / "questions"
                        / "question-profile-guided-optimization"
                        / "candidates"
                    ).glob("candidate-*.json")
                )[0].read_text()
            )
            self.assertEqual(candidate["import_status"], "imported")
            self.assertEqual(candidate["import_link"]["source_id"], source_id)

    def test_restricted_source_ingest_hides_public_file_and_source_text_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            run_command(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "Restricted Site"], check=True)
            run_command(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "alpha"], check=True)
            pdf_path = (
                REPO_ROOT
                / "tests"
                / "example"
                / "pdfs"
                / "mind"
                / "01-an-information-integration-theory-of-consciousness--w2114900706.pdf"
            )

            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "ingest.sh"),
                    str(site_path),
                    "alpha",
                    str(pdf_path),
                    "--source-title",
                    "Restricted Consciousness Fixture",
                    "--restricted-source",
                    "--source-access-reason",
                    "publisher copy is not publicly redistributable",
                    "--operator-responsibility",
                    "operator confirmed local processing rights",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            source_record = sorted((site_path / "spaces" / "alpha" / "sources" / "records").glob("source-*.json"))[0]
            payload = json.loads(source_record.read_text())
            self.assertEqual(payload["access_policy"]["public_download"], False)
            self.assertEqual(payload["access_policy"]["public_source_view"], False)
            source_page = site_path / "spaces" / "alpha" / "site" / "sources" / f"{source_record.stem}.html"
            html = source_page.read_text()
            self.assertIn("Restricted source", html)
            self.assertNotIn("source.md", html)
            self.assertNotIn("original artifact", html)
            self.assertNotIn("/sources/artifacts/", html)

    def test_failed_scouting_invocation_does_not_create_canonical_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            run_command(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "Example Site"], check=True)
            run_command(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "alpha"], check=True)

            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "scout_sources.sh"),
                    str(site_path),
                    "alpha",
                    "question-missing",
                    "--count",
                    "1",
                    "--mock-llm",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            space_root = site_path / "spaces" / "alpha"
            for dirname in ("sources", "claims", "relations", "topics"):
                self.assertEqual(
                    sorted(path for path in (space_root / dirname).rglob("*") if path.is_file()),
                    [],
                    dirname,
                )


if __name__ == "__main__":
    unittest.main()
