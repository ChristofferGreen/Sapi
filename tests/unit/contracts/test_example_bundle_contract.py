from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_ROOT = REPO_ROOT / "tests" / "example"


class ExampleBundleContractTests(unittest.TestCase):
    def test_example_runner_has_valid_bash_syntax(self) -> None:
        script_path = EXAMPLE_ROOT / "run_example_site.sh"
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_example_runner_uses_repo_root_wrappers_only_for_pipeline_steps(self) -> None:
        script_text = (EXAMPLE_ROOT / "run_example_site.sh").read_text()
        self.assertIn('bash "$REPO_ROOT/create_site.sh"', script_text)
        self.assertIn('bash "$REPO_ROOT/create_space.sh"', script_text)
        self.assertIn('bash "$REPO_ROOT/create_subspaces.sh"', script_text)
        self.assertIn('bash "$REPO_ROOT/ingest.sh"', script_text)
        self.assertIn('bash "$REPO_ROOT/create_comments.sh"', script_text)
        self.assertNotIn("scripts/ingest_source.py", script_text)
        self.assertNotIn("scripts/create_comments.py", script_text)

    def test_example_runner_pins_timeout_and_retry_policy(self) -> None:
        script_text = (EXAMPLE_ROOT / "run_example_site.sh").read_text()
        self.assertIn("STEP_TIMEOUT_SECS=1200", script_text)
        self.assertIn("STEP_MAX_ATTEMPTS=10", script_text)
        self.assertIn("STEP_ATTEMPT=", script_text)
        self.assertIn("timeout_retry=1", script_text)
        self.assertIn("cmd_status -eq 124", script_text)

    def test_example_runner_comment_resume_is_page_scoped(self) -> None:
        script_text = (EXAMPLE_ROOT / "run_example_site.sh").read_text()
        self.assertIn("collect_comment_page_rows()", script_text)
        self.assertIn('--comment-page "$page_ref"', script_text)
        self.assertIn('run_step "comments-${space_slug}-${page_ref_key}"', script_text)
        self.assertNotIn('run_step "comments-${space_slug}"', script_text)

    def test_example_plan_references_real_pdf_assets(self) -> None:
        ingest_rows = _load_tsv(EXAMPLE_ROOT / "ingest_plan.tsv")
        subspace_rows = _load_tsv(EXAMPLE_ROOT / "subspaces.tsv")

        planned_spaces = {row[1] for row in ingest_rows}
        declared_subspaces = {row[2] for row in subspace_rows}
        self.assertEqual(planned_spaces, declared_subspaces)

        self.assertEqual(len(ingest_rows), 25)
        for step_id, _space_slug, rel_pdf_path in ingest_rows:
            self.assertRegex(step_id, r"^\d{3}$")
            pdf_path = EXAMPLE_ROOT / rel_pdf_path
            self.assertTrue(pdf_path.exists(), msg=f"Missing PDF asset: {pdf_path}")


def _load_tsv(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(line.split("\t"))
    return rows
