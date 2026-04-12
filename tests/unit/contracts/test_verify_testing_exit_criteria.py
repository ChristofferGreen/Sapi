from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import verify_testing_exit_criteria as verifier


class VerifyTestingExitCriteriaTests(unittest.TestCase):
    def test_run_main_writes_success_manifest_when_all_gates_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _write_site_registry(tmp_root)
            out_dir = tmp_root / "verification-manifest"
            evidence_path = tmp_root / "testing_exit_criteria.latest.json"

            run_results = [
                _completed_process(["npm", "run", "test:pr"], returncode=0, stdout="pr ok"),
                _completed_process(["npm", "run", "test:tier4-5"], returncode=0, stdout="tier45 ok"),
                _completed_process(
                    ["pytest", "-q", "tests/integration/failure", "-m", "not live_llm"],
                    returncode=0,
                    stdout="failure suite ok",
                ),
            ]

            with patch(
                "scripts.verify_testing_exit_criteria.subprocess.run",
                side_effect=run_results,
            ):
                with patch(
                    "scripts.verify_testing_exit_criteria._verification_id",
                    return_value="testing-exit-fixed",
                ):
                    exit_code = verifier.run_main(
                        [
                            str(site_path),
                            "--space-name",
                            "alpha",
                            "--out",
                            str(out_dir),
                            "--evidence-path",
                            str(evidence_path),
                        ]
                    )

            self.assertEqual(0, exit_code)
            manifest = json.loads((out_dir / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "success")
            self.assertEqual(manifest["checks"]["pr_required_tiers_green"], True)
            self.assertEqual(manifest["checks"]["determinism_checks_green"], True)
            self.assertEqual(manifest["checks"]["rollback_leakage_regressions_absent"], True)
            self.assertEqual(manifest["checks"]["deferred_build_backlog_clear"], True)

            evidence = json.loads(evidence_path.read_text())
            self.assertEqual(evidence["status"], "success")
            self.assertEqual(evidence["checks"]["deferred_build_backlog_clear"], True)

    def test_run_main_fails_when_deferred_build_backlog_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _write_site_registry(tmp_root)
            space_root = site_path / "spaces" / "alpha"
            _write_run_markdown(space_root=space_root, run_id="run-20260413T101010Z--abcd", build_deferred=True)

            out_dir = tmp_root / "verification-manifest"
            evidence_path = tmp_root / "testing_exit_criteria.latest.json"
            run_results = [
                _completed_process(["npm", "run", "test:pr"], returncode=0, stdout="pr ok"),
                _completed_process(["npm", "run", "test:tier4-5"], returncode=0, stdout="tier45 ok"),
                _completed_process(
                    ["pytest", "-q", "tests/integration/failure", "-m", "not live_llm"],
                    returncode=0,
                    stdout="failure suite ok",
                ),
            ]

            with patch(
                "scripts.verify_testing_exit_criteria.subprocess.run",
                side_effect=run_results,
            ):
                with patch(
                    "scripts.verify_testing_exit_criteria._verification_id",
                    return_value="testing-exit-fixed",
                ):
                    exit_code = verifier.run_main(
                        [
                            str(site_path),
                            "--space-name",
                            "alpha",
                            "--out",
                            str(out_dir),
                            "--evidence-path",
                            str(evidence_path),
                        ]
                    )

            self.assertEqual(1, exit_code)
            manifest = json.loads((out_dir / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["checks"]["deferred_build_backlog_clear"], False)
            self.assertEqual(
                manifest["deferred_build_backlog_run_ids"]["alpha"],
                ["run-20260413T101010Z--abcd"],
            )

    def test_run_main_fails_when_pr_required_tiers_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _write_site_registry(tmp_root)
            out_dir = tmp_root / "verification-manifest"
            evidence_path = tmp_root / "testing_exit_criteria.latest.json"
            run_results = [
                _completed_process(["npm", "run", "test:pr"], returncode=1, stderr="pr failed"),
                _completed_process(["npm", "run", "test:tier4-5"], returncode=0, stdout="tier45 ok"),
                _completed_process(
                    ["pytest", "-q", "tests/integration/failure", "-m", "not live_llm"],
                    returncode=0,
                    stdout="failure suite ok",
                ),
            ]

            with patch(
                "scripts.verify_testing_exit_criteria.subprocess.run",
                side_effect=run_results,
            ):
                with patch(
                    "scripts.verify_testing_exit_criteria._verification_id",
                    return_value="testing-exit-fixed",
                ):
                    exit_code = verifier.run_main(
                        [
                            str(site_path),
                            "--space-name",
                            "alpha",
                            "--out",
                            str(out_dir),
                            "--evidence-path",
                            str(evidence_path),
                        ]
                    )

            self.assertEqual(1, exit_code)
            manifest = json.loads((out_dir / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["checks"]["pr_required_tiers_green"], False)
            self.assertIn("PR-required test tiers must pass", " ".join(manifest["errors"]))


def _write_site_registry(tmp_root: Path) -> Path:
    site_path = tmp_root / "site"
    space_root = site_path / "spaces" / "alpha"
    space_root.mkdir(parents=True, exist_ok=True)
    (site_path / "spaces.toml").write_text(
        (
            "[[spaces]]\n"
            'space_name = "alpha"\n'
            'space_root = "spaces/alpha"\n'
        )
    )
    return site_path


def _write_run_markdown(*, space_root: Path, run_id: str, build_deferred: bool) -> None:
    run_path = space_root / "runs" / run_id / "run.md"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text(
        (
            "---\n"
            f'run_id: {json.dumps(run_id)}\n'
            f"build_deferred: {json.dumps(build_deferred)}\n"
            "---\n"
            "## Summary\n"
            "(none)\n"
        )
    )


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
