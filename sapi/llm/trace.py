"""LLM semantic-attempt trace artifact writer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, TextIO

from sapi.llm.client import SemanticLlmRequest

_FLOW_KEY_SAFE_CHARS_RE = re.compile(r"[^a-z0-9_-]+")


@dataclass(frozen=True)
class _AttemptTraceState:
    trace_dir: Path
    started_at: str


class SiteLlmTraceContext:
    """Persist per-attempt LLM traces under the canonical site outputs path."""

    def __init__(
        self,
        *,
        site_path: Path,
        verbose: bool,
        stdout: TextIO = sys.stdout,
        stderr: TextIO = sys.stderr,
    ) -> None:
        self._site_path = site_path.resolve()
        self._trace_root = self._site_path / "outputs" / "llm_traces"
        self._trace_root.mkdir(parents=True, exist_ok=True)
        self._verbose = verbose
        self._stdout = stdout
        self._stderr = stderr
        self._attempt_state: dict[tuple[str, int], _AttemptTraceState] = {}

    @property
    def trace_root(self) -> Path:
        return self._trace_root

    def begin_semantic_attempt(
        self,
        *,
        flow_key: str,
        attempt: int,
        max_attempts: int,
        request: SemanticLlmRequest,
    ) -> None:
        attempt_dir = self._allocate_attempt_dir(flow_key=flow_key, attempt=attempt)
        started_at = _now_rfc3339_utc()
        self._attempt_state[(flow_key, attempt)] = _AttemptTraceState(
            trace_dir=attempt_dir,
            started_at=started_at,
        )

        prompt_snapshot = _render_prompt_snapshot(request=request)
        _write_text(attempt_dir / "semantic.prompt.txt", prompt_snapshot)
        _write_text(
            attempt_dir / "semantic.call.txt",
            _render_call_transcript(prompt_snapshot=prompt_snapshot, raw_output=None),
        )
        _write_json(
            attempt_dir / "semantic.context.json",
            _context_snapshot_payload(request=request),
        )
        # Runtime currently has one-shot mock/live responses; keep stream artifacts for contract parity.
        _write_text(attempt_dir / "semantic.codex.stdout.jsonl", "")
        _write_text(attempt_dir / "semantic.codex.stderr.txt", "")

        if self._verbose:
            print(
                f"LLM trace dir ({flow_key} attempt {attempt}/{max_attempts}): {attempt_dir}",
                file=self._stdout,
                flush=True,
            )
            print(
                f"Final LLM prompt ({flow_key} attempt {attempt}/{max_attempts}):",
                file=self._stdout,
                flush=True,
            )
            print(prompt_snapshot, file=self._stdout, flush=True)

    def record_semantic_attempt(
        self,
        *,
        flow_key: str,
        attempt: int,
        max_attempts: int,
        request: SemanticLlmRequest,
        raw_output: str,
        valid: bool,
        validation_errors: list[dict[str, Any]] | None,
    ) -> None:
        state = self._attempt_state.get((flow_key, attempt))
        if state is None:
            self.begin_semantic_attempt(
                flow_key=flow_key,
                attempt=attempt,
                max_attempts=max_attempts,
                request=request,
            )
            state = self._attempt_state[(flow_key, attempt)]
        attempt_dir = state.trace_dir

        _write_text(attempt_dir / "semantic.response.txt", _ensure_trailing_newline(raw_output))
        prompt_snapshot = _render_prompt_snapshot(request=request)
        _write_text(
            attempt_dir / "semantic.call.txt",
            _render_call_transcript(prompt_snapshot=prompt_snapshot, raw_output=raw_output),
        )
        maybe_json = _try_parse_json(raw_output)
        if maybe_json is not None:
            _write_json(attempt_dir / "semantic.response.json", maybe_json)

        stream_event = {
            "event": "response_complete",
            "flow_key": flow_key,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "valid": valid,
        }
        _append_jsonl(
            attempt_dir / "semantic.codex.stdout.jsonl",
            {
                **stream_event,
                "text": raw_output,
            },
        )

        stderr_text = ""
        if validation_errors:
            stderr_text = json.dumps(validation_errors, indent=2, sort_keys=True) + "\n"
            _write_text(attempt_dir / "semantic.codex.stderr.txt", stderr_text)

        meta_payload = {
            "flow_key": flow_key,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "valid": valid,
            "validation_errors": validation_errors or [],
            "schema_path": request.schema_path,
            "output_json_path": request.output_json_path,
            "context_paths": request.context_paths,
            "repair_context_present": request.repair_context is not None,
            "trace_root": str(self._trace_root),
            "trace_dir": str(attempt_dir),
            "started_at": state.started_at,
            "completed_at": _now_rfc3339_utc(),
        }
        _write_json(attempt_dir / "semantic.meta.json", meta_payload)

        if self._verbose:
            print(
                f"LLM stream output ({flow_key} attempt {attempt}/{max_attempts}):",
                file=self._stdout,
                flush=True,
            )
            print(raw_output, file=self._stdout, flush=True)
            if stderr_text:
                print(
                    f"LLM stream stderr ({flow_key} attempt {attempt}/{max_attempts}):",
                    file=self._stderr,
                    flush=True,
                )
                print(stderr_text.rstrip("\n"), file=self._stderr, flush=True)

    def _allocate_attempt_dir(self, *, flow_key: str, attempt: int) -> Path:
        flow_fragment = _sanitize_flow_key(flow_key)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        pid = str(os.getpid())
        candidate = self._trace_root / f"{timestamp}-{flow_fragment}-{pid}-{attempt}"
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate

        suffix = 1
        while True:
            retry_candidate = self._trace_root / f"{timestamp}-{flow_fragment}-{pid}-{attempt}-{suffix}"
            if not retry_candidate.exists():
                retry_candidate.mkdir(parents=True, exist_ok=False)
                return retry_candidate
            suffix += 1


def _sanitize_flow_key(flow_key: str) -> str:
    lowered = flow_key.strip().lower()
    return _FLOW_KEY_SAFE_CHARS_RE.sub("-", lowered).strip("-") or "flow"


def _render_prompt_snapshot(*, request: SemanticLlmRequest) -> str:
    sections: list[str] = [
        "=== semantic invocation ===",
        f"flow_key: {request.flow_key}",
        f"version: {request.version}",
        f"schema_path: {request.schema_path}",
        f"output_json_path: {request.output_json_path}",
        "context_paths:",
    ]
    sections.extend(f"- {path}" for path in request.context_paths)
    sections.append("")
    sections.append("=== generation spec ===")
    sections.append(request.spec_text.rstrip("\n"))
    sections.append("")
    sections.append("=== context pointers ===")
    sections.append(json.dumps(request.context_by_path, indent=2, sort_keys=True))
    if request.repair_context is not None:
        sections.append("")
        sections.append("=== repair context ===")
        sections.append(
            json.dumps(
                {
                    "previous_invalid_json": request.repair_context.previous_invalid_json,
                    "validation_errors": request.repair_context.validation_errors,
                    "require_complete_replacement_json": request.repair_context.require_complete_replacement_json,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return _ensure_trailing_newline("\n".join(sections))


def _context_snapshot_payload(*, request: SemanticLlmRequest) -> dict[str, Any]:
    return {
        "flow_key": request.flow_key,
        "version": request.version,
        "schema_path": request.schema_path,
        "output_json_path": request.output_json_path,
        "context_paths": request.context_paths,
        "context_by_path": request.context_by_path,
        "repair_context": (
            {
                "previous_invalid_json": request.repair_context.previous_invalid_json,
                "validation_errors": request.repair_context.validation_errors,
                "require_complete_replacement_json": request.repair_context.require_complete_replacement_json,
            }
            if request.repair_context is not None
            else None
        ),
    }


def _render_call_transcript(*, prompt_snapshot: str, raw_output: str | None) -> str:
    output_section = raw_output if raw_output is not None else "<pending>"
    return _ensure_trailing_newline(
        "\n".join(
            (
                "=== llm prompt ===",
                prompt_snapshot.rstrip("\n"),
                "",
                "=== llm output ===",
                output_section.rstrip("\n"),
            )
        )
    )


def _try_parse_json(raw_output: str) -> dict[str, Any] | list[Any] | None:
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, (dict, list)):
        return parsed
    return None


def _write_text(path: Path, content: str) -> None:
    path.write_text(content)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _ensure_trailing_newline(content: str) -> str:
    if content.endswith("\n"):
        return content
    return content + "\n"


def _now_rfc3339_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
