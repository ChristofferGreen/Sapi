from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    bootstrap_site_and_space,
    latest_run_directory,
    parse_run_frontmatter,
    run_command,
)


class CommentsPipelineIntegrationTests(unittest.TestCase):
    def test_default_targets_parseable_topics_and_writes_one_semantic_artifact_per_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            self._write_topic(space_root, topic_id="topic-alpha", title="Alpha")
            self._write_topic(space_root, topic_id="topic-beta", title="Beta")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "comment_section_pipeline")
            self.assertEqual(frontmatter["target_page_refs"], ["topic:topic-alpha", "topic:topic-beta"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"comment_section_generation": 2},
            )

            semantic_dir = run_dir / "semantic" / "comment_section_generation"
            semantic_artifacts = sorted(semantic_dir.glob("*.json"))
            self.assertEqual([path.name for path in semantic_artifacts], ["topic--topic-alpha.json", "topic--topic-beta.json"])

            for topic_id in ("topic-alpha", "topic-beta"):
                topic_payload = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
                comment_rows = topic_payload["comment_section"]["comments"]
                self.assertEqual(len(comment_rows), 5)

    def test_explicit_source_and_claim_targeting_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            self._write_topic(space_root, topic_id="topic-default", title="Default")
            self._write_source(space_root, source_id="source-alpha")
            self._write_claim(space_root, claim_id="claim-alpha")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--comment-page",
                    "source:source-alpha",
                    "--comment-page",
                    "claim:claim-alpha",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(
                frontmatter["target_page_refs"],
                ["source:source-alpha", "claim:claim-alpha"],
            )
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"comment_section_generation": 2},
            )

            source_payload = json.loads((space_root / "sources" / "records" / "source-alpha.json").read_text())
            claim_payload = json.loads((space_root / "claims" / "claim-alpha.json").read_text())
            topic_payload = json.loads((space_root / "topics" / "topic-default.json").read_text())
            self.assertIn("comment_section", source_payload)
            self.assertIn("comment_section", claim_payload)
            self.assertNotIn("comment_section", topic_payload)

    def test_merge_preserves_existing_comment_uid_and_assigns_only_for_new_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            existing_uid = "comment-existing--abcde12345"
            (space_root / "topics" / f"{topic_id}.json").write_text(
                json.dumps(
                    {
                        "topic_id": topic_id,
                        "title": "Alpha",
                        "comment_section": {
                            "page_ref": f"topic:{topic_id}",
                            "comments": [
                                {
                                    "comment_uid": existing_uid,
                                    "persona_id": "commenter-1",
                                    "body": f"Generated comment 1 for topic:{topic_id} by commenter-1.",
                                    "parent_comment_uid": None,
                                    "comment_no": "pc-001",
                                }
                            ],
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["comments_added"], 4)

            updated_topic = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
            rows = updated_topic["comment_section"]["comments"]
            comment_uids = [row["comment_uid"] for row in rows]
            self.assertIn(existing_uid, comment_uids)
            self.assertEqual(comment_uids.count(existing_uid), 1)
            self.assertEqual(len(rows), 5)

            new_uids = {uid for uid in comment_uids if uid != existing_uid}
            self.assertEqual(len(new_uids), 4)
            for uid in new_uids:
                self.assertTrue(uid.startswith("comment-"))

    def test_web_augmented_mode_writes_canonical_snapshot_path_and_schema_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            self._write_topic(space_root, topic_id="topic-alpha", title="Alpha")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "create_comments.py"),
                    "alpha",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--count",
                    "5",
                    "--comment-evidence-mode",
                    "web-augmented",
                    "--comment-seed",
                    "seed-123",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            snapshot_path = (
                space_root
                / "raw"
                / "snapshots"
                / "comment_sections"
                / "comment-section-seed-123.json"
            )
            self.assertTrue(snapshot_path.is_file())
            snapshot_payload = json.loads(snapshot_path.read_text())
            self.assertEqual(snapshot_payload["schema_version"], "comment_section_evidence_snapshot_v1")

            run_dir = latest_run_directory(space_root)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["evidence_mode"], "web-augmented")
            self.assertEqual(frontmatter["evidence_snapshot_path"], str(snapshot_path.resolve()))

    def _write_topic(self, space_root: Path, *, topic_id: str, title: str) -> None:
        (space_root / "topics" / f"{topic_id}.json").write_text(
            json.dumps(
                {
                    "topic_id": topic_id,
                    "title": title,
                    "sections": [],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    def _write_source(self, space_root: Path, *, source_id: str) -> None:
        (space_root / "sources" / "records" / f"{source_id}.json").write_text(
            json.dumps(
                {
                    "source_id": source_id,
                    "title": "Source fixture",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    def _write_claim(self, space_root: Path, *, claim_id: str) -> None:
        (space_root / "claims" / f"{claim_id}.json").write_text(
            json.dumps(
                {
                    "claim_id": claim_id,
                    "text": "Claim fixture",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )


if __name__ == "__main__":
    unittest.main()
