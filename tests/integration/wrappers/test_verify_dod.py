from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class VerifyDodIntegrationTests(unittest.TestCase):
    def test_verify_dod_executes_wrapper_sweep_and_writes_success_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = tmp_root / "dod-site"
            source_path = tmp_root / "dod-source.txt"
            source_path.write_text("dod verification source fixture without publication date\n")

            output_dir = tmp_root / "dod-verification-output"
            evidence_path = tmp_root / "dod_verification.latest.json"
            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "verify_dod.py"),
                    str(site_path),
                    "alpha",
                    str(source_path),
                    "What changed in this source?",
                    "--mock-llm",
                    "--out",
                    str(output_dir),
                    "--evidence-path",
                    str(evidence_path),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("verification complete", result.stdout)

            manifest_path = output_dir / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["status"], "success")

            executed_steps = [step["name"] for step in manifest["steps"]]
            self.assertEqual(
                executed_steps,
                [
                    "create_site",
                    "create_space",
                    "ingest",
                    "query",
                    "create_comments",
                    "generate_profiles",
                    "regenerate_web",
                    "validate",
                    "evaluate_source",
                ],
            )

            checks = manifest["checks"]
            self.assertTrue(checks["dod_13_1_wrappers_execute_successfully"]["passed"])
            self.assertTrue(checks["dod_13_2_validate_workflow_lint_gate"]["passed"])
            self.assertTrue(checks["dod_13_3_evaluate_source_artifact_pack"]["passed"])
            self.assertTrue(checks["dod_13_4_ingest_artifacts_and_links"]["passed"])
            self.assertTrue(checks["dod_13_10_no_deferred_build_backlog"]["passed"])

            self.assertTrue(evidence_path.is_file())
            evidence = json.loads(evidence_path.read_text())
            self.assertEqual(evidence["status"], "success")
            self.assertTrue(evidence["checks"]["dod_13_1_wrappers_execute_successfully"])


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    unittest.main()
