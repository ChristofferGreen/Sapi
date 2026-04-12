"""Shared semantic executor with strict schema validation and repair retries."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import secrets
from typing import Any, Mapping, Protocol

from sapi.contracts.schemas import load_json_schema, validate_json_instance
from sapi.contracts.semantic_specs import (
    resolve_semantic_invocation_spec,
)
from sapi.llm.client import LlmClient, SemanticLlmRequest, SemanticRepairContext


DEFAULT_MAX_REPAIR_LOOPS = 3
DEFAULT_MAX_ATTEMPTS = 1 + DEFAULT_MAX_REPAIR_LOOPS
_CONTEXT_POINTER_PREFIXES: tuple[str, ...] = ("file://", "dir://", "missing://", "unsupported://")


@dataclass(frozen=True)
class SemanticSpec:
    """Runtime semantic flow invocation contract."""

    flow_key: str
    version: str
    schema_path: Path
    output_json_path: Path
    context_paths: list[Path]
    spec_path: Path | None = None


class TraceContext(Protocol):
    """Optional tracing sink for semantic attempts."""

    def record_semantic_attempt(
        self,
        *,
        flow_key: str,
        attempt: int,
        max_attempts: int,
        valid: bool,
        validation_errors: list[dict[str, Any]] | None,
    ) -> None: ...


class SemanticFlowError(RuntimeError):
    """Terminal semantic generation failure after retry budget exhaustion."""

    def __init__(
        self,
        *,
        flow_key: str,
        attempt_count: int,
        max_attempts: int,
        last_validation_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.flow_key = flow_key
        self.attempt_count = attempt_count
        self.max_attempts = max_attempts
        self.last_validation_errors = last_validation_errors or []
        super().__init__(
            f"Semantic flow `{flow_key}` failed after {attempt_count}/{max_attempts} attempts."
        )


def build_semantic_spec_from_contract(
    flow_key: str,
    *,
    repo_root: Path,
    path_tokens: Mapping[str, str | Path],
) -> SemanticSpec:
    """Build a semantic invocation spec from authoritative generation-spec contracts."""
    resolved = resolve_semantic_invocation_spec(
        flow_key,
        repo_root=repo_root,
        path_tokens=path_tokens,
    )
    return SemanticSpec(
        flow_key=resolved.flow_key,
        version=resolved.version,
        schema_path=resolved.schema_path,
        output_json_path=resolved.output_json_path,
        context_paths=resolved.context_paths,
        spec_path=resolved.spec_path,
    )


def run_semantic_flow(
    *,
    spec: SemanticSpec,
    llm_client: LlmClient,
    max_repair_loops: int = DEFAULT_MAX_REPAIR_LOOPS,
    trace_ctx: TraceContext | None = None,
) -> tuple[dict[str, Any], int]:
    """Run one semantic flow with strict schema validation and repair retries."""
    max_attempts = max_attempts_from_repair_loops(max_repair_loops)
    schema = load_json_schema(spec.schema_path)
    spec_text = spec.spec_path.read_text() if spec.spec_path is not None else ""
    context_by_path = _gather_context_by_path(spec.context_paths)
    ensure_context_pointer_payload(context_by_path)

    repair_context: SemanticRepairContext | None = None
    for attempt in range(1, max_attempts + 1):
        request = SemanticLlmRequest(
            flow_key=spec.flow_key,
            version=spec.version,
            schema_path=str(spec.schema_path.resolve()),
            output_json_path=str(spec.output_json_path.resolve()),
            context_paths=[str(path.resolve()) for path in spec.context_paths],
            spec_text=spec_text,
            schema=schema,
            context_by_path=context_by_path,
            repair_context=repair_context,
        )
        raw_output = llm_client.generate_semantic_json(request)
        parsed_output, validation_errors = _validate_attempt_output(raw_output=raw_output, schema=schema)

        _record_attempt(
            trace_ctx=trace_ctx,
            flow_key=spec.flow_key,
            attempt=attempt,
            max_attempts=max_attempts,
            valid=not validation_errors,
            validation_errors=validation_errors or None,
        )

        if not validation_errors:
            _atomic_write_json(spec.output_json_path, parsed_output)
            return parsed_output, attempt

        if attempt >= max_attempts:
            raise SemanticFlowError(
                flow_key=spec.flow_key,
                attempt_count=attempt,
                max_attempts=max_attempts,
                last_validation_errors=validation_errors,
            )

        repair_context = SemanticRepairContext(
            previous_invalid_json=raw_output,
            validation_errors=validation_errors,
            schema=schema,
            require_complete_replacement_json=True,
        )

    raise AssertionError("Unreachable attempt loop termination.")


def max_attempts_from_repair_loops(max_repair_loops: int) -> int:
    """Translate repair-loop budget to total attempt budget."""
    if max_repair_loops < 0:
        raise ValueError("max_repair_loops must be >= 0")
    return 1 + max_repair_loops


def _gather_context_by_path(context_paths: list[Path]) -> dict[str, str]:
    """Collect filesystem pointers for declared evidence paths."""
    snapshots: dict[str, str] = {}
    for path in context_paths:
        resolved = path.resolve()
        if not resolved.exists():
            snapshots[str(resolved)] = f"missing://{resolved}"
        elif resolved.is_file():
            snapshots[str(resolved)] = f"file://{resolved}"
        elif resolved.is_dir():
            snapshots[str(resolved)] = f"dir://{resolved}"
        else:
            snapshots[str(resolved)] = f"unsupported://{resolved}"
    return snapshots


def ensure_context_pointer_payload(context_by_path: Mapping[str, str]) -> None:
    """Fail fast if prompt context payload drifts from filesystem-pointer policy."""
    for raw_path, pointer in context_by_path.items():
        resolved_path = Path(raw_path)
        if not resolved_path.is_absolute():
            raise ValueError(f"context_by_path key must be an absolute path: {raw_path}")
        if not any(pointer.startswith(prefix) for prefix in _CONTEXT_POINTER_PREFIXES):
            raise ValueError(
                "Prompt context payload must use filesystem pointer prefixes "
                "(file://, dir://, missing://, unsupported://)."
            )


def _validate_attempt_output(*, raw_output: str, schema: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        return {}, [
            {
                "path": "/",
                "message": f"Invalid JSON: {exc.msg}",
                "validator": "json_parse",
                "validator_value": None,
            }
        ]

    if not isinstance(parsed, dict):
        return {}, [
            {
                "path": "/",
                "message": "Semantic output must be a JSON object.",
                "validator": "type",
                "validator_value": "object",
            }
        ]

    issues = validate_json_instance(parsed, schema)
    return parsed, [issue.to_dict() for issue in issues]


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp.{secrets.token_hex(8)}")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp_path.replace(path)


def _record_attempt(
    *,
    trace_ctx: TraceContext | None,
    flow_key: str,
    attempt: int,
    max_attempts: int,
    valid: bool,
    validation_errors: list[dict[str, Any]] | None,
) -> None:
    if trace_ctx is None:
        return
    trace_ctx.record_semantic_attempt(
        flow_key=flow_key,
        attempt=attempt,
        max_attempts=max_attempts,
        valid=valid,
        validation_errors=validation_errors,
    )
