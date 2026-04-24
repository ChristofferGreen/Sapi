from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.contracts.run_envelopes import (
    CommentRunFields,
    OverviewRunFields,
    QueryRunFields,
    RunEnvelopeBase,
    write_run_record,
)


class RunEnvelopeMetadataInvariantTests(unittest.TestCase):
    def test_base_frontmatter_includes_required_runtime_fingerprint_toolchain_lint_fields_for_all_flows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            flows = [
                "ingest_pipeline",
                "query_pipeline",
                "comment_section_pipeline",
                "persona_profile_pipeline",
                "overview_pipeline",
            ]
            required_base_keys = {
                "run_id",
                "flow_key",
                "semantic_flows",
                "semantic_flow_invocation_counts",
                "status",
                "started_at",
                "completed_at",
                "model_fingerprint",
                "provider_fingerprint",
                "reasoning_effort",
                "execution_mode",
                "llm_attempt_count",
                "lint_error_count",
                "lint_warning_count",
                "lint_info_count",
                "toolchain_versions",
            }
            expected_extension_keys = {
                "ingest_pipeline": {"ingest_scope", "source_ids", "force_mode", "rollback_skipped"},
                "query_pipeline": {"query_id", "mode", "scope", "manifest_path"},
                "comment_section_pipeline": {
                    "target_page_refs",
                    "requested_count",
                    "comments_added",
                    "adjudication",
                    "generation_isolation",
                },
                "persona_profile_pipeline": {"persona_ids", "history_generated", "history_updated", "pages_changed"},
                "overview_pipeline": {
                    "overview_id",
                    "scope_kind",
                    "scope_name",
                    "source_records_used",
                    "article_path",
                },
            }

            for flow in flows:
                with self.subTest(flow=flow):
                    base = _base(flow_key=flow)
                    write_run_record(
                        space_root=space_root,
                        base=base,
                        flow_fields=_extension_for(flow),
                    )
                    run_md = space_root / "runs" / base.run_id / "run.md"
                    frontmatter = _parse_frontmatter(run_md.read_text())
                    self.assertTrue(required_base_keys.issubset(set(frontmatter.keys())))
                    self.assertTrue(expected_extension_keys[flow].issubset(set(frontmatter.keys())))

    def test_semantic_flow_ordered_unique_coverage_and_positive_count_invariants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            valid = _base(flow_key="query_pipeline")
            write_run_record(space_root=space_root, base=valid, flow_fields=_extension_for("query_pipeline"))

            duplicate = _base(flow_key="query_pipeline")
            duplicate.semantic_flows = ["query_synthesis", "query_synthesis"]
            duplicate.semantic_flow_invocation_counts = {"query_synthesis": 1}
            with self.assertRaises(ValueError):
                write_run_record(space_root=space_root, base=duplicate, flow_fields=_extension_for("query_pipeline"))

            missing_coverage = _base(flow_key="query_pipeline")
            missing_coverage.semantic_flows = ["query_synthesis"]
            missing_coverage.semantic_flow_invocation_counts = {}
            with self.assertRaises(ValueError):
                write_run_record(
                    space_root=space_root,
                    base=missing_coverage,
                    flow_fields=_extension_for("query_pipeline"),
                )

            non_positive = _base(flow_key="query_pipeline")
            non_positive.semantic_flows = ["query_synthesis"]
            non_positive.semantic_flow_invocation_counts = {"query_synthesis": 0}
            with self.assertRaises(ValueError):
                write_run_record(space_root=space_root, base=non_positive, flow_fields=_extension_for("query_pipeline"))

            extra_count_key = _base(flow_key="query_pipeline")
            extra_count_key.semantic_flows = ["query_synthesis"]
            extra_count_key.semantic_flow_invocation_counts = {
                "query_synthesis": 1,
                "topic_generation": 1,
            }
            with self.assertRaises(ValueError):
                write_run_record(space_root=space_root, base=extra_count_key, flow_fields=_extension_for("query_pipeline"))

            unknown_flow = _base(flow_key="query_pipeline")
            unknown_flow.semantic_flows = ["unknown_flow"]  # type: ignore[list-item]
            unknown_flow.semantic_flow_invocation_counts = {"unknown_flow": 1}  # type: ignore[dict-item]
            with self.assertRaises(ValueError):
                write_run_record(space_root=space_root, base=unknown_flow, flow_fields=_extension_for("query_pipeline"))

            unknown_count_key = _base(flow_key="query_pipeline")
            unknown_count_key.semantic_flows = ["query_synthesis"]
            unknown_count_key.semantic_flow_invocation_counts = {
                "query_synthesis": 1,
                "unknown_flow": 1,  # type: ignore[dict-item]
            }
            with self.assertRaises(ValueError):
                write_run_record(space_root=space_root, base=unknown_count_key, flow_fields=_extension_for("query_pipeline"))

    def test_flows_without_lint_build_use_consistent_zero_lint_totals_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            base = _base(flow_key="comment_section_pipeline")
            base.lint_error_count = 0
            base.lint_warning_count = 0
            base.lint_info_count = 0
            write_run_record(space_root=space_root, base=base, flow_fields=_extension_for("comment_section_pipeline"))
            frontmatter = _parse_frontmatter((space_root / "runs" / base.run_id / "run.md").read_text())
            self.assertEqual(frontmatter["lint_error_count"], 0)
            self.assertEqual(frontmatter["lint_warning_count"], 0)
            self.assertEqual(frontmatter["lint_info_count"], 0)

            invalid = _base(flow_key="comment_section_pipeline")
            invalid.lint_error_count = None  # type: ignore[assignment]
            with self.assertRaises(TypeError):
                write_run_record(space_root=space_root, base=invalid, flow_fields=_extension_for("comment_section_pipeline"))

    def test_started_and_completed_timestamps_require_rfc3339_utc_with_trailing_z(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"

            invalid_started = _base(flow_key="query_pipeline")
            invalid_started.started_at = "2026-04-12 12:00:00"
            with self.assertRaises(ValueError):
                write_run_record(
                    space_root=space_root,
                    base=invalid_started,
                    flow_fields=_extension_for("query_pipeline"),
                )

            invalid_completed = _base(flow_key="query_pipeline")
            invalid_completed.completed_at = "2026-04-12T12:00:05+00:00"
            with self.assertRaises(ValueError):
                write_run_record(
                    space_root=space_root,
                    base=invalid_completed,
                    flow_fields=_extension_for("query_pipeline"),
                )


def _base(*, flow_key: str) -> RunEnvelopeBase:
    return RunEnvelopeBase(
        run_id=f"run-20260412T120001Z--{flow_key[:10]}",
        flow_key=flow_key,  # type: ignore[arg-type]
        semantic_flows=["query_synthesis"],
        semantic_flow_invocation_counts={"query_synthesis": 1},
        status="success",
        started_at="2026-04-12T12:00:00Z",
        completed_at="2026-04-12T12:00:05Z",
        model_fingerprint="model-x",
        provider_fingerprint="provider-y",
        reasoning_effort="high",
        execution_mode="live_llm",
        llm_attempt_count=1,
        lint_error_count=0,
        lint_warning_count=0,
        lint_info_count=0,
        toolchain_versions={"python": "3.12"},
    )


def _extension_for(flow_key: str) -> object:
    if flow_key == "ingest_pipeline":
        from sapi.contracts.run_envelopes import IngestRunFields

        return IngestRunFields(
            ingest_scope="space",
            source_ids=["source-a"],
            parent_run_id=None,
            claims_changed=0,
            relations_changed=0,
            topic_pages_changed=0,
            build_deferred=False,
            deferred_build_reason=None,
            force_mode=False,
            rollback_skipped=False,
        )
    if flow_key == "query_pipeline":
        return QueryRunFields(
            query_id="query-20260412T120000Z-question--abcdefghij",
            mode="strict",
            scope="space",
            claims_used=1,
            sources_used=1,
            contradictions_considered=0,
            manifest_path=None,
        )
    if flow_key == "comment_section_pipeline":
        return CommentRunFields(
            target_page_refs=["topic:topic-a"],
            comment_user_filters=["alice"],
            requested_count=5,
            comments_added=4,
            adjudication={
                "rubric_id": "comment_section_adjudication_v1",
                "checks": {},
                "failures": {},
            },
            generation_isolation={
                "schema_version": "comment_section_generation_context_v1",
                "prompt_leak_count": 0,
                "context_leak_count": 0,
                "total_leak_count": 0,
            },
            evidence_mode="none",
            evidence_snapshot_path=None,
        )
    if flow_key == "persona_profile_pipeline":
        from sapi.contracts.run_envelopes import PersonaProfileRunFields

        return PersonaProfileRunFields(
            persona_ids=["alice"],
            history_generated=1,
            history_updated=1,
            history_reused=0,
            pages_changed=1,
        )
    if flow_key == "overview_pipeline":
        return OverviewRunFields(
            overview_id="space--alpha",
            scope_kind="space",
            scope_name="alpha",
            source_records_used=1,
            claims_used=1,
            relations_used=1,
            topics_used=1,
            article_path="/tmp/space/outputs/space_overview/space--alpha/article.md",
        )
    raise AssertionError(f"Unexpected flow_key: {flow_key}")


def _parse_frontmatter(markdown: str) -> dict[str, object]:
    lines = markdown.splitlines()
    result: dict[str, object] = {}
    index = 1
    while index < len(lines) and lines[index] != "---":
        key, raw = lines[index].split(":", 1)
        result[key.strip()] = json.loads(raw.strip())
        index += 1
    return result


if __name__ == "__main__":
    unittest.main()
