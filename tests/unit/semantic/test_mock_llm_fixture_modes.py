from __future__ import annotations

import unittest

from sapi.llm.client import SemanticLlmRequest
from tests.conftest import create_deterministic_mock_llm_fixture


def _build_request() -> SemanticLlmRequest:
    return SemanticLlmRequest(
        flow_key="topic_generation",
        version="v1",
        schema_path="/tmp/schema.json",
        output_json_path="/tmp/output.json",
        context_paths=["/tmp/context"],
        spec_text="",
        schema={},
        context_by_path={},
        repair_context=None,
    )


class DeterministicMockLlmFixtureModeTests(unittest.TestCase):
    def test_valid_mode_returns_valid_payload_on_every_attempt(self) -> None:
        fixture = create_deterministic_mock_llm_fixture(
            mode="valid",
            valid_payload={"value": "stable"},
        )
        first = fixture.generate_semantic_json(_build_request())
        second = fixture.generate_semantic_json(_build_request())
        self.assertEqual(first, '{"value": "stable"}')
        self.assertEqual(second, '{"value": "stable"}')
        self.assertEqual(fixture.call_count, 2)

    def test_invalid_then_repair_mode_switches_after_first_attempt(self) -> None:
        fixture = create_deterministic_mock_llm_fixture(
            mode="invalid_then_repair",
            valid_payload={"value": "fixed"},
        )
        first = fixture.generate_semantic_json(_build_request())
        second = fixture.generate_semantic_json(_build_request())
        third = fixture.generate_semantic_json(_build_request())
        self.assertEqual(first, "{}")
        self.assertEqual(second, '{"value": "fixed"}')
        self.assertEqual(third, '{"value": "fixed"}')
        self.assertEqual(fixture.call_count, 3)

    def test_repair_exhausted_mode_always_returns_invalid_output(self) -> None:
        fixture = create_deterministic_mock_llm_fixture(mode="repair_exhausted")
        first = fixture.generate_semantic_json(_build_request())
        second = fixture.generate_semantic_json(_build_request())
        self.assertEqual(first, "{}")
        self.assertEqual(second, "{}")
        self.assertEqual(fixture.call_count, 2)

    def test_unknown_mode_fails_fast(self) -> None:
        with self.assertRaises(ValueError):
            create_deterministic_mock_llm_fixture(mode="unknown")


if __name__ == "__main__":
    unittest.main()
