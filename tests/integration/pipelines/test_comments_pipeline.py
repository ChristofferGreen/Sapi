from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.profiles.persona_catalog import load_seeded_persona_catalog
from tests.conftest import (
    REPO_ROOT,
    assert_no_run_containers,
    bootstrap_site_and_space,
    latest_run_directory,
    parse_run_frontmatter,
    run_command,
)


class CommentsPipelineIntegrationTests(unittest.TestCase):
    _VALID_CLAIM_ID = "claim-evidence-point--abcdefabcdef"
    _VALID_SOURCE_ID = "source-primary-study--1234abcd5678"

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
            self.assertEqual(frontmatter["semantic_flows"], ["comment_section_generation"])
            self.assertEqual(frontmatter["requested_count"], 5)
            self.assertEqual(frontmatter["target_page_refs"], ["topic:topic-alpha", "topic:topic-beta"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"comment_section_generation": 2},
            )
            self.assertEqual(frontmatter["generation_isolation"]["schema_version"], "comment_section_generation_context_v1")
            self.assertEqual(frontmatter["generation_isolation"]["total_leak_count"], 0)
            self.assertEqual(frontmatter["adjudication"]["rubric_id"], "comment_section_adjudication_v1")
            self.assertIn("checks", frontmatter["adjudication"])
            self.assertIn("failures", frontmatter["adjudication"])

            semantic_dir = run_dir / "semantic" / "comment_section_generation"
            semantic_artifacts = sorted(semantic_dir.glob("*.json"))
            self.assertEqual([path.name for path in semantic_artifacts], ["topic--topic-alpha.json", "topic--topic-beta.json"])
            semantic_payloads = {path.stem: json.loads(path.read_text()) for path in semantic_artifacts}
            self.assertEqual(semantic_payloads["topic--topic-alpha"]["page_ref"], "topic:topic-alpha")
            self.assertEqual(semantic_payloads["topic--topic-beta"]["page_ref"], "topic:topic-beta")
            self.assertEqual(semantic_payloads["topic--topic-alpha"]["requested_count"], 5)
            self.assertEqual(semantic_payloads["topic--topic-beta"]["requested_count"], 5)

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

    def test_count_bounds_fail_fast_outside_allowed_range(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            self._write_topic(space_root, topic_id="topic-alpha", title="Alpha")

            for invalid_count in (4, 51):
                with self.subTest(invalid_count=invalid_count):
                    result = run_command(
                        [
                            "python3",
                            str(REPO_ROOT / "scripts" / "create_comments.py"),
                            "alpha",
                            "--registry-path",
                            str(site_path / "spaces.toml"),
                            "--count",
                            str(invalid_count),
                            "--mock-llm",
                        ]
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("--count must be in [5, 50]", result.stderr)
                    assert_no_run_containers(space_root)

    def test_merge_preserves_existing_comment_uid_and_assigns_only_for_new_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            existing_uid = "comment-existing--abcde12345"
            persona_id = _seeded_persona_ids(count=1)[0]
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
                                    "persona_id": persona_id,
                                    "body": f"Generated comment 1 by {persona_id}.",
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

    def test_moderator_outcomes_social_vote_and_permalink_keys_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            self._write_topic(space_root, topic_id=topic_id, title="Alpha")

            command = [
                "python3",
                str(REPO_ROOT / "scripts" / "create_comments.py"),
                "alpha",
                "--registry-path",
                str(site_path / "spaces.toml"),
                "--count",
                "5",
                "--mock-llm",
            ]
            first = run_command(command)
            self.assertEqual(first.returncode, 0, msg=first.stderr)

            first_topic_payload = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
            first_comment_section = first_topic_payload["comment_section"]
            self.assertIn("moderator_outcomes", first_comment_section)
            moderator_outcomes = first_comment_section["moderator_outcomes"]
            self.assertTrue(moderator_outcomes["moderator_check"].startswith("- Moderator Check:"))
            self.assertIn("claim_citation", moderator_outcomes["guardrail_checks"])
            self.assertIn("anti_repetition", moderator_outcomes["guardrail_checks"])
            self.assertIn("strongest_opposing_point_ack", moderator_outcomes["guardrail_checks"])
            self.assertIn("Consensus", moderator_outcomes["outcome_sections"])
            self.assertIn("Open Disagreements", moderator_outcomes["outcome_sections"])
            self.assertIn("Missing Evidence Priorities", moderator_outcomes["outcome_sections"])

            first_rows = first_comment_section["comments"]
            first_vote_map: dict[str, dict[str, int]] = {}
            for row in first_rows:
                comment_uid = row["comment_uid"]
                self.assertEqual(row["permalink"], f"#{comment_uid}")
                self.assertEqual(row["thread_state_key"], comment_uid)
                self.assertEqual(row["thread_expansion_key"], comment_uid)
                social_vote = row["social_vote"]
                self.assertIsInstance(social_vote["upvotes"], int)
                self.assertIsInstance(social_vote["downvotes"], int)
                self.assertIsInstance(social_vote["score"], int)
                first_vote_map[comment_uid] = dict(social_vote)

            second = run_command(command)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            second_topic_payload = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
            second_rows = second_topic_payload["comment_section"]["comments"]
            second_vote_map = {row["comment_uid"]: row["social_vote"] for row in second_rows}
            self.assertEqual(first_vote_map, second_vote_map)

            build_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(build_result.returncode, 0, msg=build_result.stderr)

            topic_html = (space_root / "site" / "topics" / f"{topic_id}.html").read_text()
            sample_uid = second_rows[0]["comment_uid"]
            sample_persona_id = second_rows[0]["persona_id"]
            sample_vote = second_rows[0]["social_vote"]
            self.assertIn("Comment Thread", topic_html)
            self.assertIn("Moderator Check", topic_html)
            self.assertIn("Open Disagreements", topic_html)
            self.assertIn("Missing Evidence Priorities", topic_html)
            self.assertIn(f"id=\"{sample_uid}\"", topic_html)
            self.assertIn(f"href=\"#{sample_uid}\"", topic_html)
            self.assertIn(f"data-thread-state-key=\"{sample_uid}\"", topic_html)
            self.assertIn(f"data-thread-expansion-key=\"{sample_uid}\"", topic_html)
            self.assertIn(f"data-upvotes=\"{sample_vote['upvotes']}\"", topic_html)
            self.assertIn(f"data-downvotes=\"{sample_vote['downvotes']}\"", topic_html)
            self.assertIn(f"data-score=\"{sample_vote['score']}\"", topic_html)
            self.assertIn(
                f"src=\"/spaces/alpha/site/assets/persona_avatars/{sample_persona_id}.jpg\"",
                topic_html,
            )
            avatar_asset = (
                space_root / "site" / "assets" / "persona_avatars" / f"{sample_persona_id}.jpg"
            )
            self.assertTrue(avatar_asset.is_file())

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

    def test_comment_quality_manifest_writes_to_canonical_path_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            self._write_topic(space_root, topic_id="topic-alpha", title="Alpha")

            def _run_comments_and_load_manifest() -> dict[str, object]:
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

                quality_manifests = sorted(
                    (space_root / "outputs" / "comment_quality").glob("CQ-*/manifest.json")
                )
                self.assertEqual(len(quality_manifests), 1)
                manifest_path = quality_manifests[0]
                manifest_payload = json.loads(manifest_path.read_text())
                self.assertEqual(
                    manifest_path,
                    space_root
                    / "outputs"
                    / "comment_quality"
                    / manifest_payload["evaluation_id"]
                    / "manifest.json",
                )
                self.assertEqual(
                    manifest_payload["schema_version"],
                    "comment_section_quality_eval_manifest_v1",
                )
                self.assertRegex(manifest_payload["evaluation_id"], r"^CQ-[0-9a-f]{12}$")
                self.assertIn("pass", manifest_payload)
                self.assertIn("fail_reasons", manifest_payload)
                return manifest_payload

            first_manifest = _run_comments_and_load_manifest()
            second_manifest = _run_comments_and_load_manifest()
            self.assertEqual(first_manifest["evaluation_id"], second_manifest["evaluation_id"])
            self.assertEqual(first_manifest["pass"], second_manifest["pass"])
            self.assertEqual(first_manifest["fail_reasons"], second_manifest["fail_reasons"])

    def test_turn_marker_normalization_supports_canonical_and_legacy_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            (space_root / "topics" / f"{topic_id}.json").write_text(
                json.dumps(
                    {
                        "topic_id": topic_id,
                        "title": "Alpha",
                        "comment_section": {
                            "page_ref": f"topic:{topic_id}",
                            "comments": [
                                {
                                    "comment_uid": "comment-canonical--abcde12345",
                                    "persona_id": "commenter-1",
                                    "body": (
                                        '<<turn:{"position":"support","claim_ids":["'
                                        + self._VALID_CLAIM_ID
                                        + '"],"evidence_refs":["claim:'
                                        + self._VALID_CLAIM_ID
                                        + '"],"confidence":0.88}>>'
                                        "Canonical marker body."
                                    ),
                                    "comment_no": "pc-001",
                                },
                                {
                                    "comment_uid": "comment-legacy--abcde67890",
                                    "persona_id": "commenter-2",
                                    "body": (
                                        "<!-- turn:{"
                                        '"position":"challenge","claim_ids":["'
                                        + self._VALID_CLAIM_ID
                                        + '"],"evidence_refs":["source:'
                                        + self._VALID_SOURCE_ID
                                        + '"],"confidence":0.45} -->'
                                        "Legacy marker body."
                                    ),
                                    "comment_no": "pc-002",
                                },
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

            topic_payload = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
            rows = {
                row["comment_uid"]: row
                for row in topic_payload["comment_section"]["comments"]
            }
            canonical_row = rows["comment-canonical--abcde12345"]
            legacy_row = rows["comment-legacy--abcde67890"]
            self.assertEqual(canonical_row["body"], "Canonical marker body.")
            self.assertEqual(canonical_row["turn"]["position"], "support")
            self.assertEqual(legacy_row["body"], "Legacy marker body.")
            self.assertEqual(legacy_row["turn"]["position"], "challenge")

    def test_argumentative_turn_validation_rejects_invalid_turn_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            (space_root / "topics" / f"{topic_id}.json").write_text(
                json.dumps(
                    {
                        "topic_id": topic_id,
                        "title": "Alpha",
                        "comment_section": {
                            "page_ref": f"topic:{topic_id}",
                            "comments": [
                                {
                                    "comment_uid": "comment-invalid-turn--abcde12345",
                                    "persona_id": "commenter-1",
                                    "body": (
                                        '<<turn:{"position":"support","claim_ids":["'
                                        + self._VALID_CLAIM_ID
                                        + '"],"confidence":0.6}>>'
                                        "Missing evidence refs."
                                    ),
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("evidence_refs", result.stderr)
            assert_no_run_containers(space_root)

    def test_social_comment_without_turn_marker_rejects_unclassified_factual_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            (space_root / "topics" / f"{topic_id}.json").write_text(
                json.dumps(
                    {
                        "topic_id": topic_id,
                        "title": "Alpha",
                        "comment_section": {
                            "page_ref": f"topic:{topic_id}",
                            "comments": [
                                {
                                    "comment_uid": "comment-unclassified--abcde12345",
                                    "persona_id": "commenter-1",
                                    "body": (
                                        "No marker, but this references factual id "
                                        + self._VALID_CLAIM_ID
                                        + "."
                                    ),
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("factual claim references", result.stderr)
            assert_no_run_containers(space_root)

    def test_rebuttal_steelman_and_claim_badges_are_normalized_in_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            rebuttal_ack = "You are right that early samples were noisy."
            existing_uid = "comment-rebuttal--abcde12345"
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
                                    "body": (
                                        '<<turn:{"position":"rebuttal","claim_ids":["'
                                        + self._VALID_CLAIM_ID
                                        + '"],"evidence_refs":["claim:'
                                        + self._VALID_CLAIM_ID
                                        + '"],"confidence":0.78,"strongest_opposing_point_ack":"'
                                        + rebuttal_ack
                                        + '"}>>'
                                        + rebuttal_ack
                                        + " I still disagree because later quarters show the same trend."
                                    ),
                                    "claim_badges": [
                                        {"claim_id": self._VALID_CLAIM_ID, "status": "verified", "confidence": 0.91},
                                        {"claim_id": self._VALID_CLAIM_ID, "status": "pending-review"},
                                    ],
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

            topic_payload = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
            rows = {
                row["comment_uid"]: row
                for row in topic_payload["comment_section"]["comments"]
            }
            rebuttal_row = rows[existing_uid]
            self.assertEqual(rebuttal_row["turn"]["position"], "rebuttal")
            self.assertEqual(rebuttal_row["turn"]["strongest_opposing_point_ack"], rebuttal_ack)
            self.assertEqual(
                rebuttal_row["claim_badges"],
                [
                    {"claim_id": self._VALID_CLAIM_ID, "status": "verified", "confidence": 0.91},
                    {"claim_id": self._VALID_CLAIM_ID, "status": "unverified"},
                ],
            )

    def test_rebuttal_without_steelman_ack_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            (space_root / "topics" / f"{topic_id}.json").write_text(
                json.dumps(
                    {
                        "topic_id": topic_id,
                        "title": "Alpha",
                        "comment_section": {
                            "page_ref": f"topic:{topic_id}",
                            "comments": [
                                {
                                    "comment_uid": "comment-missing-steelman--abcde12345",
                                    "persona_id": "commenter-1",
                                    "body": (
                                        '<<turn:{"position":"rebuttal","claim_ids":["'
                                        + self._VALID_CLAIM_ID
                                        + '"],"evidence_refs":["claim:'
                                        + self._VALID_CLAIM_ID
                                        + '"],"confidence":0.78}>>'
                                        "I disagree with the conclusion."
                                    ),
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
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("strongest_opposing_point_ack", result.stderr)
            assert_no_run_containers(space_root)

    def test_legacy_frontmatter_controls_are_written_to_canonical_page_json_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            topic_id = "topic-alpha"
            frontmatter_controls = {
                "persona_discussion_enabled": False,
                "persona_discussion_roster": ["alice", "bob"],
                "persona_discussion_max_turns": 4,
            }
            (space_root / "topics" / f"{topic_id}.json").write_text(
                json.dumps(
                    {
                        "topic_id": topic_id,
                        "title": "Alpha",
                        "frontmatter": frontmatter_controls,
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

            topic_payload = json.loads((space_root / "topics" / f"{topic_id}.json").read_text())
            self.assertEqual(
                topic_payload["discussion_controls"],
                {"enabled": False, "roster": ["alice", "bob"], "max_turns": 4},
            )
            self.assertEqual(topic_payload["frontmatter"], frontmatter_controls)
            self.assertNotIn("persona_discussion_enabled", topic_payload)

    def _write_topic(self, space_root: Path, *, topic_id: str, title: str) -> None:
        (space_root / "topics" / f"{topic_id}.json").write_text(
            json.dumps(
                {
                    "topic_id": topic_id,
                    "title": title,
                    "sections": [],
                    "source_ids": [],
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


def _seeded_persona_ids(*, count: int) -> list[str]:
    rows = load_seeded_persona_catalog(repo_root=REPO_ROOT, require_image_files=False)
    return [str(row["persona_id"]) for row in rows[:count]]
