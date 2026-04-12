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
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    runtime_policy = evaluate_semantic_runtime_policy(
        mock_llm=args.mock_llm,
        env=os.environ,
    )
    registry_path = resolve_registry_path(args.registry_path)
    resolve_space_root(registry_path, args.space_name)
    print(f"scripts/create_comments.py scaffold ready (execution_mode={runtime_policy.execution_mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
