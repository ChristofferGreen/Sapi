#!/usr/bin/env python3
"""Bootstrap stub for lint/validate entrypoint."""

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
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--workflow", action="append", default=[])
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registry_path = resolve_registry_path(args.registry_path)
    resolve_space_root(registry_path, args.space_name)
    print("scripts/lint.py scaffold ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
