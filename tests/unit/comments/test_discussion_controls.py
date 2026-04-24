from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.comments.controls import (
    load_site_discussion_controls,
    resolve_page_discussion_controls,
)


class DiscussionControlsUnitTests(unittest.TestCase):
    def test_site_controls_loader_reads_only_canonical_schema_and_keys(self) -> None:
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
                            "max_turns": 7,
                            "unknown_key": "ignored",
                        },
                        "pages": {
                            "topic:topic-a": {
                                "enabled": False,
                                "roster": ["alice", "bob", ""],
                                "persona_discussion_max_depth": 3,
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
                {"enabled": True, "max_turns": 7},
            )
            self.assertEqual(
                loaded.pages["topic:topic-a"],
                {"enabled": False, "roster": ["alice", "bob"]},
            )

    def test_site_controls_loader_falls_back_to_empty_for_missing_or_noncanonical_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp)
            self.assertEqual(load_site_discussion_controls(site_path=site_path).defaults, {})
            self.assertEqual(load_site_discussion_controls(site_path=site_path).pages, {})

            controls_path = site_path / "config" / "discussion_controls.json"
            controls_path.parent.mkdir(parents=True, exist_ok=True)
            controls_path.write_text(
                json.dumps(
                    {
                        "schema_version": "persona_discussion_controls_v1",
                        "defaults": {"enabled": True},
                        "pages": {},
                    }
                )
            )
            loaded = load_site_discussion_controls(site_path=site_path)
            self.assertEqual(loaded.defaults, {})
            self.assertEqual(loaded.pages, {})

    def test_canonical_page_metadata_resolves_when_frontmatter_is_absent(self) -> None:
        resolution = resolve_page_discussion_controls(
            site_controls=load_site_discussion_controls(site_path=Path("/tmp/does-not-exist")),
            page_ref="topic:topic-a",
            page_payload={
                "topic_id": "topic-a",
                "discussion_controls": {"enabled": True, "max_depth": 4},
            },
        )
        self.assertEqual(resolution.effective_controls["enabled"], True)
        self.assertEqual(resolution.effective_controls["max_depth"], 4)
        self.assertEqual(resolution.canonical_page_controls, {"enabled": True, "max_depth": 4})

    def test_frontmatter_discussion_controls_fail_fast_even_when_canonical_metadata_exists(self) -> None:
        with self.assertRaises(ValueError):
            resolve_page_discussion_controls(
                site_controls=load_site_discussion_controls(site_path=Path("/tmp/does-not-exist")),
                page_ref="topic:topic-a",
                page_payload={
                    "topic_id": "topic-a",
                    "discussion_controls": {"enabled": True, "max_depth": 4},
                    "frontmatter": {
                        "persona_discussion_enabled": False,
                        "persona_discussion_max_depth": 1,
                    },
                },
            )

    def test_frontmatter_discussion_controls_fail_fast_when_canonical_metadata_is_missing(self) -> None:
        with self.assertRaises(ValueError):
            resolve_page_discussion_controls(
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


if __name__ == "__main__":
    unittest.main()
