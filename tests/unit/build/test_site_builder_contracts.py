from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_site import _validate_frontend_toolchain_reproducibility
from sapi.profiles.persona_catalog import load_seeded_persona_catalog


REPO_ROOT = Path(__file__).resolve().parents[3]


class SiteBuilderContractTests(unittest.TestCase):
    def test_build_renders_deterministic_html_from_canonical_json_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(space_root, source_id="source-a", title="Source A")
            self._write_topic_record(
                space_root,
                topic_id="topic-a",
                title="Topic A",
                source_ids=["source-a"],
            )
            # Non-canonical artifact should not affect deterministic build output.
            (space_root / "raw" / "semantic_dump.json").write_text(json.dumps({"noise": True}))

            command = [
                "python3",
                str(REPO_ROOT / "scripts" / "build_site.py"),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "alpha",
            ]
            first = self._run(command)
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            self.assertIn("deterministic build complete", first.stdout)

            manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            first_manifest_text = manifest_path.read_text()
            first_manifest = json.loads(first_manifest_text)
            self.assertEqual(first_manifest["semantic_flows_executed"], [])
            self.assertEqual(first_manifest["space_targets"], ["alpha"])
            self.assertEqual(first_manifest["frozen_install_mode"], "npm ci")
            self.assertIn("toolchain_versions", first_manifest)
            self.assertIn("node", first_manifest["toolchain_versions"])
            self.assertIn("package_manager", first_manifest["toolchain_versions"])
            self.assertIn("tailwind_cli", first_manifest["toolchain_versions"])

            space_index_path = space_root / "site" / "index.html"
            topic_page_path = space_root / "site" / "topics" / "topic-a.html"
            source_page_path = space_root / "site" / "sources" / "source-a.html"
            site_new_path = site_path / "site" / "new" / "index.html"
            self.assertTrue(space_index_path.is_file())
            self.assertTrue(topic_page_path.is_file())
            self.assertTrue(source_page_path.is_file())
            self.assertTrue(site_new_path.is_file())

            first_index_text = space_index_path.read_text()
            self.assertIn("Topic A", first_index_text)
            self.assertIn("Source A", first_index_text)

            second = self._run(command)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            second_manifest_text = manifest_path.read_text()
            self.assertEqual(first_manifest_text, second_manifest_text)
            self.assertEqual(first_index_text, space_index_path.read_text())

    def test_build_fails_fast_on_unresolved_topic_source_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_topic_record(
                space_root,
                topic_id="topic-missing-link",
                title="Broken Topic",
                source_ids=["source-does-not-exist"],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unresolved source link", result.stderr)

    def test_pinned_parent_link_resolves_only_via_imports_lock_snapshot_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, child_space_root = self._bootstrap_site_space(tmp_root, "child")
            self._write_topic_record(
                child_space_root,
                topic_id="topic-child--111111111111",
                title="Child Topic",
                source_ids=[],
                pinned_parent_ref={
                    "space_name": "parent",
                    "topic_id": "topic-parent--222222222222",
                },
            )
            self._write_imports_lock_entries(
                child_space_root,
                [
                    {
                        "parent_space_name": "parent",
                        "parent_topic_id": "topic-parent--222222222222",
                        "parent_snapshot": "snapshot-20260412",
                        "parent_site_base_url": "https://parent.example.test",
                    }
                ],
            )

            # Parent topic JSON is intentionally absent; resolution must be lock-entry based only.
            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "child",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            topic_page = (child_space_root / "site" / "topics" / "topic-child--111111111111.html").read_text()
            self.assertIn("class=\"pinned-parent-link\"", topic_page)
            self.assertIn("data-space-name=\"parent\"", topic_page)
            self.assertIn("data-topic-id=\"topic-parent--222222222222\"", topic_page)
            self.assertIn("data-parent-space-name=\"parent\"", topic_page)
            self.assertIn("data-parent-snapshot=\"snapshot-20260412\"", topic_page)
            self.assertIn("data-parent-site-base-url=\"https://parent.example.test\"", topic_page)
            self.assertIn(
                "href=\"https://parent.example.test/spaces/parent/site/topics/topic-parent--222222222222.html\"",
                topic_page,
            )

            manifest = json.loads((site_path / "outputs" / "build_site" / "manifest.json").read_text())
            self.assertEqual(manifest["lint"]["error_count"], 0)

    def test_unresolved_pinned_parent_link_renders_disabled_marker_and_lint_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, parent_space_root = self._bootstrap_site_space(tmp_root, "parent")
            _site_path_2, child_space_root = self._bootstrap_site_space(tmp_root, "child")

            self._write_topic_record(
                parent_space_root,
                topic_id="topic-parent--aaaaaaaaaaaa",
                title="Parent Topic",
                source_ids=[],
            )
            self._write_topic_record(
                child_space_root,
                topic_id="topic-child--bbbbbbbbbbbb",
                title="Child Topic",
                source_ids=[],
                pinned_parent_ref={
                    "space_name": "parent",
                    "topic_id": "topic-parent--aaaaaaaaaaaa",
                },
            )
            # Intentionally omit matching lock entry; parent topic existence alone must not resolve the pin.
            self._write_imports_lock_entries(child_space_root, [])

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "child",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("lint error [unresolved_pinned_parent_link]", result.stderr)

            topic_page = (child_space_root / "site" / "topics" / "topic-child--bbbbbbbbbbbb.html").read_text()
            self.assertIn("class=\"pinned-parent-link disabled\"", topic_page)
            self.assertIn("aria-disabled=\"true\"", topic_page)
            self.assertIn("Parent topic unavailable: parent/topic-parent--aaaaaaaaaaaa", topic_page)

            manifest = json.loads((site_path / "outputs" / "build_site" / "manifest.json").read_text())
            self.assertEqual(manifest["lint"]["error_count"], 1)
            issues = manifest["lint"]["issues"]
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]["check_id"], "unresolved_pinned_parent_link")
            self.assertEqual(issues[0]["severity"], "error")
            self.assertEqual(issues[0]["space_name"], "child")

    def test_claim_reference_rendering_hides_raw_ids_from_sentence_and_keeps_clickable_audit_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            claim_id = "claim-finding--aaaaaaaaaaaa"
            self._write_topic_record(
                space_root,
                topic_id="topic-claims--aaaaaaaaaaaa",
                title="Claim Rendering Topic",
                source_ids=[],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"A factual sentence [[claims:{claim_id}]] with annotation.",
                    }
                ],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            topic_page_text = (space_root / "site" / "topics" / "topic-claims--aaaaaaaaaaaa.html").read_text()
            self.assertNotIn("[[claims:", topic_page_text)
            body_match = re.search(r"<p class=\"topic-section-body\">(.*?)</p>", topic_page_text)
            self.assertIsNotNone(body_match)
            assert body_match is not None
            self.assertNotIn(claim_id, body_match.group(1))
            self.assertIn("class=\"claim-details-link\"", topic_page_text)
            self.assertIn("href=\"#claim-details-s1-a1\"", topic_page_text)
            self.assertIn("id=\"claim-details-s1-a1\"", topic_page_text)

    def test_claim_reference_rendering_includes_js_off_fallback_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            claim_id = "claim-fallback--bbbbbbbbbbbb"
            self._write_topic_record(
                space_root,
                topic_id="topic-fallback--bbbbbbbbbbbb",
                title="Fallback Topic",
                source_ids=[],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"Sentence [[claims:{claim_id}]].",
                    }
                ],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            topic_page_text = (space_root / "site" / "topics" / "topic-fallback--bbbbbbbbbbbb.html").read_text()
            self.assertIn("<noscript><ul class=\"claim-details-fallback\">", topic_page_text)
            self.assertIn(
                f"<a href=\"../claims/{claim_id}.html\">Claim reference 1</a>",
                topic_page_text,
            )

    def test_site_presentation_mode_public_hides_internal_metadata_and_debug_exposes_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            claim_id = "claim-debug--cccccccccccc"
            self._write_topic_record(
                space_root,
                topic_id="topic-debug--cccccccccccc",
                title="Debug Topic",
                source_ids=[],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"Sentence [[claims:{claim_id}]].",
                    }
                ],
            )

            public_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(public_result.returncode, 0, msg=public_result.stderr)
            public_page_text = (space_root / "site" / "topics" / "topic-debug--cccccccccccc.html").read_text()
            self.assertNotIn("data-claim-id=", public_page_text)
            self.assertNotIn(f">{claim_id}<", public_page_text)
            public_manifest = json.loads((site_path / "outputs" / "build_site" / "manifest.json").read_text())
            self.assertEqual(public_manifest["site_presentation_mode"], "public")

            debug_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--site-presentation-mode",
                    "debug",
                    "alpha",
                ]
            )
            self.assertEqual(debug_result.returncode, 0, msg=debug_result.stderr)
            debug_page_text = (space_root / "site" / "topics" / "topic-debug--cccccccccccc.html").read_text()
            self.assertIn(f"data-claim-id=\"{claim_id}\"", debug_page_text)
            self.assertIn(f">{claim_id}<", debug_page_text)
            debug_manifest = json.loads((site_path / "outputs" / "build_site" / "manifest.json").read_text())
            self.assertEqual(debug_manifest["site_presentation_mode"], "debug")

    def test_topic_renderer_selection_is_deterministic_from_topic_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(space_root, source_id="source-only", title="Only Source")
            self._write_topic_record(
                space_root,
                topic_id="topic-wiki--111111111111",
                title="Wiki Topic",
                source_ids=[],
                structure_type="wiki",
            )
            self._write_topic_record(
                space_root,
                topic_id="topic-mirror--222222222222",
                title="Mirror Topic",
                source_ids=["source-only"],
                structure_type="source_mirror",
                source_structure_outline=["Methods / approach", "Results / findings"],
                sections=[
                    {"heading": "Results / findings", "body": "Synthesis of the primary findings."},
                    {"heading": "Methods / approach", "body": "Synthesis of the study method."},
                ],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            wiki_page = (space_root / "site" / "topics" / "topic-wiki--111111111111.html").read_text()
            mirror_page = (space_root / "site" / "topics" / "topic-mirror--222222222222.html").read_text()
            self.assertIn("data-structure-type=\"wiki\"", wiki_page)
            self.assertIn("data-structure-type=\"source_mirror\"", mirror_page)

    def test_wiki_renderer_enforces_required_section_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_topic_record(
                space_root,
                topic_id="topic-order--333333333333",
                title="Ordered Wiki Topic",
                source_ids=[],
                structure_type="wiki",
                sections=[
                    {"heading": "References", "body": "Refs body."},
                    {"heading": "Lead summary", "body": "Lead body."},
                    {"heading": "Key points", "body": "Key points body."},
                ],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            page = (space_root / "site" / "topics" / "topic-order--333333333333.html").read_text()
            lead_idx = page.index("<h2>Lead summary</h2>")
            key_idx = page.index("<h2>Key points</h2>")
            refs_idx = page.index("<h2>References</h2>")
            self.assertLess(lead_idx, key_idx)
            self.assertLess(key_idx, refs_idx)

    def test_source_mirror_renderer_follows_outline_and_rejects_verbatim_restatements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(space_root, source_id="source-single", title="Single Source")
            self._write_topic_record(
                space_root,
                topic_id="topic-mirror-order--444444444444",
                title="Mirror Ordered Topic",
                source_ids=["source-single"],
                structure_type="source_mirror",
                source_structure_outline=["Methods / approach", "Results / findings"],
                sections=[
                    {"heading": "Results / findings", "body": "Summarized findings and implications."},
                    {"heading": "Methods / approach", "body": "Summarized method overview."},
                ],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            page = (space_root / "site" / "topics" / "topic-mirror-order--444444444444.html").read_text()
            methods_idx = page.index("<h2>Methods / approach</h2>")
            results_idx = page.index("<h2>Results / findings</h2>")
            self.assertLess(methods_idx, results_idx)

            self._write_topic_record(
                space_root,
                topic_id="topic-mirror-invalid--555555555555",
                title="Mirror Invalid Topic",
                source_ids=["source-single"],
                structure_type="source_mirror",
                sections=[
                    {"heading": "Methods / approach", "body": "Methods / approach"},
                ],
            )
            invalid_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertNotEqual(invalid_result.returncode, 0)
            self.assertIn("source_mirror section body must not mirror heading verbatim", invalid_result.stderr)

    def test_build_fails_fast_on_template_conversion_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(space_root, source_id="source-a", title="Source A")
            bad_topic_payload = {
                "topic_id": "topic-invalid-section",
                "title": "Invalid Topic",
                "structure_type": "wiki",
                "sections": [{"heading": "Summary"}],
                "claim_ids": [],
                "source_ids": ["source-a"],
            }
            (space_root / "topics" / "topic-invalid-section.json").write_text(
                json.dumps(bad_topic_payload, indent=2, sort_keys=True) + "\n"
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sections[0].body", result.stderr)

    def test_incremental_build_output_is_equivalent_to_full_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                space_root,
                source_id="source-a",
                title="Source Alpha",
            )
            self._write_topic_record(
                space_root,
                topic_id="topic-a",
                title="Topic Alpha",
                source_ids=["source-a"],
            )

            full_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                ]
            )
            self.assertEqual(full_result.returncode, 0, msg=full_result.stderr)
            full_snapshot = self._capture_html_snapshot(site_path)

            incremental_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--incremental",
                ]
            )
            self.assertEqual(incremental_result.returncode, 0, msg=incremental_result.stderr)
            incremental_snapshot = self._capture_html_snapshot(site_path)
            self.assertEqual(full_snapshot, incremental_snapshot)

            manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            manifest_payload = json.loads(manifest_path.read_text())
            self.assertEqual(manifest_payload["build_mode"], "incremental")

    def test_navigation_sidebar_tabs_and_tab_page_size_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._bootstrap_site_space(tmp_root, "beta")

            for index in range(51):
                self._write_source_record(
                    alpha_space_root,
                    source_id=f"source-{index:03d}",
                    title=f"Source {index:03d}",
                )
            self._write_topic_record(
                alpha_space_root,
                topic_id="topic-a",
                title="Topic A",
                source_ids=["source-000"],
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            space_home = (alpha_space_root / "site" / "index.html").read_text()
            self.assertIn("class=\"sidebar\" style=\"position:relative;z-index:2\"", space_home)
            self.assertIn("class=\"top-search\" style=\"position:relative;z-index:1\"", space_home)
            self.assertIn("<summary>Spaces</summary>", space_home)
            self.assertIn(">Space Home</a>", space_home)
            self.assertIn("/spaces/alpha/site/index.html", space_home)
            self.assertIn("/spaces/beta/site/index.html", space_home)
            self.assertIn("<summary>Topics</summary>", space_home)
            self.assertIn("/spaces/alpha/site/new/index.html", space_home)
            self.assertIn("/spaces/alpha/site/sources/index.html", space_home)
            self.assertIn("/spaces/alpha/site/topics/index.html", space_home)
            self.assertIn("/spaces/alpha/site/users/index.html", space_home)

            sources_page_1 = (alpha_space_root / "site" / "sources" / "index.html").read_text()
            sources_page_2 = (alpha_space_root / "site" / "sources" / "page" / "2" / "index.html").read_text()
            self.assertIn("data-tab-page-size=\"50\"", sources_page_1)
            self.assertIn("Page size: 50", sources_page_1)
            self.assertIn("?tab_page=2", sources_page_1)
            self.assertNotIn("?feed_page=2", sources_page_1)
            self.assertEqual(sources_page_1.count("/site/sources/source-"), 50)
            self.assertEqual(sources_page_2.count("/site/sources/source-"), 1)

    def test_site_feed_ordering_tiebreak_and_feed_pagination_url_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            _site_path_2, beta_space_root = self._bootstrap_site_space(tmp_root, "beta")

            self._write_source_record(
                alpha_space_root,
                source_id="source-alpha-latest",
                title="Alpha Latest",
                ingested_at="2026-04-12T10:00:00Z",
            )
            self._write_source_record(
                beta_space_root,
                source_id="source-beta-latest",
                title="Beta Latest",
                ingested_at="2026-04-12T10:00:00Z",
            )
            for index in range(50):
                self._write_source_record(
                    alpha_space_root,
                    source_id=f"source-alpha-old-{index:03d}",
                    title=f"Alpha Old {index:03d}",
                    ingested_at="2026-04-01T00:00:00Z",
                )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            site_new_page_1 = (site_path / "site" / "new" / "index.html").read_text()
            site_new_page_2 = (site_path / "site" / "new" / "page" / "2" / "index.html").read_text()
            alpha_latest_href = "/spaces/alpha/site/sources/source-alpha-latest.html"
            beta_latest_href = "/spaces/beta/site/sources/source-beta-latest.html"
            self.assertIn(alpha_latest_href, site_new_page_1)
            self.assertIn(beta_latest_href, site_new_page_1)
            self.assertLess(site_new_page_1.index(alpha_latest_href), site_new_page_1.index(beta_latest_href))
            self.assertIn("?feed_page=2", site_new_page_1)
            self.assertNotIn("?tab_page=2", site_new_page_1)
            self.assertIn("?feed_page=1", site_new_page_2)

    def test_source_preview_assets_are_written_to_canonical_site_asset_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-preview-a",
                title="Preview Source A",
                summary="Deterministic summary text for preview.",
                source_file_rel="sources/artifacts/source-preview-a/source.pdf",
            )

            cmd = [
                "python3",
                str(REPO_ROOT / "scripts" / "build_site.py"),
                "--registry-path",
                str(site_path / "spaces.toml"),
            ]
            first = self._run(cmd)
            self.assertEqual(first.returncode, 0, msg=first.stderr)

            preview_path = site_path / "site" / "assets" / "source_previews" / "source-preview-a.svg"
            self.assertTrue(preview_path.is_file())
            first_svg = preview_path.read_text()
            self.assertIn("Preview Source A", first_svg)
            self.assertIn("source-preview-a", first_svg)

            second = self._run(cmd)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            self.assertEqual(first_svg, preview_path.read_text())

    def test_source_detail_and_feed_rows_render_preview_assets_and_source_pdf_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-preview-b",
                title="Preview Source B",
                summary="Source summary appears near top.",
                source_file_rel="sources/artifacts/source-preview-b/source.pdf",
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            source_page = (alpha_space_root / "site" / "sources" / "source-preview-b.html").read_text()
            self.assertIn("class=\"source-summary\"", source_page)
            self.assertIn("Source summary appears near top.", source_page)
            self.assertIn("class=\"source-preview-link\"", source_page)
            self.assertIn("/site/assets/source_previews/source-preview-b.svg", source_page)
            self.assertIn("/spaces/alpha/sources/artifacts/source-preview-b/source.pdf", source_page)

            site_new_page = (site_path / "site" / "new" / "index.html").read_text()
            self.assertIn("class=\"source-preview-feed\"", site_new_page)
            self.assertIn("/site/assets/source_previews/source-preview-b.svg", site_new_page)

            space_new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("class=\"source-preview-feed\"", space_new_page)
            self.assertIn("/site/assets/source_previews/source-preview-b.svg", space_new_page)

    def test_source_preview_generation_and_markup_are_deterministic_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-preview-c",
                title="Preview Source C",
                summary="Snapshot stable preview.",
                source_file_rel="sources/artifacts/source-preview-c/source.pdf",
            )

            cmd = [
                "python3",
                str(REPO_ROOT / "scripts" / "build_site.py"),
                "--registry-path",
                str(site_path / "spaces.toml"),
            ]
            first = self._run(cmd)
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            first_snapshot = {
                "preview_svg": (site_path / "site" / "assets" / "source_previews" / "source-preview-c.svg").read_text(),
                "source_page": (alpha_space_root / "site" / "sources" / "source-preview-c.html").read_text(),
                "site_new_page": (site_path / "site" / "new" / "index.html").read_text(),
                "space_new_page": (alpha_space_root / "site" / "new" / "index.html").read_text(),
            }

            second = self._run(cmd)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            second_snapshot = {
                "preview_svg": (site_path / "site" / "assets" / "source_previews" / "source-preview-c.svg").read_text(),
                "source_page": (alpha_space_root / "site" / "sources" / "source-preview-c.html").read_text(),
                "site_new_page": (site_path / "site" / "new" / "index.html").read_text(),
                "space_new_page": (alpha_space_root / "site" / "new" / "index.html").read_text(),
            }
            self.assertEqual(first_snapshot, second_snapshot)

    def test_users_tab_scope_and_space_profile_link_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._bootstrap_site_space(tmp_root, "beta")
            catalog_path = REPO_ROOT / "personas" / "social_users.json"
            original_catalog = catalog_path.read_text()
            try:
                seeded_catalog = {
                    "schema_version": "social_users_v1",
                    "count": 1,
                    "users": [
                        {
                            "persona_id": "persona-one",
                            "display_name": "Persona One",
                            "full_name": "Persona One",
                            "account_status": "active",
                            "stance_profile": "neutral",
                            "profile_image_path": "personas/profile_images/.gitkeep",
                        }
                    ],
                }
                catalog_path.write_text(json.dumps(seeded_catalog, indent=2, sort_keys=True) + "\n")

                result = self._run(
                    [
                        "python3",
                        str(REPO_ROOT / "scripts" / "build_site.py"),
                        "--registry-path",
                        str(site_path / "spaces.toml"),
                    ]
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)

                persona_rows = load_seeded_persona_catalog(repo_root=REPO_ROOT)
                self.assertGreater(len(persona_rows), 0)
                persona_id = str(persona_rows[0]["persona_id"])

                site_users_page = (site_path / "site" / "users" / "index.html").read_text()
                alpha_profile_href = f"/spaces/alpha/site/users/persona-{persona_id}.html"
                beta_profile_href = f"/spaces/beta/site/users/persona-{persona_id}.html"
                self.assertIn(alpha_profile_href, site_users_page)
                self.assertIn(beta_profile_href, site_users_page)

                alpha_users_page = (alpha_space_root / "site" / "users" / "index.html").read_text()
                self.assertIn(alpha_profile_href, alpha_users_page)
                self.assertNotIn(beta_profile_href, alpha_users_page)

                alpha_profile_page = alpha_space_root / "site" / "users" / f"persona-{persona_id}.html"
                self.assertTrue(alpha_profile_page.is_file())
                self.assertIn(f"persona_id: {persona_id}", alpha_profile_page.read_text())
            finally:
                catalog_path.write_text(original_catalog)

    def test_toolchain_reproducibility_validation_enforces_package_manager_lockfile_node_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)

            # Missing packageManager.
            self._write_package_json(repo_root, {"name": "sapi", "version": "0.0.0"})
            self._write_npm_lockfile(repo_root, "sapi", "0.0.0")
            (repo_root / ".nvmrc").write_text("20\n")
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Mismatched package-manager family and lockfile.
            self._write_package_json(
                repo_root,
                {"name": "sapi", "version": "0.0.0", "packageManager": "pnpm@9.0.0"},
            )
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Multiple lockfiles.
            (repo_root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Missing node pin.
            (repo_root / "pnpm-lock.yaml").unlink()
            (repo_root / ".nvmrc").unlink()
            self._write_package_json(
                repo_root,
                {"name": "sapi", "version": "0.0.0", "packageManager": "npm@10.9.2"},
            )
            with self.assertRaises(ValueError):
                _validate_frontend_toolchain_reproducibility(repo_root)

            # Valid reproducibility envelope.
            (repo_root / ".nvmrc").write_text("20\n")
            result = _validate_frontend_toolchain_reproducibility(repo_root)
            self.assertEqual(result["package_manager"], "npm@10.9.2")
            self.assertEqual(result["frozen_install_mode"], "npm ci")
            self.assertEqual(result["node"], "20")

    def _bootstrap_site_space(self, tmp_root: Path, space_name: str) -> tuple[Path, Path]:
        site_path = tmp_root / "site-a"
        self._run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
        self._run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
        space_root = site_path / "spaces" / space_name
        return site_path, space_root

    def _write_source_record(
        self,
        space_root: Path,
        *,
        source_id: str,
        title: str,
        ingested_at: str = "2026-04-12T00:00:00Z",
        summary: str | None = None,
        source_file_rel: str | None = None,
    ) -> None:
        payload = {
            "schema_version": "source_record_v1",
            "source_id": source_id,
            "title": title,
            "date": ingested_at.split("T", 1)[0],
            "ingested_at": ingested_at,
        }
        if summary is not None:
            payload["summary"] = summary
        if source_file_rel is not None:
            payload["artifacts"] = {
                "source_file": source_file_rel,
                "overview_markdown": f"sources/artifacts/{source_id}/overview.md",
                "front_page_image": None,
            }
        path = space_root / "sources" / "records" / f"{source_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_topic_record(
        self,
        space_root: Path,
        *,
        topic_id: str,
        title: str,
        source_ids: list[str],
        sections: list[dict[str, str]] | None = None,
        structure_type: str = "wiki",
        source_structure_outline: list[str] | None = None,
        pinned_parent_ref: dict[str, str] | None = None,
    ) -> None:
        payload = {
            "topic_id": topic_id,
            "title": title,
            "structure_type": structure_type,
            "sections": sections if sections is not None else [{"heading": "Summary", "body": "Body"}],
            "claim_ids": [],
            "source_ids": source_ids,
        }
        if source_structure_outline is not None:
            payload["source_structure_outline"] = source_structure_outline
        if pinned_parent_ref is not None:
            payload["pinned_parent_ref"] = pinned_parent_ref
        path = space_root / "topics" / f"{topic_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_imports_lock_entries(
        self,
        space_root: Path,
        entries: list[dict[str, str]],
    ) -> None:
        payload = {"schema_version": "imports_lock_v1", "imports": entries}
        lock_path = space_root / "imports.lock.md"
        lock_path.write_text(
            "# imports.lock.md\n\n"
            "```json\n"
            + json.dumps(payload, indent=2, sort_keys=True)
            + "\n```\n"
        )

    def _write_package_json(self, repo_root: Path, payload: dict[str, object]) -> None:
        (repo_root / "package.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_npm_lockfile(self, repo_root: Path, name: str, version: str) -> None:
        payload = {
            "name": name,
            "version": version,
            "lockfileVersion": 3,
            "requires": True,
            "packages": {"": {"name": name, "version": version}},
        }
        (repo_root / "package-lock.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _capture_html_snapshot(self, site_path: Path) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for html_path in sorted(site_path.rglob("*.html")):
            snapshot[str(html_path.relative_to(site_path))] = html_path.read_text()
        return snapshot

    def _run(self, cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise AssertionError(
                f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        return result


if __name__ == "__main__":
    unittest.main()
