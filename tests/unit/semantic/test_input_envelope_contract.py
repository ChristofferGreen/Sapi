from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.contracts.semantic_specs import FLOW_MAP, validate_semantic_invocation_spec
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.semantic_executor import (
    SemanticSpec,
    build_semantic_spec_from_contract,
    ensure_context_pointer_payload,
    run_semantic_flow,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


class _CapturingLlmClient:
    def __init__(self, output_json: str) -> None:
        self.output_json = output_json
        self.requests: list[SemanticLlmRequest] = []

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        self.requests.append(request)
        return self.output_json


class SemanticInputEnvelopeContractTests(unittest.TestCase):
    def test_all_semantic_flows_resolve_canonical_invocation_envelope_fields(self) -> None:
        space_root = (REPO_ROOT / ".tmp/tests/space").resolve()
        site_path = (REPO_ROOT / ".tmp/tests/site").resolve()
        common_tokens: dict[str, str | Path] = {
            "space_root": space_root,
            "site_path": site_path,
            "run_id": "run-001",
            "query_id": "query-001",
            "topic_id": "topic-001",
            "persona_id": "persona-001",
            "page_ref_key": "topic--topic-001",
        }

        for flow_key in FLOW_MAP:
            with self.subTest(flow_key=flow_key):
                spec = build_semantic_spec_from_contract(
                    flow_key,
                    repo_root=REPO_ROOT,
                    path_tokens=common_tokens,
                )
                self.assertEqual(spec.schema_path, (REPO_ROOT / FLOW_MAP[flow_key].schema_relpath).resolve())
                self.assertTrue(spec.output_json_path.is_absolute())
                self.assertGreater(len(spec.context_paths), 0)
                for context_path in spec.context_paths:
                    self.assertTrue(context_path.is_absolute())

    def test_semantic_invocation_uses_canonical_contract_fields(self) -> None:
        space_root = (REPO_ROOT / ".tmp/tests/space").resolve()
        spec = build_semantic_spec_from_contract(
            "query_synthesis",
            repo_root=REPO_ROOT,
            path_tokens={
                "space_root": space_root,
                "query_id": "query-001",
            },
        )

        self.assertEqual(
            spec.schema_path,
            (REPO_ROOT / "schemas/query_synthesis.v1.schema.json").resolve(),
        )
        self.assertEqual(
            spec.output_json_path,
            (space_root / "outputs/query/query-001/query.json").resolve(),
        )
        self.assertEqual(
            spec.context_paths,
            [
                (space_root / "topics").resolve(),
                (space_root / "claims").resolve(),
                (space_root / "sources").resolve(),
            ],
        )

    def test_prompt_context_payload_uses_filesystem_pointers_not_inline_dumps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            schema_path = tmp_root / "schemas/topic_generation.v1.schema.json"
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
            output_path = tmp_root / "space/topics/topic-a.json"
            context_file = tmp_root / "space/claims/claim-1.json"
            context_file.parent.mkdir(parents=True, exist_ok=True)
            context_file.write_text('{"sensitive":"INLINE-DUMP-SHOULD-NOT-APPEAR"}\n')
            context_dir = tmp_root / "space/sources"
            context_dir.mkdir(parents=True, exist_ok=True)

            spec = SemanticSpec(
                flow_key="topic_generation",
                version="v1",
                schema_path=schema_path,
                output_json_path=output_path,
                context_paths=[context_file, context_dir],
                spec_path=None,
            )
            client = _CapturingLlmClient('{"value":"ok"}')
            run_semantic_flow(spec=spec, llm_client=client)

            request = client.requests[0]
            self.assertEqual(request.schema_path, str(schema_path.resolve()))
            self.assertEqual(request.output_json_path, str(output_path.resolve()))
            self.assertEqual(request.context_paths, [str(context_file.resolve()), str(context_dir.resolve())])
            file_payload = request.context_by_path[str(context_file.resolve())]
            dir_payload = request.context_by_path[str(context_dir.resolve())]
            self.assertEqual(file_payload, f"file://{context_file.resolve()}")
            self.assertEqual(dir_payload, f"dir://{context_dir.resolve()}")
            self.assertNotIn("INLINE-DUMP-SHOULD-NOT-APPEAR", file_payload)

    def test_validation_rejects_semantic_invocation_envelope_drift(self) -> None:
        space_root = (REPO_ROOT / ".tmp/tests/space").resolve()
        with self.assertRaises(ValueError):
            validate_semantic_invocation_spec(
                "ingest_extraction",
                repo_root=REPO_ROOT,
                path_tokens={
                    "space_root": space_root,
                    "run_id": "run-001",
                },
                schema_path=(REPO_ROOT / "schemas/ingest_extraction.v1.schema.json").resolve(),
                output_json_path=(space_root / "runs/run-001/semantic/not-canonical.json").resolve(),
                context_paths=[
                    (space_root / "sources").resolve(),
                    (space_root / "claims").resolve(),
                    (space_root / "relations").resolve(),
                ],
            )

    def test_prompt_context_payload_guard_rejects_non_pointer_payload(self) -> None:
        with self.assertRaises(ValueError):
            ensure_context_pointer_payload(
                {
                    str((REPO_ROOT / "claims").resolve()): '{"inline":"not-allowed"}',
                }
            )


if __name__ == "__main__":
    unittest.main()
