#!/usr/bin/env python3
"""Deterministic site-build entrypoint scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.build.projection import ProjectionContractError
from sapi.build.projection_index import write_projection_index
from sapi.build.site_builder import build_space_site, refresh_site_new_index
from sapi.core.registry import (
    load_registry,
    resolve_registry_path,
    resolve_site_path_from_registry,
    resolve_space_root,
)

_PUBLICATION_BLOCKING_CHECK_IDS: frozenset[str] = frozenset({"final_disputed_contradiction"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--workflow-key", default="build_site", choices=["build_site"])
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument(
        "--site-presentation-mode",
        default="public",
        choices=["public", "debug"],
    )
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
        space_roots = {
            space_name: resolve_space_root(registry_path, space_name) for space_name in space_targets
        }
        stylesheet_artifacts = _compile_site_stylesheet_assets(
            repo_root=_REPO_ROOT,
            site_path=site_path,
            space_roots=space_roots,
            package_manager_family=toolchain["package_manager_family"],
            incremental=args.incremental,
        )
        compiled_stylesheet = stylesheet_artifacts["compiled_css_bytes"]

        builds = []
        lint_issue_rows: list[dict[str, object]] = []
        for space_name in space_targets:
            space_root = space_roots[space_name]
            build = build_space_site(
                space_root,
                incremental=args.incremental,
                site_presentation_mode=args.site_presentation_mode,
                compiled_stylesheet=compiled_stylesheet,
            )
            lint_summary = build.lint_summary
            lint_issue_rows.extend(
                {
                    "space_name": space_name,
                    "check_id": issue.check_id,
                    "severity": issue.severity,
                    "message": issue.message,
                    "path": issue.path,
                    "line": issue.line,
                }
                for issue in lint_summary.issues
            )
            builds.append(
                {
                    "space_name": build.space_name,
                    "output_root": str(build.output_root),
                    "generated_files": [str(path) for path in build.generated_files],
                    "content_hashes": build.content_hashes,
                    "lint": {
                        "error_count": lint_summary.error_count,
                        "warning_count": lint_summary.warning_count,
                        "info_count": lint_summary.info_count,
                    },
                }
            )
            projection_index_path = write_projection_index(
                space_root=space_root,
                generated_files=build.generated_files,
            )
            builds[-1]["projection_index_path"] = str(projection_index_path)
        site_new_index_path = refresh_site_new_index(
            site_path,
            incremental=args.incremental,
            compiled_stylesheet=compiled_stylesheet,
        )
    except (ProjectionContractError, ValueError, KeyError, FileNotFoundError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1

    lint_error_count = sum(int(build["lint"]["error_count"]) for build in builds)
    lint_warning_count = sum(int(build["lint"]["warning_count"]) for build in builds)
    lint_info_count = sum(int(build["lint"]["info_count"]) for build in builds)

    manifest = {
        "workflow_key": args.workflow_key,
        "site_path": str(site_path),
        "registry_path": str(registry_path),
        "space_targets": space_targets,
        "semantic_flows_executed": [],
        "build_mode": "incremental" if args.incremental else "deterministic",
        "site_presentation_mode": args.site_presentation_mode,
        "space_builds": builds,
        "lint": {
            "error_count": lint_error_count,
            "warning_count": lint_warning_count,
            "info_count": lint_info_count,
            "issues": lint_issue_rows,
        },
        "site_new_index_path": str(site_new_index_path),
        "toolchain_versions": {
            "node": toolchain["node"],
            "package_manager": toolchain["package_manager"],
            "tailwind_cli": toolchain["tailwind_cli"],
        },
        "frozen_install_mode": toolchain["frozen_install_mode"],
        "stylesheet_assets": [
            {
                "path": stylesheet_artifacts["site_asset_path"],
                "sha256": stylesheet_artifacts["site_asset_sha256"],
                "bytes": stylesheet_artifacts["site_asset_bytes"],
            },
            *[
                {
                    "path": asset["path"],
                    "sha256": asset["sha256"],
                    "bytes": asset["bytes"],
                }
                for asset in stylesheet_artifacts["space_assets"]
            ],
        ],
    }
    manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    for lint_issue in lint_issue_rows:
        if lint_issue["severity"] != "error":
            continue
        issue_path = lint_issue["path"] if lint_issue["path"] else "<unknown>"
        print(
            "lint error "
            f"[{lint_issue['check_id']}] {lint_issue['space_name']}:{issue_path}: {lint_issue['message']}",
            file=sys.stderr,
        )

    blocking_lint_issues = [
        issue
        for issue in lint_issue_rows
        if issue["check_id"] in _PUBLICATION_BLOCKING_CHECK_IDS and issue["severity"] == "error"
    ]
    if blocking_lint_issues:
        print(
            "Build blocked by publication-gating lint errors: "
            + ", ".join(sorted(str(issue["check_id"]) for issue in blocking_lint_issues)),
            file=sys.stderr,
        )
        return 1

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
        "package_manager_family": package_manager_family,
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


def _compile_site_stylesheet_assets(
    *,
    repo_root: Path,
    site_path: Path,
    space_roots: dict[str, Path],
    package_manager_family: str,
    incremental: bool,
) -> dict[str, object]:
    input_css_path = repo_root / "web" / "styles" / "site.css"
    tailwind_config_path = repo_root / "web" / "styles" / "tailwind.config.cjs"
    postcss_config_path = repo_root / "web" / "styles" / "postcss.config.cjs"
    for path in (input_css_path, tailwind_config_path, postcss_config_path):
        if not path.is_file():
            raise ValueError(f"Missing required stylesheet pipeline contract file: {path}")

    _ensure_node_style_toolchain(repo_root=repo_root, package_manager_family=package_manager_family)

    with tempfile.TemporaryDirectory(prefix="sapi-style-compile-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        tailwind_out = tmp_root / "site.tailwind.css"
        compiled_out = tmp_root / "site.css"
        _run_style_command(
            [
                "npm",
                "exec",
                "--",
                "tailwindcss",
                "--config",
                str(tailwind_config_path),
                "--input",
                str(input_css_path),
                "--output",
                str(tailwind_out),
                "--minify",
            ],
            cwd=repo_root,
            failure_hint="tailwind_css_compile_failed",
        )
        _run_style_command(
            [
                "npm",
                "exec",
                "--",
                "postcss",
                str(tailwind_out),
                "--config",
                str(postcss_config_path),
                "--output",
                str(compiled_out),
            ],
            cwd=repo_root,
            failure_hint="postcss_autoprefixer_compile_failed",
        )
        compiled_css_bytes = compiled_out.read_bytes()

    if not compiled_css_bytes:
        raise ValueError("Compiled stylesheet is empty; stylesheet emission contract violated.")

    site_asset_path = site_path / "site" / "assets" / "site.css"
    _write_binary_file(site_asset_path, compiled_css_bytes, incremental=incremental)
    space_assets: list[dict[str, object]] = []
    for space_name, space_root in sorted(space_roots.items()):
        space_asset_path = space_root / "site" / "assets" / "site.css"
        _write_binary_file(space_asset_path, compiled_css_bytes, incremental=incremental)
        space_assets.append(
            {
                "space_name": space_name,
                "path": str(space_asset_path),
                "sha256": hashlib.sha256(compiled_css_bytes).hexdigest(),
                "bytes": len(compiled_css_bytes),
            }
        )

    return {
        "compiled_css_bytes": compiled_css_bytes,
        "site_asset_path": str(site_asset_path),
        "site_asset_sha256": hashlib.sha256(compiled_css_bytes).hexdigest(),
        "site_asset_bytes": len(compiled_css_bytes),
        "space_assets": space_assets,
    }


def _ensure_node_style_toolchain(*, repo_root: Path, package_manager_family: str) -> None:
    tailwind_bin = repo_root / "node_modules" / ".bin" / "tailwindcss"
    postcss_bin = repo_root / "node_modules" / ".bin" / "postcss"
    if tailwind_bin.is_file() and postcss_bin.is_file():
        return
    if package_manager_family != "npm":
        raise ValueError(
            "Only npm packageManager family is currently supported for deterministic stylesheet compilation."
        )
    result = subprocess.run(
        ["npm", "ci", "--silent"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(
            "npm ci failed while preparing deterministic stylesheet toolchain.\n"
            + result.stderr.strip()
        )
    if not tailwind_bin.is_file() or not postcss_bin.is_file():
        raise ValueError(
            "Deterministic stylesheet toolchain missing required binaries after npm ci."
        )


def _run_style_command(cmd: list[str], *, cwd: Path, failure_hint: str) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(
            f"{failure_hint}: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout.strip()}\n"
            f"stderr:\n{result.stderr.strip()}"
        )


def _write_binary_file(path: Path, content: bytes, *, incremental: bool) -> None:
    if incremental and path.is_file() and path.read_bytes() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


if __name__ == "__main__":
    raise SystemExit(main())
