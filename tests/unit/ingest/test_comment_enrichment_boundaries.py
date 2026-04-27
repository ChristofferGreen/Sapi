from __future__ import annotations

import unittest

from sapi.ingest.ingest_pipeline import plan_ingest_semantic_execution


class IngestCommentEnrichmentBoundaryTests(unittest.TestCase):
    def test_default_ingest_path_never_invokes_comment_section_generation(self) -> None:
        plan = plan_ingest_semantic_execution()
        self.assertEqual(plan.semantic_flows, ["ingest_extraction", "topic_generation"])
        self.assertEqual(
            plan.semantic_flow_invocation_counts,
            {"ingest_extraction": 1, "topic_generation": 1},
        )
        self.assertNotIn("comment_section_generation", plan.semantic_flows)

    def test_revision_detection_plan_is_optional_prefix_when_it_runs(self) -> None:
        plan = plan_ingest_semantic_execution(include_source_revision_detection=True)
        self.assertEqual(
            plan.semantic_flows,
            ["source_revision_detection", "ingest_extraction", "topic_generation"],
        )
        self.assertEqual(
            plan.semantic_flow_invocation_counts,
            {
                "source_revision_detection": 1,
                "ingest_extraction": 1,
                "topic_generation": 1,
            },
        )

    def test_optional_enrichment_requires_explicit_opt_in(self) -> None:
        with self.assertRaises(ValueError):
            plan_ingest_semantic_execution(
                requested_comment_count=5,
                comment_target_page_refs=["topic:topic-a"],
            )

    def test_opt_in_enrichment_preserves_comment_pipeline_contract_bounds(self) -> None:
        with self.assertRaises(ValueError):
            plan_ingest_semantic_execution(
                enable_comment_enrichment=True,
                requested_comment_count=4,
                comment_target_page_refs=["topic:topic-a"],
            )
        with self.assertRaises(ValueError):
            plan_ingest_semantic_execution(
                enable_comment_enrichment=True,
                requested_comment_count=51,
                comment_target_page_refs=["topic:topic-a"],
            )
        with self.assertRaises(ValueError):
            plan_ingest_semantic_execution(
                enable_comment_enrichment=True,
                requested_comment_count=10,
                comment_target_page_refs=["profile:persona-a"],
            )

    def test_run_metadata_counts_are_boundary_correct_for_ingest_modes(self) -> None:
        enriched_plan = plan_ingest_semantic_execution(
            enable_comment_enrichment=True,
            requested_comment_count=10,
            comment_target_page_refs=["topic:topic-a", "source:source-a", "claim:claim-a"],
        )
        self.assertEqual(
            enriched_plan.semantic_flows,
            ["ingest_extraction", "topic_generation", "comment_section_generation"],
        )
        self.assertEqual(
            enriched_plan.semantic_flow_invocation_counts,
            {
                "ingest_extraction": 1,
                "topic_generation": 1,
                "comment_section_generation": 3,
            },
        )


if __name__ == "__main__":
    unittest.main()
