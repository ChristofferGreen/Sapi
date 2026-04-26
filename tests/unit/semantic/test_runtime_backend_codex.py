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
    def __init__(self, *, writer) -> None:
        self.stdin = _FakeStdin()
        self.stdout = io.StringIO('{"type":"item.started","item":"semantic"}\n')
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

    def test_live_semantic_generation_uses_codex_defaults_and_returns_written_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "semantic.json"
            request = _request_for(output_path)
            popen_calls: list[tuple[list[str], dict[str, object]]] = []
            processes: list[_FakeProcess] = []
            prompts: list[str] = []

            def writer(prompt: str) -> None:
                prompts.append(prompt)
                payload = _payload_from_prompt(prompt)
                resolved_output_path = Path(str(payload["output_json_path"]))
                resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
                resolved_output_path.write_text(json.dumps({"ok": True, "flow": payload["flow_key"]}) + "\n")

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
            self.assertEqual(len(popen_calls), 1)
            command, kwargs = popen_calls[0]
            self.assertIn("codex", command[0])
            self.assertIn("--model", command)
            self.assertIn(DEFAULT_LIVE_LLM_MODEL, command)
            self.assertIn("--json", command)
            self.assertIn("--sandbox", command)
            self.assertIn("workspace-write", command)
            self.assertIn("-c", command)
            self.assertIn('model_reasoning_effort="high"', command)
            self.assertFalse(any("openai_base_url" in arg for arg in command))
            self.assertIn("--add-dir", command)
            self.assertIn(str(output_path.parent.resolve()), command)
            self.assertTrue(kwargs["text"])
            self.assertEqual(kwargs["bufsize"], 1)
            self.assertEqual(len(processes), 1)
            self.assertIsNone(processes[0].wait_timeout)
            self.assertEqual(len(prompts), 1)
            self.assertIn("Do not use apply_patch or patch-style edits for output_json_path.", prompts[0])
            self.assertIn("Write output_json_path directly in one step with a shell redirect or short script.", prompts[0])
            self.assertIn("Do not probe whether output_json_path exists before writing; just overwrite it.", prompts[0])
            self.assertEqual(json.loads(output_path.read_text())["ok"], True)

    def test_live_semantic_generation_requires_json_object_from_written_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "semantic.json"
            request = _request_for(output_path)

            def writer(prompt: str) -> None:
                payload = _payload_from_prompt(prompt)
                resolved_output_path = Path(str(payload["output_json_path"]))
                resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
                resolved_output_path.write_text('["not-an-object"]\n')

            with patch(
                "sapi.llm.runtime_backend.subprocess.Popen",
                return_value=_FakeProcess(writer=writer),
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


def _payload_from_prompt(prompt: str) -> dict[str, object]:
    marker = "Semantic request payload:\n"
    if marker not in prompt:
        raise AssertionError("Prompt missing semantic request payload marker.")
    payload_text = prompt.split(marker, 1)[1]
    payload = json.loads(payload_text)
    if not isinstance(payload, dict):
        raise AssertionError("Prompt payload must be a JSON object.")
    return payload


if __name__ == "__main__":
    unittest.main()
