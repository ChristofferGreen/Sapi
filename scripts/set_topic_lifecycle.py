#!/usr/bin/env python3
"""Manual lifecycle transition entrypoint for canonical topic records."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.build.topic_lifecycle import (
    normalize_lifecycle_state_for_write,
    resolve_topic_lifecycle,
    validate_manual_lifecycle_transition,
)
from sapi.contracts.ids import format_timestamp_rfc3339_utc
from sapi.core.registry import resolve_registry_path, resolve_space_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--topic-id", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--actor", default="manual_operator")
    parser.add_argument("--reason", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        registry_path = resolve_registry_path(args.registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        topic_id = args.topic_id.strip()
        if not topic_id:
            raise ValueError("--topic-id must be a non-empty string.")
        target_state = normalize_lifecycle_state_for_write(args.state)
        actor = _normalize_actor(args.actor)
        reason = args.reason.strip()

        topic_path = space_root / "topics" / f"{topic_id}.json"
        topic = _load_topic(topic_path)
        payload_topic_id = topic.get("topic_id")
        if payload_topic_id != topic_id:
            raise ValueError(
                f"{topic_path}: topic_id mismatch; expected `{topic_id}`, found `{payload_topic_id}`."
            )

        lifecycle_resolution = resolve_topic_lifecycle(topic=topic, topic_id=topic_id)
        current_state = lifecycle_resolution.effective_state
        validate_manual_lifecycle_transition(current_state=current_state, target_state=target_state)

        changed = _apply_transition(
            topic=topic,
            topic_id=topic_id,
            current_state=current_state,
            target_state=target_state,
            actor=actor,
            reason=reason,
        )
        if not changed:
            print(
                "scripts/set_topic_lifecycle.py no-op "
                f"(topic_id={topic_id}, lifecycle_state={target_state}, topic_path={topic_path})"
            )
            return 0

        topic_path.write_text(json.dumps(topic, indent=2, sort_keys=True) + "\n")
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        "scripts/set_topic_lifecycle.py lifecycle updated "
        f"(topic_id={topic_id}, from_state={current_state}, to_state={target_state}, "
        f"topic_path={topic_path})"
    )
    return 0


def _normalize_actor(raw_actor: str) -> str:
    actor = raw_actor.strip()
    if not actor:
        raise ValueError("--actor must be a non-empty string.")
    return actor


def _load_topic(topic_path: Path) -> dict[str, object]:
    if not topic_path.is_file():
        raise FileNotFoundError(f"Topic file not found: {topic_path}")
    payload = json.loads(topic_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{topic_path}: topic payload must be a JSON object.")
    return payload


def _apply_transition(
    *,
    topic: dict[str, object],
    topic_id: str,
    current_state: str,
    target_state: str,
    actor: str,
    reason: str,
) -> bool:
    if current_state == target_state:
        return False

    now = format_timestamp_rfc3339_utc(datetime.now(UTC))
    topic["lifecycle_state"] = target_state

    if target_state == "final":
        topic["finalized_by"] = actor
        topic["finalized_at"] = now

    audit_row = {
        "timestamp": now,
        "actor": actor,
        "topic_id": topic_id,
        "from_state": current_state,
        "to_state": target_state,
        "action": "set_topic_lifecycle",
    }
    if reason:
        audit_row["reason"] = reason

    audit_rows = topic.get("lifecycle_audit")
    if audit_rows is None:
        audit_list: list[dict[str, object]] = []
    elif isinstance(audit_rows, list):
        audit_list = list(audit_rows)
    else:
        raise ValueError(f"{topic_id}: lifecycle_audit must be an array when present.")
    audit_list.append(audit_row)
    topic["lifecycle_audit"] = audit_list
    return True


if __name__ == "__main__":
    raise SystemExit(main())
