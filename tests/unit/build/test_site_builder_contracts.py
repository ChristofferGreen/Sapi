from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_site import _validate_frontend_toolchain_reproducibility


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

    def _write_source_record(self, space_root: Path, *, source_id: str, title: str) -> None:
        payload = {
            "schema_version": "source_record_v1",
            "source_id": source_id,
            "title": title,
            "date": "2026-04-12",
            "ingested_at": "2026-04-12T00:00:00Z",
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
