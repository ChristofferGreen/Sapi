#!/usr/bin/env python3
"""Bootstrap stub for profiles entrypoint."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.profiles.persona_catalog import load_seeded_persona_catalog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--persona-id", action="append", default=[])
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    runtime_policy = evaluate_semantic_runtime_policy(
        mock_llm=args.mock_llm,
        env=os.environ,
    )
    try:
        registry_path = resolve_registry_path(args.registry_path)
        resolve_space_root(registry_path, args.space_name)
        persona_catalog = load_seeded_persona_catalog(repo_root=_REPO_ROOT)
        _validate_requested_persona_ids(args.persona_id, persona_catalog)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(
        "scripts/generate_profiles.py scaffold ready "
        f"(execution_mode={runtime_policy.execution_mode}, personas_loaded={len(persona_catalog)})"
    )
    return 0


def _validate_requested_persona_ids(
    requested_persona_ids: list[str],
    persona_catalog: list[dict[str, object]],
) -> None:
    if not requested_persona_ids:
        return
    known_persona_ids = {str(row["persona_id"]) for row in persona_catalog}
    unknown = sorted(
        {
            persona_id
            for persona_id in requested_persona_ids
            if persona_id not in known_persona_ids
        }
    )
    if unknown:
        raise ValueError(
            "Unknown persona_id values requested via --persona-id: " + ", ".join(unknown)
        )


if __name__ == "__main__":
    raise SystemExit(main())
