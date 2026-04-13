from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from pathlib import Path
from typing import Sequence

from sapi.llm.client import SemanticLlmRequest


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class IsolatedSiteSpaceFixture:
    fixture_root: Path
    site_path: Path
    registry_path: Path
    space_name: str
    space_root: Path


@dataclass
class DeterministicMockLlmFixture:
    mode: str
    valid_output: str
    invalid_output: str
    requests: list[SemanticLlmRequest]
    call_count: int = 0

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        self.requests.append(request)
        self.call_count += 1
        if self.mode == "valid":
            return self.valid_output
        if self.mode == "invalid_then_repair":
            return self.invalid_output if self.call_count == 1 else self.valid_output
        if self.mode == "repair_exhausted":
            return self.invalid_output
        raise AssertionError(f"Unsupported deterministic mock LLM mode: {self.mode}")


def create_deterministic_mock_llm_fixture(
    *,
    mode: str,
    valid_payload: dict[str, object] | None = None,
    invalid_output: str = "{}",
) -> DeterministicMockLlmFixture:
    if mode not in {"valid", "invalid_then_repair", "repair_exhausted"}:
        raise ValueError(
            "Unsupported deterministic mock LLM mode. "
            "Expected one of: valid, invalid_then_repair, repair_exhausted."
        )

    payload = {"value": "ok"} if valid_payload is None else valid_payload
    return DeterministicMockLlmFixture(
        mode=mode,
        valid_output=json.dumps(payload, sort_keys=True),
        invalid_output=invalid_output,
        requests=[],
    )


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


def bootstrap_site_and_space(
    tmp_root: Path,
    space_name: str = "alpha",
    *,
    site_dir_name: str = "site-a",
    site_name: str = "My Site",
) -> Path:
    site_path = tmp_root / site_dir_name
    run_command(
        ["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), site_name],
        check=True,
    )
    run_command(
        ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name],
        check=True,
    )
    return site_path


def create_isolated_site_space_fixture(
    tmp_root: Path,
    *,
    fixture_name: str,
    space_name: str = "alpha",
    site_name: str = "My Site",
) -> IsolatedSiteSpaceFixture:
    fixture_root = tmp_root / fixture_name
    fixture_root.mkdir(parents=True, exist_ok=False)
    site_path = bootstrap_site_and_space(
        fixture_root,
        space_name=space_name,
        site_dir_name="site-a",
        site_name=site_name,
    )
    registry_path = site_path / "spaces.toml"
    if not registry_path.is_file():
        raise AssertionError(f"Expected isolated registry file at {registry_path}")
    space_root = site_path / "spaces" / space_name
    if not space_root.is_dir():
        raise AssertionError(f"Expected isolated space root at {space_root}")
    return IsolatedSiteSpaceFixture(
        fixture_root=fixture_root,
        site_path=site_path,
        registry_path=registry_path,
        space_name=space_name,
        space_root=space_root,
    )


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
