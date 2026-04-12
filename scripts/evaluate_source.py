#!/usr/bin/env python3
"""Bootstrap stub for source evaluation harness entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("source_path_or_url")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--out")
    parser.add_argument("--comments", type=int)
    parser.add_argument("--comment-user", action="append", default=[])
    parser.add_argument("--comment-page", action="append", default=[])
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registry_path = resolve_registry_path(args.registry_path)
    resolve_space_root(registry_path, args.space_name)
    print("scripts/evaluate_source.py scaffold ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
