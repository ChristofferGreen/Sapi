from __future__ import annotations

import unittest

from sapi.llm.client import SemanticLlmRequest
from scripts.create_comments import _BootstrapCommentSectionClient, _audit_generation_isolation_request


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

    def test_bootstrap_client_rejects_request_when_leaks_are_detected(self) -> None:
        client = _BootstrapCommentSectionClient(
            page_ref="topic:topic-alpha",
            requested_count=5,
            persona_ids=["commenter-1", "commenter-2"],
        )
        with self.assertRaisesRegex(ValueError, "adjudication rubric"):
            client.generate_semantic_json(
                _request(
                    spec_text="Include scoring rubric guidance.",
                    context_by_path={"/tmp/topics": "dir:///tmp/topics"},
                )
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
