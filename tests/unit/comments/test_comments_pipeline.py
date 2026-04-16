from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.comments.comments_pipeline import collect_comment_targets


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


class CommentPipelineUnitTests(unittest.TestCase):
    def test_default_target_collection_includes_topics_and_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp)
            _write_json(
                space_root / "topics" / "topic-b.json",
                {"topic_id": "topic-b", "title": "Topic B"},
            )
            _write_json(
                space_root / "topics" / "topic-a.json",
                {"topic_id": "topic-a", "title": "Topic A"},
            )
            _write_json(
                space_root / "sources" / "records" / "source-z.json",
                {"source_id": "source-z", "title": "Source Z"},
            )
            _write_json(
                space_root / "sources" / "records" / "source-y.json",
                {"source_id": "source-y", "title": "Source Y"},
            )

            targets = collect_comment_targets(space_root=space_root, explicit_page_refs=[])
            self.assertEqual(
                [target.page_ref for target in targets],
                ["source:source-y", "source:source-z", "topic:topic-a", "topic:topic-b"],
            )

    def test_default_target_collection_requires_parseable_topic_or_source_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp)
            with self.assertRaisesRegex(
                ValueError,
                "No eligible parseable topic/source pages found",
            ):
                collect_comment_targets(space_root=space_root, explicit_page_refs=[])

    def test_explicit_target_collection_still_resolves_single_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp)
            _write_json(
                space_root / "sources" / "records" / "source-a.json",
                {"source_id": "source-a", "title": "Source A"},
            )
            targets = collect_comment_targets(
                space_root=space_root,
                explicit_page_refs=["source:source-a"],
            )
            self.assertEqual(len(targets), 1)
            self.assertEqual(targets[0].page_ref, "source:source-a")
            self.assertEqual(targets[0].page_type, "source")


if __name__ == "__main__":
    unittest.main()
