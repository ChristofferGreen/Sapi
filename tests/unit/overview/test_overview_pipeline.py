from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.overview.overview_pipeline import (
    OverviewInputs,
    OverviewScope,
    determine_overview_refresh,
    resolve_overview_scope,
)
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

    def test_determine_overview_refresh_skips_when_signature_matches_existing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            scope = _scope()
            inputs = _inputs(signature="sha256:stable")
            _seed_overview_artifacts(space_root=space_root, scope=scope, input_signature="sha256:stable")

            decision = determine_overview_refresh(
                space_root=space_root,
                scope=scope,
                inputs=inputs,
                force_mode=False,
            )

            self.assertFalse(decision.refresh_required)
            self.assertEqual(decision.refresh_decision, "skip")
            self.assertEqual(decision.refresh_reason, "no_content_change")

    def test_determine_overview_refresh_requires_regeneration_when_signature_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            scope = _scope()
            inputs = _inputs(signature="sha256:new")
            _seed_overview_artifacts(space_root=space_root, scope=scope, input_signature="sha256:old")

            decision = determine_overview_refresh(
                space_root=space_root,
                scope=scope,
                inputs=inputs,
                force_mode=False,
            )

            self.assertTrue(decision.refresh_required)
            self.assertEqual(decision.refresh_decision, "refresh")
            self.assertEqual(decision.refresh_reason, "input_signature_changed")

    def test_determine_overview_refresh_force_mode_bypasses_unchanged_signature_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            scope = _scope()
            inputs = _inputs(signature="sha256:stable")
            _seed_overview_artifacts(space_root=space_root, scope=scope, input_signature="sha256:stable")

            decision = determine_overview_refresh(
                space_root=space_root,
                scope=scope,
                inputs=inputs,
                force_mode=True,
            )

            self.assertTrue(decision.refresh_required)
            self.assertEqual(decision.refresh_decision, "refresh")
            self.assertEqual(decision.refresh_reason, "force_mode")


def _scope() -> OverviewScope:
    return OverviewScope(
        overview_id="space--alpha",
        scope_kind="space",
        space_name="alpha",
        scope_name="alpha",
        title=None,
        parent_space_name=None,
    )


def _inputs(*, signature: str) -> OverviewInputs:
    return OverviewInputs(
        source_records=[],
        claims=[],
        relations=[],
        topics=[],
        source_ids=[],
        claim_ids=[],
        relation_ids=[],
        topic_ids=[],
        input_signature=signature,
    )


def _seed_overview_artifacts(*, space_root: Path, scope: OverviewScope, input_signature: str) -> None:
    overview_root = space_root / "outputs" / "space_overview" / scope.overview_id
    overview_root.mkdir(parents=True, exist_ok=True)
    (overview_root / "context.json").write_text(
        json.dumps(
            {
                "schema_version": "space_overview_context_v1",
                "metadata": {"overview_id": scope.overview_id},
                "freshness": {"input_signature": input_signature},
                "warnings": [],
                "source_records": [],
                "claims": [],
                "relations": [],
                "topics": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (overview_root / "overview.json").write_text(
        json.dumps(
            {
                "schema_version": "space_overview_v1",
                "metadata": {
                    "overview_id": scope.overview_id,
                    "scope_kind": scope.scope_kind,
                    "space_name": scope.space_name,
                    "scope_name": scope.scope_name,
                    "title": "State of the Evidence in alpha",
                    "summary": "Summary",
                },
                "sections": [],
                "references": {"source_ids": [], "claim_ids": [], "citation_anchors": []},
                "freshness": {
                    "generated_at": "2026-04-25T00:00:00Z",
                    "input_signature": input_signature,
                    "source_record_count": 0,
                    "claim_count": 0,
                    "relation_count": 0,
                    "topic_count": 0,
                },
                "warnings": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (overview_root / "article.md").write_text("# State of the Evidence in alpha\n")


if __name__ == "__main__":
    unittest.main()
