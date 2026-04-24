from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command, write_source_fixture


class BuildDeterminismIntegrationTests(unittest.TestCase):
    def test_repeated_full_builds_produce_identical_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            source_path = write_source_fixture(tmp_root, content="tier4 deterministic fixture\n")

            ingest_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Tier4 Determinism Source",
                    "--mock-llm",
                ]
            )
            self.assertEqual(ingest_result.returncode, 0, msg=ingest_result.stderr)
            _seed_overview_artifact(
                site_path / "spaces" / "alpha",
                overview_id="space--alpha",
                space_name="alpha",
            )

            first_build = _run_build(site_path=site_path, incremental=False)
            self.assertEqual(first_build.returncode, 0, msg=first_build.stderr)
            first_snapshot = _capture_build_snapshot(site_path=site_path)
            self.assertIn("outputs/build_site/manifest.json", first_snapshot)
            self.assertIn("site/index.html", first_snapshot)
            self.assertIn("spaces/alpha/site/index.html", first_snapshot)
            self.assertIn("spaces/alpha/site/overview/index.html", first_snapshot)
            self.assertIn("site/assets/site.css", first_snapshot)
            self.assertIn("spaces/alpha/site/assets/site.css", first_snapshot)
            self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', first_snapshot["site/index.html"])
            self.assertIn('<link rel="stylesheet" href="assets/site.css">', first_snapshot["site/index.html"])
            self.assertIn(
                '<link rel="stylesheet" href="assets/site.css">',
                first_snapshot["spaces/alpha/site/index.html"],
            )
            self.assertIn("Open full overview", first_snapshot["spaces/alpha/site/index.html"])
            self.assertIn("Deterministic overview summary.", first_snapshot["spaces/alpha/site/overview/index.html"])

            second_build = _run_build(site_path=site_path, incremental=False)
            self.assertEqual(second_build.returncode, 0, msg=second_build.stderr)
            second_snapshot = _capture_build_snapshot(site_path=site_path)

            self.assertEqual(first_snapshot, second_snapshot)


def _run_build(*, site_path: Path, incremental: bool) -> object:
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "build_site.py"),
        "--registry-path",
        str(site_path / "spaces.toml"),
        "alpha",
    ]
    if incremental:
        cmd.append("--incremental")
    return run_command(cmd)


def _capture_build_snapshot(*, site_path: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted((site_path / "site").rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".html", ".svg", ".css"}:
            continue
        snapshot[str(path.relative_to(site_path))] = path.read_text()

    for path in sorted((site_path / "spaces" / "alpha" / "site").rglob("*")):
        if not path.is_file() or path.suffix not in {".html", ".css"}:
            continue
        snapshot[str(path.relative_to(site_path))] = path.read_text()

    manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
    snapshot[str(manifest_path.relative_to(site_path))] = manifest_path.read_text()
    return snapshot


def _seed_overview_artifact(space_root: Path, *, overview_id: str, space_name: str) -> None:
    payload = {
        "schema_version": "space_overview_v1",
        "metadata": {
            "overview_id": overview_id,
            "scope_kind": "space",
            "space_name": space_name,
            "scope_name": space_name,
            "title": "State of the Evidence in alpha",
            "summary": "Deterministic overview summary.",
        },
        "sections": [
            {
                "section_id": "topic_framing",
                "heading": "Topic framing",
                "body": "Deterministic topic framing.",
                "source_ids": [],
                "claim_ids": [],
                "citation_anchor_ids": [],
            },
            {
                "section_id": "key_themes",
                "heading": "Key themes",
                "body": "Deterministic key themes.",
                "source_ids": [],
                "claim_ids": [],
                "citation_anchor_ids": [],
            },
            {
                "section_id": "agreement_and_disagreement",
                "heading": "Agreement and disagreement",
                "body": "Deterministic agreement summary.",
                "source_ids": [],
                "claim_ids": [],
                "citation_anchor_ids": [],
            },
            {
                "section_id": "methods_and_evidence",
                "heading": "Methods and evidence",
                "body": "Deterministic methods summary.",
                "source_ids": [],
                "claim_ids": [],
                "citation_anchor_ids": [],
            },
            {
                "section_id": "open_questions",
                "heading": "Open questions",
                "body": "Deterministic open questions.",
                "source_ids": [],
                "claim_ids": [],
                "citation_anchor_ids": [],
            },
        ],
        "references": {"source_ids": [], "claim_ids": [], "citation_anchors": []},
        "freshness": {
            "generated_at": "2026-04-24T09:00:00Z",
            "input_signature": "deterministic-overview-signature",
            "source_record_count": 0,
            "claim_count": 0,
            "relation_count": 0,
            "topic_count": 0,
        },
        "warnings": [],
    }
    overview_path = space_root / "outputs" / "space_overview" / overview_id / "overview.json"
    overview_path.parent.mkdir(parents=True, exist_ok=True)
    overview_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    unittest.main()
