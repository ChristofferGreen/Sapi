from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sapi.core.runtime_config import DEFAULT_LIVE_LLM_MODEL
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import SemanticBackendConfig, generate_semantic_json_live


class _FakeStdin:
    def __init__(self) -> None:
        self._chunks: list[str] = []
        self.closed = False

    def write(self, content: str) -> int:
        self._chunks.append(content)
        return len(content)

    def close(self) -> None:
        self.closed = True

    def getvalue(self) -> str:
        return "".join(self._chunks)


class _FakeProcess:
    def __init__(
        self,
        *,
        writer,
        stdout_text: str | None = None,
    ) -> None:
        self.stdin = _FakeStdin()
        self.stdout = io.StringIO(stdout_text or _agent_message_event({"ok": True, "flow": "topic_generation"}))
        self.stderr = io.StringIO("")
        self._writer = writer
        self.returncode = 0
        self.pid = 4242
        self.wait_timeout: int | None | object = object()

    def wait(self, timeout: int | None = None) -> int:
        self.wait_timeout = timeout
        self._writer(self.stdin.getvalue())
        return self.returncode

    def kill(self) -> None:
        self.returncode = -9


class RuntimeBackendCodexTests(unittest.TestCase):
    def test_live_semantic_generation_rejects_non_codex_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = _request_for(Path(tmp) / "semantic.json")
            with self.assertRaisesRegex(RuntimeError, "Supported values: codex"):
                generate_semantic_json_live(
                    request=request,
                    backend_config=SemanticBackendConfig(
                        backend="gemini",
                        model=DEFAULT_LIVE_LLM_MODEL,
                        reasoning_effort="high",
                        timeout_secs=None,
                    ),
                )

    def test_live_semantic_generation_uses_codex_defaults_and_returns_final_json_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "semantic.json"
            request = _request_for(output_path)
            popen_calls: list[tuple[list[str], dict[str, object]]] = []
            processes: list[_FakeProcess] = []
            prompts: list[str] = []

            def writer(prompt: str) -> None:
                prompts.append(prompt)

            def fake_popen(command: list[str], **kwargs):
                popen_calls.append((command, kwargs))
                process = _FakeProcess(writer=writer)
                processes.append(process)
                return process

            with patch("sapi.llm.runtime_backend.subprocess.Popen", side_effect=fake_popen):
                raw = generate_semantic_json_live(
                    request=request,
                    backend_config=SemanticBackendConfig(
                        backend="codex",
                        model="",
                        reasoning_effort="high",
                        timeout_secs=None,
                    ),
                )

            parsed = json.loads(raw)
            self.assertEqual(parsed["ok"], True)
            self.assertEqual(parsed["flow"], "topic_generation")
            self.assertFalse(output_path.exists())
            self.assertEqual(len(popen_calls), 1)
            command, kwargs = popen_calls[0]
            self.assertIn("codex", command[0])
            self.assertIn("--model", command)
            self.assertIn(DEFAULT_LIVE_LLM_MODEL, command)
            self.assertIn("--json", command)
            self.assertIn("--sandbox", command)
            self.assertIn("read-only", command)
            self.assertNotIn("--output-schema", command)
            self.assertIn("-c", command)
            self.assertIn('model_reasoning_effort="high"', command)
            self.assertFalse(any("openai_base_url" in arg for arg in command))
            self.assertTrue(kwargs["text"])
            self.assertEqual(kwargs["bufsize"], 1)
            self.assertEqual(len(processes), 1)
            self.assertIsNone(processes[0].wait_timeout)
            self.assertEqual(len(prompts), 1)
            self.assertIn("Return exactly one JSON object as your final response.", prompts[0])
            self.assertIn("Do not write output_json_path yourself", prompts[0])
            self.assertIn("Do not create, modify, overwrite, or delete any files.", prompts[0])
            self.assertIn("Do not use shell, Python, Node, jq, or other code to construct", prompts[0])

    def test_live_semantic_generation_requires_json_object_from_final_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "semantic.json"
            request = _request_for(output_path)

            with patch(
                "sapi.llm.runtime_backend.subprocess.Popen",
                return_value=_FakeProcess(
                    writer=lambda _prompt: None,
                    stdout_text=_agent_message_event(["not-an-object"]),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "must be a JSON object"):
                    generate_semantic_json_live(
                        request=request,
                        backend_config=SemanticBackendConfig(
                            backend="codex",
                            model=DEFAULT_LIVE_LLM_MODEL,
                            reasoning_effort="high",
                            timeout_secs=None,
                        ),
                    )

    def test_live_semantic_generation_rejects_code_constructed_output_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "semantic.json"
            request = _request_for(output_path)
            stdout_text = (
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "command": "/bin/bash -lc \"python3 - <<'PY'\\nimport json\\nPY\"",
                        },
                    }
                )
                + "\n"
                + _agent_message_event({"ok": True})
            )

            with patch(
                "sapi.llm.runtime_backend.subprocess.Popen",
                return_value=_FakeProcess(writer=lambda _prompt: None, stdout_text=stdout_text),
            ):
                with self.assertRaisesRegex(RuntimeError, "disallowed command"):
                    generate_semantic_json_live(
                        request=request,
                        backend_config=SemanticBackendConfig(
                            backend="codex",
                            model=DEFAULT_LIVE_LLM_MODEL,
                            reasoning_effort="high",
                            timeout_secs=None,
                        ),
                    )


def _request_for(output_path: Path) -> SemanticLlmRequest:
    return SemanticLlmRequest(
        flow_key="topic_generation",
        version="v1",
        schema_path=str((output_path.parent / "schema.json").resolve()),
        output_json_path=str(output_path.resolve()),
        context_paths=[str((output_path.parent / "context").resolve())],
        spec_text="# spec",
        schema={"type": "object"},
        context_by_path={str((output_path.parent / "context").resolve()): f"dir://{(output_path.parent / 'context').resolve()}"},
        repair_context=None,
    )


def _agent_message_event(payload: object) -> str:
    return (
        json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "id": "item_0",
                    "type": "agent_message",
                    "text": json.dumps(payload),
                },
            }
        )
        + "\n"
    )


if __name__ == "__main__":
    unittest.main()
