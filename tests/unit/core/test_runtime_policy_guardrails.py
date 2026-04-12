from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.contracts.run_envelopes import QueryRunFields, RunEnvelopeBase, write_run_record
from sapi.core.runtime_policy import DISALLOWED_FLOW_ENV_VARS, evaluate_semantic_runtime_policy


class RuntimePolicyGuardrailsTests(unittest.TestCase):
    def test_production_flow_rejects_deterministic_fallback(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_semantic_runtime_policy(
                mock_llm=False,
                deterministic_fallback_requested=True,
                env={},
            )

    def test_flow_behavior_cannot_be_controlled_by_env_vars(self) -> None:
        for key in DISALLOWED_FLOW_ENV_VARS:
            with self.subTest(env_key=key):
                with self.assertRaises(ValueError):
                    evaluate_semantic_runtime_policy(
                        mock_llm=False,
                        env={key: "1"},
                    )

    def test_mock_mode_is_test_only_and_auditable_via_execution_mode_in_run_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            policy = evaluate_semantic_runtime_policy(mock_llm=True, env={})
            self.assertEqual(policy.execution_mode, "mock_llm_test")

            base = RunEnvelopeBase(
                run_id="run-20260412T120000Z--abcdefghij",
                flow_key="query_pipeline",
                semantic_flows=["query_synthesis"],
                semantic_flow_invocation_counts={"query_synthesis": 1},
                status="success",
                started_at="2026-04-12T12:00:00Z",
                completed_at="2026-04-12T12:00:05Z",
                model_fingerprint="model-x",
                provider_fingerprint="provider-y",
                reasoning_effort="high",
                execution_mode=policy.execution_mode,
                llm_attempt_count=1,
                lint_error_count=0,
                lint_warning_count=0,
                lint_info_count=0,
                toolchain_versions={"python": "3.12"},
            )
            write_run_record(
                space_root=space_root,
                base=base,
                flow_fields=QueryRunFields(
                    query_id="query-20260412T120000Z-q--abcdefghij",
                    mode="strict",
                    scope="space",
                    claims_used=0,
                    sources_used=0,
                    contradictions_considered=0,
                    manifest_path=None,
                ),
            )
            run_md = space_root / "runs" / base.run_id / "run.md"
            frontmatter = _parse_frontmatter(run_md.read_text())
            self.assertEqual(frontmatter["execution_mode"], "mock_llm_test")


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
