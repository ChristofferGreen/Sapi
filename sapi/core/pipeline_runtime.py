"""Shared runtime helpers for semantic pipeline entrypoints."""

from __future__ import annotations

import json
from pathlib import Path
import secrets
import shutil
from typing import Literal

from sapi.contracts.run_envelopes import PipelineFlowKey, RunEnvelopeBase, RunStatus
from sapi.core.transactions import ArtifactTransaction


def record_semantic_invocation(
    *,
    flow_key: str,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
) -> None:
    if flow_key not in semantic_flows:
        semantic_flows.append(flow_key)
    semantic_flow_invocation_counts[flow_key] = semantic_flow_invocation_counts.get(flow_key, 0) + 1


def add_llm_attempts(*, llm_attempt_count: int, attempt_count: int) -> int:
    if attempt_count <= 0:
        raise ValueError("attempt_count must be positive.")
    if llm_attempt_count < 0:
        raise ValueError("llm_attempt_count must be >= 0.")
    return llm_attempt_count + attempt_count


def build_run_envelope_base(
    *,
    run_id: str,
    flow_key: PipelineFlowKey,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
    status: RunStatus | Literal["success", "success_with_warnings", "failed", "aborted", "pending"],
    started_at: str,
    completed_at: str,
    execution_mode: str,
    llm_backend: str,
    llm_model: str,
    reasoning_effort: str,
    llm_attempt_count: int,
    toolchain_versions: dict[str, str],
) -> RunEnvelopeBase:
    model_fingerprint = "mock_semantic_fixture" if execution_mode == "mock_llm_test" else llm_model
    provider_fingerprint = "mock" if execution_mode == "mock_llm_test" else llm_backend
    return RunEnvelopeBase(
        run_id=run_id,
        flow_key=flow_key,
        semantic_flows=list(semantic_flows),  # type: ignore[arg-type]
        semantic_flow_invocation_counts=dict(semantic_flow_invocation_counts),  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        started_at=started_at,
        completed_at=completed_at,
        model_fingerprint=model_fingerprint,
        provider_fingerprint=provider_fingerprint,
        reasoning_effort=reasoning_effort,
        execution_mode=execution_mode,
        llm_attempt_count=llm_attempt_count,
        lint_error_count=0,
        lint_warning_count=0,
        lint_info_count=0,
        toolchain_versions=toolchain_versions,
    )


def track_path_for_write(path: Path, *, transaction: ArtifactTransaction) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup_path = path.with_name(f".{path.name}.bak.{secrets.token_hex(8)}")
        shutil.copy2(path, backup_path)
        transaction.mark_replace(path, backup_path)
        return
    transaction.mark_create(path)


def write_json_with_transaction(
    path: Path,
    payload: dict[str, object],
    *,
    transaction: ArtifactTransaction,
) -> None:
    track_path_for_write(path, transaction=transaction)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
