from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.llm.client import SemanticLlmRequest
from sapi.llm.semantic_executor import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_REPAIR_LOOPS,
    SemanticFlowError,
    SemanticSpec,
    max_attempts_from_repair_loops,
    run_semantic_flow,
)


class _FakeLlmClient:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = outputs
        self.requests: list[SemanticLlmRequest] = []
        self.call_count = 0

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        self.requests.append(request)
        index = min(self.call_count, len(self._outputs) - 1)
        self.call_count += 1
        return self._outputs[index]


class RetryBudgetTests(unittest.TestCase):
    def test_default_budget_enforces_max_repair_loops_3_and_max_attempts_4(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            schema_path = _write_schema(tmp_root)
            output_path = tmp_root / "space/runs/run-1/semantic/topic_generation.json"
            spec = _build_spec(schema_path=schema_path, output_path=output_path, context_paths=[])

            client = _FakeLlmClient(outputs=["{}", "{}", "{}", "{}"])
            with self.assertRaises(SemanticFlowError) as raised:
                run_semantic_flow(spec=spec, llm_client=client)

            error = raised.exception
            self.assertEqual(DEFAULT_MAX_REPAIR_LOOPS, 3)
            self.assertEqual(DEFAULT_MAX_ATTEMPTS, 4)
            self.assertEqual(client.call_count, DEFAULT_MAX_ATTEMPTS)
            self.assertEqual(error.attempt_count, DEFAULT_MAX_ATTEMPTS)
            self.assertEqual(error.max_attempts, DEFAULT_MAX_ATTEMPTS)
            self.assertFalse(output_path.exists())

    def test_attempt_budget_helper_uses_initial_attempt_plus_repairs(self) -> None:
        self.assertEqual(max_attempts_from_repair_loops(0), 1)
        self.assertEqual(max_attempts_from_repair_loops(DEFAULT_MAX_REPAIR_LOOPS), DEFAULT_MAX_ATTEMPTS)

    def test_attempt_budget_helper_rejects_negative_repair_loops(self) -> None:
        with self.assertRaises(ValueError):
            max_attempts_from_repair_loops(-1)

    def test_repair_attempt_receives_invalid_json_validation_errors_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            schema_path = _write_schema(tmp_root)
            output_path = tmp_root / "space/topics/topic-a.json"
            spec = _build_spec(schema_path=schema_path, output_path=output_path, context_paths=[])

            client = _FakeLlmClient(outputs=["{}", '{"value":"ok"}'])
            result, attempt_count = run_semantic_flow(spec=spec, llm_client=client)

            self.assertEqual(attempt_count, 2)
            self.assertEqual(result, {"value": "ok"})
            self.assertEqual(client.call_count, 2)

            first_request = client.requests[0]
            self.assertIsNone(first_request.repair_context)

            second_request = client.requests[1]
            self.assertIsNotNone(second_request.repair_context)
            repair = second_request.repair_context
            assert repair is not None
            self.assertEqual(repair.previous_invalid_json, "{}")
            self.assertEqual(repair.schema, json.loads(schema_path.read_text()))
            self.assertTrue(repair.require_complete_replacement_json)
            self.assertGreaterEqual(len(repair.validation_errors), 1)
            self.assertTrue(
                any(error["validator"] == "required" for error in repair.validation_errors)
            )

            self.assertEqual(json.loads(output_path.read_text()), {"value": "ok"})

    def test_invalid_outputs_never_overwrite_existing_canonical_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            schema_path = _write_schema(tmp_root)
            output_path = tmp_root / "space/topics/topic-a.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text('{"value":"stable"}\n')
            spec = _build_spec(schema_path=schema_path, output_path=output_path, context_paths=[])

            client = _FakeLlmClient(outputs=["{}", "{}", "{}", "{}"])
            with self.assertRaises(SemanticFlowError):
                run_semantic_flow(spec=spec, llm_client=client)

            self.assertEqual(json.loads(output_path.read_text()), {"value": "stable"})


def _write_schema(tmp_root: Path) -> Path:
    schema_path = tmp_root / "schemas" / "topic_generation.v1.schema.json"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": False,
                "required": ["value"],
                "properties": {"value": {"type": "string"}},
            }
        )
        + "\n"
    )
    return schema_path


def _build_spec(*, schema_path: Path, output_path: Path, context_paths: list[Path]) -> SemanticSpec:
    return SemanticSpec(
        flow_key="topic_generation",
        version="v1",
        schema_path=schema_path,
        output_json_path=output_path,
        context_paths=context_paths,
        spec_path=None,
    )


if __name__ == "__main__":
    unittest.main()
