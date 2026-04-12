from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.comments.controls import (
    apply_canonical_page_discussion_controls,
    load_site_discussion_controls,
    resolve_page_discussion_controls,
)


class DiscussionControlsUnitTests(unittest.TestCase):
    def test_site_controls_loader_reads_canonical_schema_and_normalizes_alias_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp)
            controls_path = site_path / "config" / "discussion_controls.json"
            controls_path.parent.mkdir(parents=True, exist_ok=True)
            controls_path.write_text(
                json.dumps(
                    {
                        "schema_version": "comment_section_discussion_controls_v1",
                        "defaults": {
                            "enabled": True,
                            "persona_discussion_max_turns": 7,
                            "persona_discussion_reply_chance": 0.45,
                            "unknown_key": "ignored",
                        },
                        "pages": {
                            "topic:topic-a": {
                                "persona_discussion_enabled": False,
                                "persona_discussion_roster": ["alice", "bob", ""],
                            }
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            loaded = load_site_discussion_controls(site_path=site_path)
            self.assertEqual(
                loaded.defaults,
                {"enabled": True, "max_turns": 7, "reply_chance": 0.45},
            )
            self.assertEqual(
                loaded.pages["topic:topic-a"],
                {"enabled": False, "roster": ["alice", "bob"]},
            )

    def test_site_controls_loader_falls_back_to_empty_for_missing_or_schema_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp)
            self.assertEqual(load_site_discussion_controls(site_path=site_path).defaults, {})
            self.assertEqual(load_site_discussion_controls(site_path=site_path).pages, {})

            controls_path = site_path / "config" / "discussion_controls.json"
            controls_path.parent.mkdir(parents=True, exist_ok=True)
            controls_path.write_text(
                json.dumps(
                    {
                        "schema_version": "unexpected_schema_v9",
                        "defaults": {"enabled": True},
                        "pages": {},
                    }
                )
            )
            loaded = load_site_discussion_controls(site_path=site_path)
            self.assertEqual(loaded.defaults, {})
            self.assertEqual(loaded.pages, {})

    def test_canonical_page_metadata_overrides_legacy_frontmatter_when_both_present(self) -> None:
        resolution = resolve_page_discussion_controls(
            site_controls=load_site_discussion_controls(site_path=Path("/tmp/does-not-exist")),
            page_ref="topic:topic-a",
            page_payload={
                "topic_id": "topic-a",
                "discussion_controls": {"enabled": True, "max_depth": 4},
                "frontmatter": {"persona_discussion_enabled": False, "persona_discussion_max_depth": 1},
            },
        )
        self.assertEqual(resolution.effective_controls["enabled"], True)
        self.assertEqual(resolution.effective_controls["max_depth"], 4)
        self.assertEqual(resolution.canonical_page_controls, {"enabled": True, "max_depth": 4})
        self.assertIsNone(resolution.canonical_page_controls_to_write)

    def test_legacy_frontmatter_controls_can_be_written_to_canonical_page_metadata(self) -> None:
        resolution = resolve_page_discussion_controls(
            site_controls=load_site_discussion_controls(site_path=Path("/tmp/does-not-exist")),
            page_ref="topic:topic-a",
            page_payload={
                "topic_id": "topic-a",
                "frontmatter": {
                    "persona_discussion_enabled": False,
                    "persona_discussion_roster": ["alice", "bob"],
                },
            },
        )
        self.assertEqual(
            resolution.canonical_page_controls_to_write,
            {"enabled": False, "roster": ["alice", "bob"]},
        )
        updated = apply_canonical_page_discussion_controls(
            page_payload={
                "topic_id": "topic-a",
                "frontmatter": {
                    "persona_discussion_enabled": False,
                    "persona_discussion_roster": ["alice", "bob"],
                },
            },
            canonical_page_controls=resolution.canonical_page_controls_to_write or {},
        )
        self.assertEqual(updated["discussion_controls"], {"enabled": False, "roster": ["alice", "bob"]})
        self.assertEqual(
            updated["frontmatter"],
            {
                "persona_discussion_enabled": False,
                "persona_discussion_roster": ["alice", "bob"],
            },
        )


if __name__ == "__main__":
    unittest.main()
