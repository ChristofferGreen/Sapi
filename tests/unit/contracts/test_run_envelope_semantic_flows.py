from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.contracts.run_envelopes import (
    CommentRunFields,
    IngestRunFields,
    PersonaProfileRunFields,
    QueryRunFields,
    RunEnvelopeBase,
    run_record_path,
    write_run_record,
)


class RunEnvelopeWriterTests(unittest.TestCase):
    def test_run_record_writes_to_canonical_run_md_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            base = _make_base(flow_key="query_pipeline")
            path = write_run_record(
                space_root=space_root,
                base=base,
                flow_fields=_query_fields(),
            )
            self.assertEqual(path, run_record_path(space_root=space_root, run_id=base.run_id))
            self.assertTrue(path.exists())

    def test_base_fields_include_semantic_flows_and_invocation_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            base = _make_base(flow_key="ingest_pipeline")
            write_run_record(
                space_root=space_root,
                base=base,
                flow_fields=_ingest_fields(),
            )
            text = run_record_path(space_root=space_root, run_id=base.run_id).read_text()
            frontmatter = _parse_frontmatter(text)
            self.assertIn("semantic_flows", frontmatter)
            self.assertIn("semantic_flow_invocation_counts", frontmatter)
            self.assertEqual(frontmatter["semantic_flows"], ["ingest_extraction", "topic_generation"])
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"ingest_extraction": 1, "topic_generation": 1},
            )

    def test_required_run_body_sections_are_always_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            base = _make_base(flow_key="query_pipeline")
            run_path = write_run_record(
                space_root=space_root,
                base=base,
                flow_fields=_query_fields(),
                summary="done",
            )
            text = run_path.read_text()
            self.assertIn("## Summary", text)
            self.assertIn("## Changes", text)
            self.assertIn("## Lint Summary", text)
            self.assertIn("## Errors", text)

    def test_required_run_body_sections_are_emitted_in_order_with_none_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            base = _make_base(flow_key="query_pipeline")
            run_path = write_run_record(
                space_root=space_root,
                base=base,
                flow_fields=_query_fields(),
                summary="",
                changes="",
                lint_summary="",
                errors="",
            )
            text = run_path.read_text()
            expected_sections = [
                "## Summary\n(none)\n",
                "## Changes\n(none)\n",
                "## Lint Summary\n(none)\n",
                "## Errors\n(none)\n",
            ]
            start = 0
            for section in expected_sections:
                offset = text.find(section, start)
                self.assertNotEqual(offset, -1, f"Missing section block: {section!r}")
                start = offset + len(section)

    def test_flow_specific_extension_fields_are_present_and_typed_by_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"

            cases = [
                (
                    "ingest_pipeline",
                    _ingest_fields(),
                    {"ingest_scope", "source_ids", "force_mode", "rollback_skipped"},
                ),
                (
                    "query_pipeline",
                    _query_fields(),
                    {"query_id", "mode", "scope", "manifest_path"},
                ),
                (
                    "comment_section_pipeline",
                    _comment_fields(),
                    {"target_page_refs", "requested_count", "comments_added", "adjudication", "generation_isolation"},
                ),
                (
                    "persona_profile_pipeline",
                    _profile_fields(),
                    {"persona_ids", "history_generated", "history_updated", "pages_changed"},
                ),
            ]

            for flow_key, extension, required_keys in cases:
                with self.subTest(flow_key=flow_key):
                    base = _make_base(flow_key=flow_key)
                    write_run_record(space_root=space_root, base=base, flow_fields=extension)
                    text = run_record_path(space_root=space_root, run_id=base.run_id).read_text()
                    frontmatter = _parse_frontmatter(text)
                    for key in required_keys:
                        self.assertIn(key, frontmatter)

            with self.assertRaises(TypeError):
                write_run_record(
                    space_root=space_root,
                    base=_make_base(flow_key="query_pipeline"),
                    flow_fields=_ingest_fields(),
                )


def _make_base(*, flow_key: str) -> RunEnvelopeBase:
    return RunEnvelopeBase(
        run_id=f"run-20260412T120000Z--{flow_key[:10]}",
        flow_key=flow_key,  # type: ignore[arg-type]
        semantic_flows=["ingest_extraction", "topic_generation"],
        semantic_flow_invocation_counts={"ingest_extraction": 1, "topic_generation": 1},
        status="success",
        started_at="2026-04-12T12:00:00Z",
        completed_at="2026-04-12T12:00:05Z",
        model_fingerprint="model-x",
        provider_fingerprint="provider-y",
        reasoning_effort="high",
        execution_mode="live_llm",
        llm_attempt_count=2,
        lint_error_count=0,
        lint_warning_count=0,
        lint_info_count=0,
        toolchain_versions={"python": "3.12"},
    )


def _ingest_fields() -> IngestRunFields:
    return IngestRunFields(
        ingest_scope="space",
        source_ids=["source-a"],
        parent_run_id=None,
        claims_changed=1,
        relations_changed=1,
        topic_pages_changed=1,
        build_deferred=False,
        deferred_build_reason=None,
        force_mode=False,
        rollback_skipped=False,
    )


def _query_fields() -> QueryRunFields:
    return QueryRunFields(
        query_id="query-20260412T120000Z-what-is-x--abcdefghij",
        mode="strict",
        scope="space",
        claims_used=1,
        sources_used=1,
        contradictions_considered=0,
        manifest_path=None,
    )


def _comment_fields() -> CommentRunFields:
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


def _profile_fields() -> PersonaProfileRunFields:
    return PersonaProfileRunFields(
        persona_ids=["alice"],
        history_generated=1,
        history_updated=1,
        history_reused=0,
        pages_changed=1,
    )


def _parse_frontmatter(markdown: str) -> dict[str, object]:
    lines = markdown.splitlines()
    if len(lines) < 3 or lines[0] != "---":
        raise AssertionError("Missing frontmatter start")
    result: dict[str, object] = {}
    index = 1
    while index < len(lines) and lines[index] != "---":
        line = lines[index]
        key, raw = line.split(":", 1)
        result[key.strip()] = json.loads(raw.strip())
        index += 1
    if index >= len(lines) or lines[index] != "---":
        raise AssertionError("Missing frontmatter end")
    return result


if __name__ == "__main__":
    unittest.main()
