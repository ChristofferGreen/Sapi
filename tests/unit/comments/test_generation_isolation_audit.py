from __future__ import annotations

import unittest
from unittest.mock import patch

from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import SemanticBackendConfig
from scripts.create_comments import (
    _LiveCommentSectionClient,
    _MockCommentSectionClient,
    _audit_generation_isolation_request,
)


class GenerationIsolationAuditTests(unittest.TestCase):
    def test_audit_reports_zero_leaks_for_clean_request_payload(self) -> None:
        request = _request(spec_text="Generate comments as strict JSON.", context_by_path={"/tmp/topics": "dir:///tmp/topics"})
        summary = _audit_generation_isolation_request(request)
        self.assertEqual(summary["schema_version"], "comment_section_generation_context_v1")
        self.assertEqual(summary["prompt_leak_count"], 0)
        self.assertEqual(summary["context_leak_count"], 0)
        self.assertEqual(summary["total_leak_count"], 0)
        self.assertEqual(summary["detected_terms"], [])

    def test_audit_detects_adjudication_rubric_leaks(self) -> None:
        request = _request(
            spec_text="Do not expose the adjudication rubric.",
            context_by_path={"/tmp/topics": "dir:///tmp/topics", "/tmp/rubric": "file:///tmp/adjudication rubric.md"},
        )
        summary = _audit_generation_isolation_request(request)
        self.assertGreater(summary["prompt_leak_count"], 0)
        self.assertGreater(summary["context_leak_count"], 0)
        self.assertGreater(summary["total_leak_count"], 0)
        self.assertIn("adjudication rubric", summary["detected_terms"])

    def test_mock_client_rejects_request_when_leaks_are_detected(self) -> None:
        client = _MockCommentSectionClient(
            page_ref="topic:topic-alpha",
            requested_count=5,
            persona_ids=["commenter-1", "commenter-2"],
            page_payload={"topic_id": "topic-alpha", "title": "Topic Alpha"},
            original_source_context={"source_ids": [], "source_records": []},
        )
        with self.assertRaisesRegex(ValueError, "adjudication rubric"):
            client.generate_semantic_json(
                _request(
                    spec_text="Include scoring rubric guidance.",
                    context_by_path={"/tmp/topics": "dir:///tmp/topics"},
                )
            )

    def test_live_client_passes_style_constraints_to_semantic_backend(self) -> None:
        client = _LiveCommentSectionClient(
            backend_config=SemanticBackendConfig(
                backend="codex",
                model="gpt-5.5",
                reasoning_effort="high",
                timeout_secs=1000,
            ),
            page_ref="topic:topic-alpha",
            requested_count=5,
            persona_ids=["persona-maya-santoro", "persona-eli-okafor"],
            page_payload={"topic_id": "topic-alpha", "title": "Topic Alpha"},
            original_source_context={"source_ids": [], "source_records": []},
        )
        request = _request(
            spec_text="Generate comments as strict JSON.",
            context_by_path={"/tmp/topics": "dir:///tmp/topics"},
        )
        with patch("scripts.create_comments.generate_semantic_json_live") as mocked_generate:
            mocked_generate.return_value = (
                '{"page_ref":"topic:topic-alpha","requested_count":5,"comments":[]}'
            )
            client.generate_semantic_json(request)

        self.assertTrue(mocked_generate.called)
        task_context = mocked_generate.call_args.kwargs["task_context"]
        requirements = task_context["task_requirements"]
        self.assertEqual(requirements["must_use_page_ref"], "topic:topic-alpha")
        self.assertEqual(requirements["requested_count"], 5)
        self.assertIn("style_constraints", requirements)
        style_constraints = requirements["style_constraints"]
        self.assertIn(
            "Write natural discussion comments, not moderation-template prose.",
            style_constraints,
        )
        self.assertIn(
            "Do not use formulaic phrases like 'most defensible sentence is' or 'more persuasive if'.",
            style_constraints,
        )
        self.assertIn(
            "Never reference internal IDs or slug labels (for example source-paper-lowres). Use human-readable page titles.",
            style_constraints,
        )


def _request(*, spec_text: str, context_by_path: dict[str, str]) -> SemanticLlmRequest:
    return SemanticLlmRequest(
        flow_key="comment_section_generation",
        version="v1",
        schema_path="/tmp/schema.json",
        output_json_path="/tmp/out.json",
        context_paths=list(context_by_path.keys()),
        spec_text=spec_text,
        schema={"type": "object"},
        context_by_path=context_by_path,
        repair_context=None,
    )


if __name__ == "__main__":
    unittest.main()
