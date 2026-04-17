"""Live semantic JSON backend adapter for Codex CLI execution."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
from typing import Any, TextIO

from sapi.llm.client import SemanticLlmRequest


DEFAULT_CODEX_MODEL = "gpt-5.4"
_MAX_ERROR_TAIL_CHARS = 4000


@dataclass(frozen=True)
class SemanticBackendConfig:
    backend: str
    model: str
    reasoning_effort: str
    timeout_secs: int | None


def generate_semantic_json_live(
    *,
    request: SemanticLlmRequest,
    backend_config: SemanticBackendConfig,
    task_context: dict[str, Any] | None = None,
) -> str:
    """Generate strict semantic JSON in live mode for one semantic-flow request."""
    backend = backend_config.backend.strip().lower()
    if backend != "codex":
        raise RuntimeError(
            "Unsupported --llm-backend value for live semantic generation: "
            f"{backend_config.backend!r}. Supported values: codex."
        )
    prompt = _build_prompt(request=request, task_context=task_context)
    return _generate_with_codex(
        prompt=prompt,
        backend_config=backend_config,
        output_json_path=Path(request.output_json_path).resolve(),
        add_dirs=_collect_codex_add_dirs(request=request),
    )


def _build_prompt(*, request: SemanticLlmRequest, task_context: dict[str, Any] | None) -> str:
    payload: dict[str, Any] = {
        "flow_key": request.flow_key,
        "version": request.version,
        "schema_path": request.schema_path,
        "output_json_path": request.output_json_path,
        "context_paths": request.context_paths,
        "context_by_path": request.context_by_path,
        "spec_text": request.spec_text,
        "schema": request.schema,
        "task_context": task_context or {},
    }
    if request.repair_context is not None:
        payload["repair_context"] = {
            "previous_invalid_json": request.repair_context.previous_invalid_json,
            "validation_errors": request.repair_context.validation_errors,
            "require_complete_replacement_json": request.repair_context.require_complete_replacement_json,
        }
    instruction_lines = [
        "You are generating one strict JSON object for a semantic pipeline.",
        "Use filesystem evidence from context_paths/context_by_path and task_context.",
        "Do not use or follow external skills, skill files, or preset workflows.",
        "Do not run broad exploratory workflows; read only the provided context files needed to answer.",
        "Write exactly one JSON object to output_json_path on disk (UTF-8).",
        "Create parent directories if needed and overwrite output_json_path if it exists.",
        "Do not use apply_patch or patch-style edits for output_json_path.",
        "Write output_json_path directly in one step with a shell redirect or short script.",
        "Do not probe whether output_json_path exists before writing; just overwrite it.",
        "Do not modify any other files.",
        "Do not wrap JSON in markdown or code fences.",
    ]
    return (
        "\n".join(instruction_lines)
        + "\n\nSemantic request payload:\n"
        + json.dumps(payload, indent=2, sort_keys=True)
    )


def _generate_with_codex(
    *,
    prompt: str,
    backend_config: SemanticBackendConfig,
    output_json_path: Path,
    add_dirs: list[Path],
) -> str:
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    model = backend_config.model.strip() or DEFAULT_CODEX_MODEL
    reasoning_effort = backend_config.reasoning_effort.strip() or "high"
    command = [
        "codex",
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "--model",
        model,
        "-c",
        f"model_reasoning_effort={json.dumps(reasoning_effort)}",
        "--cd",
        str(_repo_root()),
        "-",
    ]
    for add_dir in add_dirs:
        command.extend(["--add-dir", str(add_dir)])
    try:
        process = subprocess.Popen(
            command,
            cwd=str(_repo_root()),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            # Isolate Codex in its own process group so reconnect/orphan descendants
            # can be terminated if they keep pipes open after the parent exits.
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Codex CLI not found for live semantic generation. Install `codex` and retry."
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"Failed to launch Codex CLI: {exc}") from exc

    if process.stdin is None:
        raise RuntimeError("Codex subprocess stdin was not available.")
    process.stdin.write(prompt)
    process.stdin.close()

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stdout_thread = threading.Thread(
        target=_stream_process_output,
        args=(process.stdout, stdout_chunks, sys.stdout),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_stream_process_output,
        args=(process.stderr, stderr_chunks, sys.stderr),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    try:
        if backend_config.timeout_secs is None:
            return_code = process.wait()
        else:
            return_code = process.wait(timeout=backend_config.timeout_secs)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process.pid)
        process.wait()
        _close_stream(process.stdout)
        _close_stream(process.stderr)
        _join_stream_threads(
            stdout_thread=stdout_thread,
            stderr_thread=stderr_thread,
        )
        raise RuntimeError(
            "Codex semantic generation timed out after "
            f"{backend_config.timeout_secs} seconds for `{output_json_path}`."
        ) from exc

    _join_stream_threads(
        stdout_thread=stdout_thread,
        stderr_thread=stderr_thread,
    )

    if return_code != 0:
        raise RuntimeError(
            "Codex semantic generation failed with non-zero exit status "
            f"{return_code}: {_tail(''.join(stderr_chunks))}"
        )

    if not output_json_path.is_file():
        raise RuntimeError(
            "Codex semantic generation completed but did not write output_json_path "
            f"`{output_json_path}`."
        )

    raw_output = output_json_path.read_text()
    _require_json_object(raw_output=raw_output, output_json_path=output_json_path)
    return raw_output


def _stream_process_output(
    stream: TextIO | None,
    sink: list[str],
    target: TextIO,
) -> None:
    if stream is None:
        return
    for line in iter(stream.readline, ""):
        sink.append(line)
        print(line, file=target, end="", flush=True)
    stream.close()


def _join_stream_threads(
    *,
    stdout_thread: threading.Thread,
    stderr_thread: threading.Thread,
) -> None:
    stdout_thread.join()
    stderr_thread.join()


def _terminate_process_group(process_pid: int) -> None:
    try:
        os.killpg(process_pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        return


def _close_stream(stream: TextIO | None) -> None:
    if stream is None:
        return
    try:
        stream.close()
    except OSError:
        return


def _require_json_object(*, raw_output: str, output_json_path: Path) -> None:
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Codex wrote invalid JSON to output_json_path "
            f"`{output_json_path}`: {exc.msg}."
        ) from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Codex semantic output must be a JSON object at output_json_path "
            f"`{output_json_path}`."
        )


def _tail(text: str, *, max_chars: int = _MAX_ERROR_TAIL_CHARS) -> str:
    normalized = text.strip()
    if len(normalized) <= max_chars:
        return normalized
    return "..." + normalized[-max_chars:]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _collect_codex_add_dirs(*, request: SemanticLlmRequest) -> list[Path]:
    repo_root = _repo_root()
    candidates: list[Path] = [Path(request.output_json_path).resolve().parent]
    for raw_context_path in request.context_paths:
        context_path = Path(raw_context_path).resolve()
        if context_path.is_file():
            candidates.append(context_path.parent)
        else:
            candidates.append(context_path)

    add_dirs: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            candidate.relative_to(repo_root)
            continue
        except ValueError:
            add_dirs.append(candidate)
    return add_dirs
