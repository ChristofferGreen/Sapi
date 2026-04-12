#!/usr/bin/env python3
"""Deterministic site-build entrypoint scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import (
    load_registry,
    resolve_registry_path,
    resolve_site_path_from_registry,
    resolve_space_root,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--workflow-key", default="build_site", choices=["build_site"])
    parser.add_argument("space_name", nargs="?")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registry_path = resolve_registry_path(args.registry_path)
    site_path = resolve_site_path_from_registry(registry_path)
    if args.space_name:
        resolve_space_root(registry_path, args.space_name)
        space_targets = [args.space_name]
    else:
        registry = load_registry(registry_path)
        space_targets = sorted(space.space_name for space in registry["spaces"])

    manifest = {
        "workflow_key": args.workflow_key,
        "site_path": str(site_path),
        "registry_path": str(registry_path),
        "space_targets": space_targets,
        "semantic_flows_executed": [],
        "build_mode": "deterministic",
    }
    manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(
        "scripts/build_site.py scaffold ready "
        f"(workflow_key={args.workflow_key} registry_path={registry_path} manifest_path={manifest_path})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
