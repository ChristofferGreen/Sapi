from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sapi.query.query_pipeline import (
    build_query_result_record,
    canonical_query_manifest_path,
    validate_query_result_shape,
)


class QueryResultShapeContractTests(unittest.TestCase):
    def test_query_result_contains_required_high_signal_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space-a"
            record = _build_sample_record(space_root=space_root, output_mode="markdown")
            required = {
                "query_id",
                "answer",
                "claims_used",
                "sources_used",
                "retrieval_counts",
                "contradictions_considered",
                "falsification_signals",
                "omitted_due_to_budget",
                "mode",
                "scope",
                "run_id",
                "query_timestamp_utc",
                "citation_coverage",
                "lint_summary",
                "execution",
                "warnings",
                "manifest_path",
            }
            self.assertTrue(required.issubset(set(record.keys())))
            self.assertIsNone(record["manifest_path"])

    def test_optional_fields_follow_deterministic_presence_absence_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space-a"

            no_optionals = _build_sample_record(space_root=space_root, output_mode="markdown")
            self.assertNotIn("ancestor_pages_used", no_optionals)
            self.assertNotIn("inherited_conflicts", no_optionals)
            self.assertNotIn("synthesis_claim_ids", no_optionals)

            with_optionals = _build_sample_record(
                space_root=space_root,
                output_mode="markdown",
                ancestor_pages_used=["page-c", "page-a", "page-a"],
                inherited_conflicts=["conflict-b", "conflict-a"],
                synthesis_claim_ids=["claim-z", "claim-a", "claim-z"],
            )
            self.assertEqual(with_optionals["ancestor_pages_used"], ["page-a", "page-c"])
            self.assertEqual(with_optionals["inherited_conflicts"], ["conflict-a", "conflict-b"])
            self.assertEqual(with_optionals["synthesis_claim_ids"], ["claim-a", "claim-z"])

    def test_manifest_path_contract_depends_on_output_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space-a"

            markdown_record = _build_sample_record(space_root=space_root, output_mode="markdown")
            self.assertIsNone(markdown_record["manifest_path"])

            mermaid_record = _build_sample_record(space_root=space_root, output_mode="mermaid")
            self.assertEqual(
                mermaid_record["manifest_path"],
                str(
                    canonical_query_manifest_path(
                        space_root=space_root,
                        query_id=mermaid_record["query_id"],
                    )
                ),
            )

            invalid_markdown_record = dict(markdown_record)
            invalid_markdown_record["manifest_path"] = str(
                canonical_query_manifest_path(
                    space_root=space_root,
                    query_id=markdown_record["query_id"],
                )
            )
            with self.assertRaises(ValueError):
                validate_query_result_shape(
                    invalid_markdown_record,
                    output_mode="markdown",
                    space_root=space_root,
                )


def _build_sample_record(
    *,
    space_root: Path,
    output_mode: str,
    ancestor_pages_used: list[str] | None = None,
    inherited_conflicts: list[str] | None = None,
    synthesis_claim_ids: list[str] | None = None,
) -> dict[str, object]:
    return build_query_result_record(
        query_id="query-20260412T120000Z-example--abcdefghij",
        answer="Structured answer",
        claims_used=["claim-a", "claim-b"],
        sources_used=["source-a"],
        retrieval_counts={"claims_retrieved": 2, "sources_retrieved": 1},
        contradictions_considered=1,
        falsification_signals=[{"claim_id": "claim-a", "signal": "none"}],
        omitted_due_to_budget={"claims": 0, "sources": 0},
        mode="strict",
        scope="space",
        run_id="run-20260412T120000Z-ingest--abcdefghij",
        query_timestamp_utc="2026-04-12T12:00:00Z",
        citation_coverage={"factual_sentence_ratio": 0.95},
        lint_summary={"error_count": 0, "warning_count": 0, "info_count": 0},
        execution={
            "execution_mode": "mock_llm_test",
            "llm_attempt_count": 1,
            "reasoning_effort": "high",
            "model_fingerprint": "model-x",
            "provider_fingerprint": "provider-y",
        },
        warnings=[],
        output_mode=output_mode,
        space_root=space_root,
        ancestor_pages_used=ancestor_pages_used,
        inherited_conflicts=inherited_conflicts,
        synthesis_claim_ids=synthesis_claim_ids,
    )


if __name__ == "__main__":
    unittest.main()
