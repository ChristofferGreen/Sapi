from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import verify_slice_b as verifier


class VerifySliceBTests(unittest.TestCase):
    def test_run_main_writes_success_manifest_when_all_gates_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = tmp_root / "site"
            site_path.mkdir(parents=True)
            out_dir = tmp_root / "verification-manifest"
            evidence_path = tmp_root / "slice_b_exit_criteria.latest.json"
            run_results = [
                _completed_process(
                    [
                        "pytest",
                        "-q",
                        "tests/integration/build/test_build_determinism.py",
                        "tests/integration/build/test_incremental_vs_full_equivalence.py",
                        "-m",
                        "not live_llm",
                    ],
                    returncode=0,
                    stdout="determinism ok",
                ),
                _completed_process(
                    [
                        "pytest",
                        "-q",
                        "tests/integration/pipelines/test_ingest_pipeline.py",
                        "tests/integration/pipelines/test_query_pipeline_outputs.py",
                        "tests/unit/contracts/test_run_envelope_semantic_flows.py",
                        "tests/golden/test_query_snapshot.py",
                        "tests/golden/test_run_envelope_snapshot.py",
                        "-m",
                        "not live_llm",
                    ],
                    returncode=0,
                    stdout="contracts ok",
                ),
                _completed_process(
                    [
                        "pytest",
                        "-q",
                        "tests/integration/wrappers/test_bootstrap_registry_exception.py",
                        "tests/integration/wrappers/test_wrapper_alias_normalization.py",
                        "tests/integration/wrappers/test_wrapper_alias_conflicts.py",
                        "tests/integration/wrappers/test_regenerate_web_wrapper_contract.py",
                        "tests/integration/wrappers/test_wrapper_runtime_flags.py",
                        "-m",
                        "not live_llm",
                    ],
                    returncode=0,
                    stdout="wrappers ok",
                ),
            ]

            with patch("scripts.verify_slice_b.subprocess.run", side_effect=run_results):
                with patch("scripts.verify_slice_b._verification_id", return_value="slice-b-fixed"):
                    exit_code = verifier.run_main(
                        [
                            str(site_path),
                            "--out",
                            str(out_dir),
                            "--evidence-path",
                            str(evidence_path),
                        ]
                    )

            self.assertEqual(0, exit_code)
            manifest = json.loads((out_dir / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "success")
            self.assertEqual(manifest["checks"]["reliability_determinism_green"], True)
            self.assertEqual(manifest["checks"]["ingest_build_query_contracts_green"], True)
            self.assertEqual(manifest["checks"]["operator_wrapper_usability_green"], True)

            evidence = json.loads(evidence_path.read_text())
            self.assertEqual(evidence["status"], "success")

    def test_run_main_fails_when_wrapper_usability_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = tmp_root / "site"
            site_path.mkdir(parents=True)
            out_dir = tmp_root / "verification-manifest"
            evidence_path = tmp_root / "slice_b_exit_criteria.latest.json"
            run_results = [
                _completed_process(["pytest"], returncode=0, stdout="determinism ok"),
                _completed_process(["pytest"], returncode=0, stdout="contracts ok"),
                _completed_process(["pytest"], returncode=1, stderr="wrappers failed"),
            ]

            with patch("scripts.verify_slice_b.subprocess.run", side_effect=run_results):
                with patch("scripts.verify_slice_b._verification_id", return_value="slice-b-fixed"):
                    exit_code = verifier.run_main(
                        [
                            str(site_path),
                            "--out",
                            str(out_dir),
                            "--evidence-path",
                            str(evidence_path),
                        ]
                    )

            self.assertEqual(1, exit_code)
            manifest = json.loads((out_dir / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["checks"]["operator_wrapper_usability_green"], False)
            self.assertIn("manual workarounds", " ".join(manifest["errors"]))


def _completed_process(
    command: list[str],
    *,
    returncode: int,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


if __name__ == "__main__":
    unittest.main()
