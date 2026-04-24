from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    bootstrap_site_and_space,
    parse_run_frontmatter,
    run_command,
    run_directories,
)


class GenerateOverviewWrapperIntegrationTests(unittest.TestCase):
    def test_wrapper_routes_registry_and_writes_overview_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            _seed_source(space_root, source_id="source-alpha--aaaaaaaaaaaa", title="Source Alpha")

            before_runs = run_directories(space_root)
            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "generate_overview.sh"),
                    str(site_path),
                    "alpha",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            run_dir = _capture_single_new_run(space_root=space_root, before_runs=before_runs)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["flow_key"], "overview_pipeline")
            self.assertEqual(frontmatter["scope_kind"], "space")
            self.assertEqual(frontmatter["overview_id"], "space--alpha")

            overview_root = space_root / "outputs" / "space_overview" / "space--alpha"
            self.assertTrue((overview_root / "context.json").is_file())
            self.assertTrue((overview_root / "overview.json").is_file())
            self.assertTrue((overview_root / "article.md").is_file())

    def test_wrapper_supports_subspace_targets_via_space_name_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            run_command(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "beta"],
                check=True,
            )
            alpha_root = site_path / "spaces" / "alpha"
            beta_root = site_path / "spaces" / "beta"
            (alpha_root / "subspaces.json").write_text(
                json.dumps(
                    {
                        "schema_version": "space_subspaces_v1",
                        "subspaces": [
                            {
                                "space_name": "beta",
                                "space_root": "../beta",
                                "title": "Beta Subspace",
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            _seed_source(beta_root, source_id="source-beta--aaaaaaaaaaaa", title="Source Beta")

            before_runs = run_directories(beta_root)
            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "generate_overview.sh"),
                    str(site_path),
                    "beta",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            run_dir = _capture_single_new_run(space_root=beta_root, before_runs=before_runs)
            frontmatter = parse_run_frontmatter(run_dir / "run.md")
            self.assertEqual(frontmatter["scope_kind"], "subspace")
            self.assertEqual(frontmatter["overview_id"], "subspace--beta")
            self.assertTrue(
                (beta_root / "outputs" / "space_overview" / "subspace--beta" / "overview.json").is_file()
            )

    def test_wrapper_propagates_terminal_failure_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            _seed_source(space_root, source_id="source-alpha--aaaaaaaaaaaa", title="Source Alpha")

            result = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "generate_overview.sh"),
                    str(site_path),
                    "alpha",
                    "--mock-llm",
                    "--simulate-terminal-failure",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Simulated terminal overview failure", result.stderr)
            self.assertEqual(
                list((space_root / "outputs" / "space_overview").glob("space--alpha")),
                [],
            )
            self.assertEqual(list((space_root / "runs").glob("*/run.md")), [])


def _seed_source(space_root: Path, *, source_id: str, title: str) -> None:
    path = space_root / "sources" / "records" / f"{source_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "source_record_v1",
                "source_id": source_id,
                "title": title,
                "date": "2026-04-25",
                "ingested_at": "2026-04-25T00:00:00Z",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _capture_single_new_run(*, space_root: Path, before_runs: list[Path]) -> Path:
    after_runs = run_directories(space_root)
    created = [path for path in after_runs if path not in before_runs]
    if len(created) != 1:
        raise AssertionError(
            "Expected exactly one new run directory. "
            f"before={[path.name for path in before_runs]} after={[path.name for path in after_runs]}"
        )
    return created[0]


if __name__ == "__main__":
    unittest.main()
