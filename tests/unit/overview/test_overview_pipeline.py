from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sapi.overview.overview_pipeline import resolve_overview_scope
from tests.conftest import REPO_ROOT, run_command


class OverviewPipelineUnitTests(unittest.TestCase):
    def test_resolve_overview_scope_detects_subspace_membership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = tmp_root / "site-a"
            run_command(
                ["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"],
                check=True,
            )
            run_command(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "alpha"],
                check=True,
            )
            run_command(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "beta"],
                check=True,
            )

            alpha_root = site_path / "spaces" / "alpha"
            (alpha_root / "subspaces.json").write_text(
                """
{
  "schema_version": "space_subspaces_v1",
  "subspaces": [
    {
      "space_name": "beta",
      "space_root": "../beta",
      "title": "Beta Subspace"
    }
  ]
}
""".strip()
                + "\n"
            )

            scope = resolve_overview_scope(site_path=site_path, space_name="beta")
            self.assertEqual(scope.scope_kind, "subspace")
            self.assertEqual(scope.overview_id, "subspace--beta")
            self.assertEqual(scope.parent_space_name, "alpha")
            self.assertEqual(scope.title, "Beta Subspace")


if __name__ == "__main__":
    unittest.main()
