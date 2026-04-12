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

from sapi.build.projection import ProjectionContractError
from sapi.build.site_builder import build_space_site, refresh_site_new_index
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
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("space_name", nargs="?")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        registry_path = resolve_registry_path(args.registry_path)
        site_path = resolve_site_path_from_registry(registry_path)
        toolchain = _validate_frontend_toolchain_reproducibility(_REPO_ROOT)
        if args.space_name:
            resolve_space_root(registry_path, args.space_name)
            space_targets = [args.space_name]
        else:
            registry = load_registry(registry_path)
            space_targets = sorted(space.space_name for space in registry["spaces"])

        builds = []
        for space_name in space_targets:
            space_root = resolve_space_root(registry_path, space_name)
            build = build_space_site(space_root, incremental=args.incremental)
            builds.append(
                {
                    "space_name": build.space_name,
                    "output_root": str(build.output_root),
                    "generated_files": [str(path) for path in build.generated_files],
                    "content_hashes": build.content_hashes,
                }
            )
        site_new_index_path = refresh_site_new_index(site_path, incremental=args.incremental)
    except (ProjectionContractError, ValueError, KeyError, FileNotFoundError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1

    manifest = {
        "workflow_key": args.workflow_key,
        "site_path": str(site_path),
        "registry_path": str(registry_path),
        "space_targets": space_targets,
        "semantic_flows_executed": [],
        "build_mode": "incremental" if args.incremental else "deterministic",
        "space_builds": builds,
        "site_new_index_path": str(site_new_index_path),
        "toolchain_versions": {
            "node": toolchain["node"],
            "package_manager": toolchain["package_manager"],
            "tailwind_cli": toolchain["tailwind_cli"],
        },
        "frozen_install_mode": toolchain["frozen_install_mode"],
    }
    manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(
        "scripts/build_site.py deterministic build complete "
        f"(workflow_key={args.workflow_key} registry_path={registry_path} manifest_path={manifest_path})"
    )
    return 0


def _validate_frontend_toolchain_reproducibility(repo_root: Path) -> dict[str, str]:
    package_json_path = repo_root / "package.json"
    if not package_json_path.is_file():
        raise ValueError("Missing required package.json for frontend toolchain reproducibility.")
    package_json = json.loads(package_json_path.read_text())
    if not isinstance(package_json, dict):
        raise ValueError("package.json must decode to a JSON object.")

    package_manager_decl = package_json.get("packageManager")
    if not isinstance(package_manager_decl, str) or not package_manager_decl.strip():
        raise ValueError("package.json must declare packageManager for reproducible builds.")
    package_manager_decl = package_manager_decl.strip()

    package_manager_family = package_manager_decl.split("@", 1)[0]
    lockfile_by_pm = {
        "npm": "package-lock.json",
        "pnpm": "pnpm-lock.yaml",
        "yarn": "yarn.lock",
    }
    frozen_install_by_pm = {
        "npm": "npm ci",
        "pnpm": "pnpm install --frozen-lockfile",
        "yarn": "yarn install --immutable",
    }
    if package_manager_family not in lockfile_by_pm:
        raise ValueError(
            "packageManager must use npm, pnpm, or yarn family for reproducible builds."
        )

    lockfiles = [name for name in lockfile_by_pm.values() if (repo_root / name).is_file()]
    if len(lockfiles) != 1:
        raise ValueError(
            "Repository must contain exactly one lockfile (package-lock.json, pnpm-lock.yaml, or yarn.lock)."
        )
    expected_lockfile = lockfile_by_pm[package_manager_family]
    if lockfiles[0] != expected_lockfile:
        raise ValueError(
            f"Lockfile `{lockfiles[0]}` does not match declared packageManager family `{package_manager_family}`."
        )

    if expected_lockfile == "package-lock.json":
        lock_payload = json.loads((repo_root / expected_lockfile).read_text())
        if lock_payload.get("name") != package_json.get("name"):
            raise ValueError(
                "package-lock.json is out-of-sync with package.json name."
            )
        if lock_payload.get("version") != package_json.get("version"):
            raise ValueError(
                "package-lock.json is out-of-sync with package.json version."
            )

    node_pin_value = _resolve_node_pin(repo_root)

    package_dependencies = package_json.get("dependencies")
    package_dev_dependencies = package_json.get("devDependencies")
    tailwind_cli = "not_declared"
    if isinstance(package_dependencies, dict) and isinstance(package_dependencies.get("tailwindcss"), str):
        tailwind_cli = package_dependencies["tailwindcss"]
    elif isinstance(package_dev_dependencies, dict) and isinstance(package_dev_dependencies.get("tailwindcss"), str):
        tailwind_cli = package_dev_dependencies["tailwindcss"]

    return {
        "node": node_pin_value,
        "package_manager": package_manager_decl,
        "tailwind_cli": tailwind_cli,
        "frozen_install_mode": frozen_install_by_pm[package_manager_family],
    }


def _resolve_node_pin(repo_root: Path) -> str:
    nvmrc_path = repo_root / ".nvmrc"
    node_version_path = repo_root / ".node-version"
    for pin_path in (nvmrc_path, node_version_path):
        if pin_path.is_file():
            value = pin_path.read_text().strip()
            if value:
                return value
    raise ValueError("Missing required Node runtime pin (.nvmrc or .node-version).")


if __name__ == "__main__":
    raise SystemExit(main())
