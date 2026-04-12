from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_command(
    cmd: Sequence[str],
    *,
    check: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(cmd),
        cwd=REPO_ROOT if cwd is None else cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def bootstrap_site_and_space(tmp_root: Path, space_name: str = "alpha") -> Path:
    site_path = tmp_root / "site-a"
    run_command(
        ["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"],
        check=True,
    )
    run_command(
        ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name],
        check=True,
    )
    return site_path


def write_source_fixture(
    tmp_root: Path,
    *,
    filename: str = "source.txt",
    content: str = "fixture source\n",
) -> Path:
    source_path = tmp_root / filename
    source_path.write_text(content)
    return source_path


def parse_run_frontmatter(run_md_path: Path) -> dict[str, object]:
    return parse_frontmatter(run_md_path.read_text())


def parse_frontmatter(markdown: str) -> dict[str, object]:
    lines = markdown.splitlines()
    if len(lines) < 3 or lines[0] != "---":
        raise AssertionError("Missing frontmatter start delimiter.")

    frontmatter: dict[str, object] = {}
    index = 1
    while index < len(lines) and lines[index] != "---":
        key, raw = lines[index].split(":", 1)
        frontmatter[key.strip()] = json.loads(raw.strip())
        index += 1

    if index >= len(lines) or lines[index] != "---":
        raise AssertionError("Missing frontmatter end delimiter.")
    return frontmatter


def run_directories(space_root: Path) -> list[Path]:
    runs_root = space_root / "runs"
    if not runs_root.is_dir():
        return []
    return sorted(path for path in runs_root.glob("run-*") if path.is_dir())


def latest_run_directory(space_root: Path) -> Path:
    run_dirs = run_directories(space_root)
    if not run_dirs:
        raise AssertionError("Expected at least one run directory.")
    return run_dirs[-1]


def assert_no_run_containers(space_root: Path) -> None:
    run_dirs = run_directories(space_root)
    if run_dirs:
        raise AssertionError(f"Expected no run directories, found: {[path.name for path in run_dirs]}")
    if list((space_root / "runs").glob("*/run.md")):
        raise AssertionError("Expected no committed run.md artifacts.")
    if list((space_root / "runs").glob("*/lint.json")):
        raise AssertionError("Expected no committed lint.json artifacts.")
