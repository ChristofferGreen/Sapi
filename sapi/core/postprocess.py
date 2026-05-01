"""Shared deterministic post-processing helpers for pipeline entrypoints."""

from __future__ import annotations

from pathlib import Path
import subprocess


def run_space_build_postprocess(
    *,
    repo_root: Path,
    registry_path: Path,
    site_path: Path,
    space_name: str,
    refresh_site_new_index: bool = True,
) -> Path:
    command = [
        "python3",
        str(repo_root / "scripts" / "build_site.py"),
        "--workflow-key",
        "build_site",
        "--registry-path",
        str(registry_path),
        space_name,
    ]
    if not refresh_site_new_index:
        command.insert(-1, "--skip-site-new-index")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Deterministic space build failed: "
            f"stdout={result.stdout.strip()} stderr={result.stderr.strip()}"
        )

    manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("Deterministic space build did not emit build manifest.")
    return manifest_path
