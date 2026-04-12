from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from sapi.build.topic_lifecycle import resolve_topic_lifecycle


REPO_ROOT = Path(__file__).resolve().parents[3]


class TopicLifecycleContractTests(unittest.TestCase):
    def test_resolve_topic_lifecycle_applies_automatic_transitions(self) -> None:
        draft_resolution = resolve_topic_lifecycle(
            topic={"lifecycle_state": "draft"},
            topic_id="topic-auto-stable--aaaaaaaaaaaa",
        )
        self.assertEqual(draft_resolution.declared_state, "draft")
        self.assertEqual(draft_resolution.effective_state, "stable")
        self.assertEqual(draft_resolution.auto_transition, "draft_to_stable")

        stable_resolution = resolve_topic_lifecycle(
            topic={"lifecycle_state": "stable", "major_conflict": True},
            topic_id="topic-auto-draft--bbbbbbbbbbbb",
        )
        self.assertEqual(stable_resolution.declared_state, "stable")
        self.assertEqual(stable_resolution.effective_state, "draft")
        self.assertEqual(stable_resolution.auto_transition, "stable_to_draft")

        final_resolution = resolve_topic_lifecycle(
            topic={
                "lifecycle_state": "final",
                "major_conflict": True,
                "structural_churn": True,
            },
            topic_id="topic-final--cccccccccccc",
        )
        self.assertEqual(final_resolution.declared_state, "final")
        self.assertEqual(final_resolution.effective_state, "final")
        self.assertIsNone(final_resolution.auto_transition)

    def test_build_site_blocks_final_disputed_contradiction_without_auto_demoting_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            topic_id = "topic-final-contradiction--aaaaaaaaaaaa"
            self._write_topic(
                space_root=space_root,
                topic_id=topic_id,
                lifecycle_state="final",
                final_disputed_contradiction=True,
            )

            build_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertNotEqual(build_result.returncode, 0)
            self.assertIn("final_disputed_contradiction", build_result.stderr)
            self.assertIn("Build blocked by publication-gating lint errors", build_result.stderr)

            topic_payload = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
            self.assertEqual(topic_payload["lifecycle_state"], "final")

            manifest = json.loads((site_path / "outputs" / "build_site" / "manifest.json").read_text())
            self.assertEqual(manifest["lint"]["error_count"], 1)
            issue = manifest["lint"]["issues"][0]
            self.assertEqual(issue["check_id"], "final_disputed_contradiction")
            self.assertEqual(issue["severity"], "error")

    def test_set_topic_lifecycle_supports_manual_remediation_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            topic_id = "topic-manual-remediation--aaaaaaaaaaaa"
            topic_path = self._write_topic(
                space_root=space_root,
                topic_id=topic_id,
                lifecycle_state="final",
                final_disputed_contradiction=True,
            )

            demote_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "set_topic_lifecycle.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--topic-id",
                    topic_id,
                    "--state",
                    "stable",
                    "--actor",
                    "moderator_a",
                    "--reason",
                    "manual remediation for contradiction",
                ]
            )
            self.assertEqual(demote_result.returncode, 0, msg=demote_result.stderr)

            topic_payload = json.loads(topic_path.read_text())
            self.assertEqual(topic_payload["lifecycle_state"], "stable")
            self.assertEqual(len(topic_payload["lifecycle_audit"]), 1)
            first_audit = topic_payload["lifecycle_audit"][0]
            self.assertEqual(first_audit["from_state"], "final")
            self.assertEqual(first_audit["to_state"], "stable")
            self.assertEqual(first_audit["actor"], "moderator_a")
            self.assertEqual(first_audit["reason"], "manual remediation for contradiction")

            build_after_remediation = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(build_after_remediation.returncode, 0, msg=build_after_remediation.stderr)

            promote_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "set_topic_lifecycle.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--topic-id",
                    topic_id,
                    "--state",
                    "final",
                    "--actor",
                    "moderator_b",
                ]
            )
            self.assertEqual(promote_result.returncode, 0, msg=promote_result.stderr)

            topic_payload = json.loads(topic_path.read_text())
            self.assertEqual(topic_payload["lifecycle_state"], "final")
            self.assertEqual(topic_payload["finalized_by"], "moderator_b")
            self.assertRegex(topic_payload["finalized_at"], r"^\d{4}-\d{2}-\d{2}T")
            self.assertEqual(len(topic_payload["lifecycle_audit"]), 2)
            second_audit = topic_payload["lifecycle_audit"][1]
            self.assertEqual(second_audit["from_state"], "stable")
            self.assertEqual(second_audit["to_state"], "final")
            self.assertEqual(second_audit["actor"], "moderator_b")

            invalid_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "set_topic_lifecycle.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--topic-id",
                    topic_id,
                    "--state",
                    "draft",
                ]
            )
            self.assertNotEqual(invalid_result.returncode, 0)
            self.assertIn("final -> draft", invalid_result.stderr)

    def _bootstrap_site_space(self, tmp_root: Path, space_name: str) -> tuple[Path, Path]:
        site_path = tmp_root / "site-a"
        self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "Lifecycle Site"], check=True)
        self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
        return site_path, site_path / "spaces" / space_name

    def _write_topic(
        self,
        *,
        space_root: Path,
        topic_id: str,
        lifecycle_state: str,
        final_disputed_contradiction: bool,
    ) -> Path:
        payload = {
            "topic_id": topic_id,
            "title": "Lifecycle Topic",
            "structure_type": "wiki",
            "sections": [{"heading": "Summary", "body": "Body"}],
            "claim_ids": [],
            "source_ids": [],
            "lifecycle_state": lifecycle_state,
            "final_disputed_contradiction": final_disputed_contradiction,
        }
        path = space_root / "topics" / f"{topic_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return path

    def _run(self, cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise AssertionError(
                f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        return result


if __name__ == "__main__":
    unittest.main()
