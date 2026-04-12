#!/usr/bin/env python3
"""Bootstrap stub for comments entrypoint."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.core.runtime_flags import (
    add_runtime_flag_arguments,
    runtime_flags_summary_dict,
    snapshot_runtime_flags,
    validate_runtime_flag_arguments,
)
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--count", required=True, type=int)
    parser.add_argument("--comment-user", action="append", default=[])
    parser.add_argument("--comment-page", action="append", default=[])
    parser.add_argument("--comment-seed")
    parser.add_argument("--comment-evidence-mode")
    parser.add_argument("--verbose", action="store_true")
    add_runtime_flag_arguments(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        validate_runtime_flag_arguments(args)
        runtime_flags = snapshot_runtime_flags(args)
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=runtime_flags.mock_llm,
            env=os.environ,
        )
        registry_path = resolve_registry_path(args.registry_path)
        resolve_space_root(registry_path, args.space_name)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(
        "scripts/create_comments.py scaffold ready "
        f"(execution_mode={runtime_policy.execution_mode}, "
        f"runtime_flags={runtime_flags_summary_dict(runtime_flags)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
