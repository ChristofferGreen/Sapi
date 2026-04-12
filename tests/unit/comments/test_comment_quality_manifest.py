from __future__ import annotations

from datetime import UTC, datetime
import unittest
from pathlib import Path

from sapi.comments.quality import (
    QUALITY_DIMENSIONS,
    build_comment_quality_manifest,
    load_comment_quality_benchmark,
)
from tests.conftest import REPO_ROOT


class CommentQualityManifestUnitTests(unittest.TestCase):
    def test_benchmark_artifact_loads_with_expected_contract_defaults(self) -> None:
        benchmark = load_comment_quality_benchmark(repo_root=REPO_ROOT)
        self.assertEqual(benchmark.schema_version, "comment_section_quality_benchmark_v1")
        self.assertEqual(benchmark.benchmark_id, "comment-quality-v1")
        self.assertEqual(benchmark.dimensions, QUALITY_DIMENSIONS)
        self.assertEqual(benchmark.overall_min, 0.62)
        self.assertEqual(benchmark.dimension_mins["argument_quality"], 0.55)
        self.assertEqual(
            benchmark.benchmark_path,
            REPO_ROOT / "sapi" / "benchmarks" / "comment_quality_benchmark_v1.json",
        )

    def test_manifest_path_uses_canonical_outputs_comment_quality_location(self) -> None:
        space_root = Path("/tmp/space-for-comment-quality")
        manifest_path, manifest = build_comment_quality_manifest(
            repo_root=REPO_ROOT,
            space_root=space_root,
            comments_by_page={
                "topic:topic-alpha": [
                    {
                        "comment_uid": "comment-alpha--abcdef123456",
                        "persona_id": "persona-alpha",
                        "body": "This is a thoughtful response with enough words to satisfy relevance scoring.",
                    }
                ]
            },
            snapshot_path=space_root / "raw" / "snapshots" / "comment_sections" / "comment-section-seed.json",
            as_of=datetime(2026, 4, 13, 9, 0, 0, tzinfo=UTC),
        )
        self.assertTrue(str(manifest_path).startswith(str(space_root / "outputs" / "comment_quality" / "CQ-")))
        self.assertEqual(manifest_path.name, "manifest.json")
        self.assertEqual(manifest["schema_version"], "comment_section_quality_eval_manifest_v1")
        self.assertEqual(
            manifest["snapshot_path"],
            "raw/snapshots/comment_sections/comment-section-seed.json",
        )
        self.assertTrue(manifest["pass"])
        self.assertEqual(manifest["fail_reasons"], [])

    def test_threshold_decision_and_fail_reasons_are_deterministic(self) -> None:
        space_root = Path("/tmp/space-for-comment-quality")
        comments_by_page = {
            "topic:topic-alpha": [
                {"comment_uid": "comment-low-1", "body": "ok"},
                {"comment_uid": "comment-low-2", "body": "ok"},
            ]
        }

        first_path, first_manifest = build_comment_quality_manifest(
            repo_root=REPO_ROOT,
            space_root=space_root,
            comments_by_page=comments_by_page,
            snapshot_path=None,
            as_of=datetime(2026, 4, 13, 9, 30, 0, tzinfo=UTC),
        )
        second_path, second_manifest = build_comment_quality_manifest(
            repo_root=REPO_ROOT,
            space_root=space_root,
            comments_by_page=comments_by_page,
            snapshot_path=None,
            as_of=datetime(2026, 4, 13, 10, 30, 0, tzinfo=UTC),
        )

        self.assertEqual(first_manifest["evaluation_id"], second_manifest["evaluation_id"])
        self.assertEqual(first_path, second_path)
        self.assertFalse(first_manifest["pass"])
        self.assertEqual(
            first_manifest["fail_reasons"],
            [
                "overall_below_min:0.3500<0.6200",
                "persona_consistency_below_min:0.0000<0.5000",
                "novelty_below_min:0.2500<0.5000",
                "relevance_below_min:0.5000<0.5500",
                "human_likeness_below_min:0.4000<0.5500",
            ],
        )
        self.assertEqual(first_manifest["fail_reasons"], second_manifest["fail_reasons"])


if __name__ == "__main__":
    unittest.main()
