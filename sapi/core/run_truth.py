"""Run-truth reconciliation advancement semantics."""

from __future__ import annotations

import json
from pathlib import Path
import secrets
import shutil

from sapi.contracts.run_envelopes import RunEnvelopeBase, RunStatus
from sapi.core.transactions import ArtifactTransaction


_ADVANCING_STATUSES: frozenset[RunStatus] = frozenset({"success", "success_with_warnings"})
_RECONCILIATION_SCHEMA_VERSION = "run_truth_reconciliation_v1"


def status_advances_reconciliation(status: RunStatus) -> bool:
    return status in _ADVANCING_STATUSES


def reconciliation_state_path(*, space_root: Path) -> Path:
    return space_root / "outputs" / "run_truth" / "reconciliation_state.json"


def advance_reconciliation_state(
    *,
    space_root: Path,
    base: RunEnvelopeBase,
    transaction: ArtifactTransaction,
) -> bool:
    """Advance reconciliation state for eligible terminal run statuses."""
    if not status_advances_reconciliation(base.status):
        return False

    state_path = reconciliation_state_path(space_root=space_root)
    state_payload = _load_reconciliation_payload(state_path=state_path)
    flow_states = state_payload["flow_states"]
    assert isinstance(flow_states, dict)

    flow_state = flow_states.get(base.flow_key)
    if not isinstance(flow_state, dict):
        flow_state = {
            "last_advanced_run_id": None,
            "last_advanced_status": None,
            "last_advanced_completed_at": None,
            "consecutive_advanced_runs": 0,
            "advanced_run_ids": [],
        }
        flow_states[base.flow_key] = flow_state

    current_count = flow_state.get("consecutive_advanced_runs", 0)
    if not isinstance(current_count, int) or current_count < 0:
        current_count = 0
    flow_state["consecutive_advanced_runs"] = current_count + 1
    flow_state["last_advanced_run_id"] = base.run_id
    flow_state["last_advanced_status"] = base.status
    flow_state["last_advanced_completed_at"] = base.completed_at

    advanced_run_ids = flow_state.get("advanced_run_ids")
    if not isinstance(advanced_run_ids, list):
        advanced_run_ids = []
    normalized_advanced_ids: list[str] = [
        str(item).strip() for item in advanced_run_ids if isinstance(item, str) and str(item).strip()
    ]
    if base.run_id in normalized_advanced_ids:
        normalized_advanced_ids = [item for item in normalized_advanced_ids if item != base.run_id]
    normalized_advanced_ids.append(base.run_id)
    flow_state["advanced_run_ids"] = normalized_advanced_ids[-20:]

    _write_reconciliation_payload(
        state_path=state_path,
        payload=state_payload,
        transaction=transaction,
    )
    return True


def _load_reconciliation_payload(*, state_path: Path) -> dict[str, object]:
    if not state_path.is_file():
        return {
            "schema_version": _RECONCILIATION_SCHEMA_VERSION,
            "flow_states": {},
        }

    parsed = json.loads(state_path.read_text())
    if not isinstance(parsed, dict):
        raise ValueError(f"Run-truth reconciliation state must be a JSON object: {state_path}")
    if str(parsed.get("schema_version") or "") != _RECONCILIATION_SCHEMA_VERSION:
        raise ValueError(
            "Run-truth reconciliation schema mismatch; "
            f"expected {_RECONCILIATION_SCHEMA_VERSION}."
        )
    flow_states = parsed.get("flow_states")
    if not isinstance(flow_states, dict):
        raise ValueError("Run-truth reconciliation flow_states must be a JSON object.")
    return {
        "schema_version": _RECONCILIATION_SCHEMA_VERSION,
        "flow_states": flow_states,
    }


def _write_reconciliation_payload(
    *,
    state_path: Path,
    payload: dict[str, object],
    transaction: ArtifactTransaction,
) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if state_path.exists():
        backup_path = state_path.with_name(f".{state_path.name}.bak.{secrets.token_hex(8)}")
        shutil.copy2(state_path, backup_path)
        transaction.mark_replace(state_path, backup_path)
    else:
        transaction.mark_create(state_path)
    state_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
