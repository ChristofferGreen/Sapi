from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.llm.client import SemanticLlmRequest
from sapi.llm.semantic_executor import SemanticSpec, run_semantic_flow
from sapi.llm.trace import SiteLlmTraceContext


class _StaticSemanticClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.requests: list[SemanticLlmRequest] = []

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        self.requests.append(request)
        return json.dumps(self._payload)


class LlmTraceArtifactTests(unittest.TestCase):
    def test_semantic_trace_context_persists_required_trace_file_set_under_site_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = tmp_root / "site-a"
            site_path.mkdir(parents=True, exist_ok=True)
            space_root = site_path / "spaces" / "alpha"
            output_path = space_root / "topics" / "topic-a.json"
            schema_path = _write_schema(tmp_root)
            context_path = space_root / "claims"
            context_path.mkdir(parents=True, exist_ok=True)
            context_file = context_path / "claim-a.json"
            context_file.write_text('{"claim_id":"claim-a"}\n')

            trace_ctx = SiteLlmTraceContext(site_path=site_path, verbose=False)
            client = _StaticSemanticClient({"value": "ok"})
            run_semantic_flow(
                spec=SemanticSpec(
                    flow_key="topic_generation",
                    version="v1",
                    schema_path=schema_path,
                    output_json_path=output_path,
                    context_paths=[context_file],
                    spec_path=None,
                ),
                llm_client=client,
                trace_ctx=trace_ctx,
            )

            trace_dirs = sorted((site_path / "outputs" / "llm_traces").glob("*"))
            self.assertEqual(len(trace_dirs), 1)
            trace_dir = trace_dirs[0]
            self.assertIn("topic_generation", trace_dir.name)
            self.assertIn("-1", trace_dir.name)

            self.assertTrue((trace_dir / "semantic.prompt.txt").is_file())
            self.assertTrue((trace_dir / "semantic.context.json").is_file())
            self.assertTrue((trace_dir / "semantic.response.txt").is_file())
            self.assertTrue((trace_dir / "semantic.response.json").is_file())
            self.assertTrue((trace_dir / "semantic.codex.stdout.jsonl").is_file())
            self.assertTrue((trace_dir / "semantic.codex.stderr.txt").is_file())
            self.assertTrue((trace_dir / "semantic.meta.json").is_file())

            meta = json.loads((trace_dir / "semantic.meta.json").read_text())
            self.assertEqual(meta["flow_key"], "topic_generation")
            self.assertEqual(meta["attempt"], 1)
            self.assertEqual(meta["max_attempts"], 4)
            self.assertTrue(meta["valid"])
            self.assertEqual(meta["validation_errors"], [])
            self.assertEqual(meta["trace_root"], str((site_path / "outputs" / "llm_traces").resolve()))
            self.assertEqual(meta["trace_dir"], str(trace_dir.resolve()))


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


if __name__ == "__main__":
    unittest.main()
