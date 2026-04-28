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
            self.assertNotEqual(first_manifest["toolchain_versions"]["tailwind_cli"], "not_declared")
            self.assertIn("stylesheet_assets", first_manifest)
            self.assertGreaterEqual(len(first_manifest["stylesheet_assets"]), 2)

            space_index_path = space_root / "site" / "index.html"
            topic_page_path = space_root / "site" / "topics" / "topic-a.html"
            source_page_path = space_root / "site" / "sources" / "source-a.html"
            site_new_path = site_path / "site" / "new" / "index.html"
            site_css_path = site_path / "site" / "assets" / "site.css"
            space_css_path = space_root / "site" / "assets" / "site.css"
            self.assertTrue(space_index_path.is_file())
            self.assertTrue(topic_page_path.is_file())
            self.assertTrue(source_page_path.is_file())
            self.assertTrue(site_new_path.is_file())
            self.assertTrue(site_css_path.is_file())
            self.assertTrue(space_css_path.is_file())
            self.assertGreater(site_css_path.stat().st_size, 0)
            self.assertEqual(site_css_path.read_bytes(), space_css_path.read_bytes())

            first_index_text = space_index_path.read_text()
            topic_page_text = topic_page_path.read_text()
            source_page_text = source_page_path.read_text()
            self.assertIn("Topic A", first_index_text)
            self.assertIn("Source A", first_index_text)
            self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', first_index_text)
            self.assertIn('<link rel="stylesheet" href="assets/site.css">', first_index_text)
            self.assertIn('class="site-root-menubar"', first_index_text)
            self.assertIn('class="site-name site-home-link" href="../../../site/index.html">', first_index_text)
            self.assertIn("class=\"comment-thread\"", topic_page_text)
            self.assertIn("No comments yet for this page.", topic_page_text)
            self.assertIn('class="site-root-menubar"', source_page_text)
            self.assertIn('class="site-name site-home-link" href="../../../../site/index.html">', source_page_text)
            self.assertIn("class=\"comment-thread\"", source_page_text)
            self.assertIn("No comments yet for this page.", source_page_text)
            site_new_text = site_new_path.read_text()
            self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', site_new_text)
            self.assertIn('<link rel="stylesheet" href="../assets/site.css">', site_new_text)

            second = self._run(command)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            second_manifest_text = manifest_path.read_text()
            self.assertEqual(first_manifest_text, second_manifest_text)
            self.assertEqual(first_index_text, space_index_path.read_text())
            self.assertEqual(site_css_path.read_bytes(), space_css_path.read_bytes())

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
                        "body": f"A factual sentence with annotation. [[claims:{claim_id}]]",
                    }
                ],
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

            topic_page_text = (space_root / "site" / "topics" / "topic-claims--aaaaaaaaaaaa.html").read_text()
            self.assertNotIn("[[claims:", topic_page_text)
            body_match = re.search(r"<p class=\"topic-section-body\">(.*?)</p>", topic_page_text)
            self.assertIsNotNone(body_match)
            assert body_match is not None
            self.assertNotIn(f">{claim_id}<", body_match.group(1))
            self.assertIn("class=\"sentence-claim-link\"", topic_page_text)
            self.assertIn(
                f"<a class=\"sentence-claim-link\" href=\"../claims/{claim_id}.html\">",
                topic_page_text,
            )
            claims_index_text = (space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn(f"href=\"{claim_id}.html\"", claims_index_text)
            claim_page_text = (space_root / "site" / "claims" / f"{claim_id}.html").read_text()
            self.assertIn(f"<h1>{claim_id}</h1>", claim_page_text)

    def test_claim_reference_rendering_multi_claim_sentence_opens_selector_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            claim_id_1 = "claim-fallback--bbbbbbbbbbbb"
            claim_id_2 = "claim-fallback--cccccccccccc"
            self._write_claim_record(
                space_root,
                claim_id=claim_id_1,
                source_id="source-a",
                text=(
                    "The paper claims that preparation independence constrains epistemic overlaps between distinct "
                    "quantum states in multi-system measurement settings."
                ),
            )
            self._write_claim_record(
                space_root,
                claim_id=claim_id_2,
                source_id="source-a",
                text="Joint measurements reveal incompatibility with psi-epistemic models.",
            )
            self._write_topic_record(
                space_root,
                topic_id="topic-fallback--bbbbbbbbbbbb",
                title="Fallback Topic",
                source_ids=[],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"Sentence with multiple references. [[claims:{claim_id_1},{claim_id_2}]]",
                    }
                ],
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

            topic_page_text = (space_root / "site" / "topics" / "topic-fallback--bbbbbbbbbbbb.html").read_text()
            self.assertIn("class=\"content-card topic-content-card\"", topic_page_text)
            self.assertIn("class=\"sentence-claim-picker\"", topic_page_text)
            self.assertIn("aria-expanded=\"false\"", topic_page_text)
            self.assertIn("class=\"sentence-claim-card\"", topic_page_text)
            self.assertIn("class=\"sentence-claim-option\"", topic_page_text)
            self.assertIn("closeAll(picker);", topic_page_text)
            self.assertIn("data-open", topic_page_text)
            self.assertIn("positionCard(picker);", topic_page_text)
            self.assertIn("picker.setAttribute('data-align','right');", topic_page_text)
            self.assertIn("card.style.maxWidth=targetWidth+'px';", topic_page_text)
            self.assertIn("window.addEventListener('resize'", topic_page_text)
            self.assertIn(
                (
                    f"<a class=\"sentence-claim-option\" href=\"../claims/{claim_id_1}.html\">"
                    "The paper claims that preparation independence constrains epistemic overlaps between "
                    "distinct quantum states in multi-system measurement settings</a>"
                ),
                topic_page_text,
            )
            self.assertIn(
                (
                    f"<a class=\"sentence-claim-option\" href=\"../claims/{claim_id_2}.html\">"
                    "Joint measurements reveal incompatibility with psi-epistemic models</a>"
                ),
                topic_page_text,
            )
            self.assertNotIn("Claim reference 1", topic_page_text)
            self.assertNotIn("Claim reference 2", topic_page_text)
            option_labels = re.findall(r'class=\"sentence-claim-option\" href=\"[^\"]+\">([^<]+)</a>', topic_page_text)
            self.assertGreaterEqual(len(option_labels), 2)
            self.assertTrue(all(len(label.split()) >= 3 for label in option_labels))

    def test_comment_threads_render_nested_collapsible_rows_with_compact_avatar_and_vote_stack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            persona_rows = load_seeded_persona_catalog(repo_root=REPO_ROOT)
            self.assertGreater(len(persona_rows), 0)
            persona_ids = [str(row["persona_id"]) for row in persona_rows]
            persona_display_names = {
                str(row["persona_id"]): str(row.get("display_name") or row["persona_id"])
                for row in persona_rows
            }
            root_persona = persona_ids[0]
            child_persona = persona_ids[1] if len(persona_ids) > 1 else persona_ids[0]
            leaf_persona = persona_ids[2] if len(persona_ids) > 2 else persona_ids[0]

            self._write_topic_record(
                space_root,
                topic_id="topic-comments-tree--aaaaaaaaaaaa",
                title="Nested Comment Topic",
                source_ids=[],
                comment_section={
                    "page_ref": "topic:topic-comments-tree--aaaaaaaaaaaa",
                    "comments": [
                        {
                            "comment_uid": "comment-root",
                            "comment_no": "1",
                            "persona_id": root_persona,
                            "body": "Root level comment",
                            "permalink": "#comment-root",
                            "social_vote": {"upvotes": 34, "downvotes": 5, "score": 29},
                        },
                        {
                            "comment_uid": "comment-child",
                            "comment_no": "2",
                            "parent_comment_uid": "comment-root",
                            "persona_id": child_persona,
                            "body": "Nested reply",
                            "permalink": "#comment-child",
                            "social_vote": {"upvotes": 12, "downvotes": 1, "score": 11},
                        },
                        {
                            "comment_uid": "comment-grandchild",
                            "comment_no": "3",
                            "parent_comment_uid": "comment-child",
                            "persona_id": leaf_persona,
                            "body": "Nested reply level two",
                            "permalink": "#comment-grandchild",
                            "social_vote": {"upvotes": 2, "downvotes": 5, "score": -3},
                        },
                    ],
                    "moderator_outcomes": {
                        "moderator_check": "claim_citation=pass; anti_repetition=pass",
                        "guardrail_checks": {
                            "claim_citation": {"passed": 1, "failed": 0},
                            "anti_repetition": {"passed": 3, "failed": 0},
                            "strongest_opposing_point_ack": {"passed": 1, "failed": 0},
                        },
                        "outcome_sections": {
                            "Consensus": ["Balanced support/challenge signal."],
                            "Open Disagreements": ["No unresolved contradictions."],
                            "Missing Evidence Priorities": ["None."],
                        },
                    },
                },
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

            topic_page_text = (
                space_root / "site" / "topics" / "topic-comments-tree--aaaaaaaaaaaa.html"
            ).read_text()
            self.assertIn("class=\"comment-thread-list\"", topic_page_text)
            self.assertIn("class=\"comment-children\"", topic_page_text)
            self.assertRegex(
                topic_page_text,
                (
                    r"(?s)id=\"comment-root\".*?class=\"comment-children\">.*?id=\"comment-child\""
                    r".*?class=\"comment-children\">.*?id=\"comment-grandchild\""
                ),
            )
            self.assertIn("class=\"comment-summary\"", topic_page_text)
            self.assertIn("class=\"comment-toggle-indicator\"", topic_page_text)
            self.assertIn("class=\"comment-signal-label\">Insightful</span>", topic_page_text)
            self.assertIn("class=\"comment-signal-label\">Average</span>", topic_page_text)
            self.assertIn("class=\"comment-signal-label\">Bad</span>", topic_page_text)
            self.assertIn("class=\"comment-vote-stack comment-signal-insightful\"", topic_page_text)
            self.assertIn("class=\"comment-vote-stack comment-signal-average\"", topic_page_text)
            self.assertIn("class=\"comment-vote-stack comment-signal-bad\"", topic_page_text)
            self.assertIn("class=\"comment-signal-points\">29 points</span>", topic_page_text)
            self.assertIn("class=\"comment-signal-points\">11 points</span>", topic_page_text)
            self.assertIn("class=\"comment-signal-points\">-3 points</span>", topic_page_text)
            self.assertRegex(
                topic_page_text,
                (
                    r"class=\"comment-author\" href=\"[^\"]*users/persona-"
                    + re.escape(root_persona)
                    + r"\.html\">"
                    r"<img class=\"comment-avatar\" [^>]*>"
                    r"<span class=\"comment-persona\">"
                    + re.escape(persona_display_names[root_persona])
                    + r"</span></a>"
                ),
            )
            self.assertNotIn(f">{root_persona}</span>", topic_page_text)
            self.assertNotIn("class=\"comment-no\"", topic_page_text)
            self.assertNotIn("class=\"comment-permalink\"", topic_page_text)
            self.assertNotIn(">permalink</a>", topic_page_text)
            self.assertNotIn("Moderator Check", topic_page_text)
            self.assertNotIn("claim_citation: passed=", topic_page_text)
            self.assertNotIn("<h3>Consensus</h3>", topic_page_text)
            self.assertIn("assets/persona_avatars", topic_page_text)
            self.assertIn("<details class=\"comment-row\" id=\"comment-root\"", topic_page_text)
            self.assertIn("<details class=\"comment-row\" id=\"comment-child\"", topic_page_text)
            self.assertIn("<details class=\"comment-row\" id=\"comment-grandchild\"", topic_page_text)
            self.assertRegex(
                topic_page_text,
                r"<details class=\"comment-row\" id=\"comment-root\"[^>]* open>",
            )
            self.assertRegex(
                topic_page_text,
                r"<details class=\"comment-row\" id=\"comment-child\"[^>]* open>",
            )
            self.assertRegex(
                topic_page_text,
                r"<details class=\"comment-row\" id=\"comment-grandchild\"[^>]*>",
            )
            self.assertNotRegex(
                topic_page_text,
                r"<details class=\"comment-row\" id=\"comment-grandchild\"[^>]* open>",
            )

    def test_claim_pages_render_human_title_overview_usage_evidence_and_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-a"
            claim_id = "claim-rich-overview--aaaaaaaaaaaa"
            claim_text = (
                "Treating quantum states as purely epistemic conflicts with independently "
                "prepared systems in the PBR setup."
            )
            self._write_source_record(
                space_root,
                source_id=source_id,
                title="Source A",
                citation_count=240,
                source_dossier={
                    "summary_short": "Short dossier summary.",
                    "summary_long": "Long dossier summary.",
                    "sections": [
                        {
                            "heading": "Interpretation",
                            "body": (
                                "Within the paper, this claim marks the key break-point where an "
                                "epistemic-only interpretation fails once preparation independence "
                                "is imposed in the formal construction."
                            ),
                            "grounding_claim_ids": [claim_id],
                        }
                    ],
                },
            )
            self._write_claim_record(
                space_root,
                claim_id=claim_id,
                source_id=source_id,
                text=claim_text,
            )
            self._write_evidence_record(
                space_root,
                evidence_id="evidence-prepared-systems-joint--111111111111",
                title="Joint measurement contradiction",
                excerpt="The contradiction appears when independently prepared systems are measured jointly.",
                overview=(
                    "This evidence captures the specific measurement condition that yields contradiction under "
                    "psi-epistemic overlap assumptions."
                ),
                evidence_type="measurement",
                source_id=source_id,
                claim_ids=[claim_id],
                page_refs=["p.4"],
            )
            self._write_evidence_record(
                space_root,
                evidence_id="evidence-overlap-equation-seven--222222222222",
                title="Overlap equation contradiction",
                excerpt="Equation (7) shows overlap assumptions produce predictions incompatible with quantum theory.",
                overview=(
                    "This equation-level result formalizes why overlap assumptions clash with observed predictions."
                ),
                evidence_type="equation",
                source_id=source_id,
                claim_ids=[claim_id],
                page_refs=["Eq.7"],
            )
            self._write_topic_record(
                space_root,
                topic_id="topic-claim-rich--aaaaaaaaaaaa",
                title="Claim-Rich Topic",
                source_ids=[source_id],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"Sentence with grounded claim. [[claims:{claim_id}]]",
                    }
                ],
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

            claim_page_text = (space_root / "site" / "claims" / f"{claim_id}.html").read_text()
            self.assertIn(
                (
                    "<h1>"
                    "Treating quantum states as purely epistemic conflicts with independently prepared systems "
                    "in the PBR setup"
                    "</h1>"
                ),
                claim_page_text,
            )
            self.assertIn("<h2>Claim Statement</h2>", claim_page_text)
            self.assertIn(claim_text, claim_page_text)
            self.assertIn("Overview and Interpretation", claim_page_text)
            self.assertIn(
                "epistemic-only interpretation fails once preparation independence",
                claim_page_text,
            )
            self.assertIn("Pages Using This Claim", claim_page_text)
            self.assertIn("href=\"../topics/topic-claim-rich--aaaaaaaaaaaa.html\"", claim_page_text)
            self.assertIn("href=\"../sources/source-a.html\"", claim_page_text)
            self.assertIn("Short dossier summary.", claim_page_text)
            self.assertIn("Evidence Items", claim_page_text)
            self.assertIn("href=\"../evidence/", claim_page_text)
            self.assertIn("jointly", claim_page_text)
            self.assertNotIn("Strength and Support Stats", claim_page_text)
            self.assertNotIn("Debug Score Metadata", claim_page_text)
            self.assertNotIn("deterministic UI heuristic", claim_page_text)
            self.assertNotIn("neutral fallback", claim_page_text)
            self.assertNotIn(
                "score = 100 * (0.65 * evidence_factor + 0.20 * source_factor + 0.15 * citation_factor)",
                claim_page_text,
            )
            self.assertNotIn("Topic usages (informational only)", claim_page_text)
            self.assertNotIn("class=\"comment-thread\"", claim_page_text)
            evidence_links = re.findall(r'href=\"\.\./evidence/(evidence-[^\"]+)\.html\"', claim_page_text)
            self.assertGreaterEqual(len(evidence_links), 2)

            debug_result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--site-presentation-mode",
                    "debug",
                ]
            )
            self.assertEqual(debug_result.returncode, 0, msg=debug_result.stderr)
            debug_claim_page_text = (space_root / "site" / "claims" / f"{claim_id}.html").read_text()
            self.assertIn("Debug Score Metadata", debug_claim_page_text)
            self.assertIn(
                "score = 100 * (0.65 * evidence_factor + 0.20 * source_factor + 0.15 * citation_factor)",
                debug_claim_page_text,
            )
            self.assertIn("where evidence_factor=min(evidence_items/3,1)", debug_claim_page_text)
            self.assertIn("citation_factor=min(log10(max_citation_count+1)/3,1)", debug_claim_page_text)
            self.assertIn("<dt>Max source citations</dt><dd>240</dd>", debug_claim_page_text)
            self.assertIn("<dt>Citation factor</dt>", debug_claim_page_text)
            self.assertIn("Topic usages (informational only)", debug_claim_page_text)
            self.assertNotIn("deterministic UI heuristic", debug_claim_page_text)
            self.assertNotIn("neutral fallback", debug_claim_page_text)

            evidence_index_text = (space_root / "site" / "evidence" / "index.html").read_text()
            self.assertIn("<h1>Evidence</h1>", evidence_index_text)
            self.assertIn("independently prepared systems", evidence_index_text)
            evidence_page_text = (space_root / "site" / "evidence" / f"{evidence_links[0]}.html").read_text()
            self.assertNotIn("Evidence ID:", evidence_page_text)

            claims_index_text = (space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn("id=\"claims-sort-direction\"", claims_index_text)
            self.assertIn("<option value=\"alphabetical\">Alphabetical</option>", claims_index_text)
            self.assertIn("<option value=\"score\" selected>Score</option>", claims_index_text)
            self.assertIn("<option value=\"reverse_score\">Reverse score</option>", claims_index_text)
            self.assertIn("<option value=\"newest\">Newest</option>", claims_index_text)
            self.assertIn("<option value=\"oldest\">Oldest</option>", claims_index_text)
            self.assertIn("id=\"claims-index-list\"", claims_index_text)
            self.assertIn("data-claim-score=\"", claims_index_text)
            self.assertIn("data-claim-added-at=\"", claims_index_text)
            self.assertIn("parseAddedAt", claims_index_text)
            self.assertIn("mode==='newest'", claims_index_text)
            self.assertIn("mode==='oldest'", claims_index_text)
            self.assertIn("var mode=select.value||'score';", claims_index_text)
            self.assertIn("rows.sort(function(a,b){return compareRows(a,b,mode);});", claims_index_text)
            self.assertIn(f"href=\"{evidence_links[0]}.html\"", evidence_index_text)

            topic_page_text = (space_root / "site" / "topics" / "topic-claim-rich--aaaaaaaaaaaa.html").read_text()
            self.assertIn("Claims Used by This Topic", topic_page_text)
            self.assertIn(f"href=\"../claims/{claim_id}.html\"", topic_page_text)
            self.assertIn("class=\"summary\">", topic_page_text)
            self.assertIn(
                (
                    "Treating quantum states as purely epistemic conflicts with independently prepared systems "
                    "in the PBR setup"
                ),
                topic_page_text,
            )
            self.assertIn("Evidence Used by This Topic", topic_page_text)
            self.assertIn("../evidence/", topic_page_text)

            source_page_text = (space_root / "site" / "sources" / "source-a.html").read_text()
            self.assertIn("Evidence from This Source", source_page_text)
            self.assertIn("../evidence/", source_page_text)
            self.assertIn(
                (
                    "Treating quantum states as purely epistemic conflicts with independently prepared systems "
                    "in the PBR setup"
                ),
                source_page_text,
            )
            self.assertNotIn(f">{claim_id}</a>", source_page_text)
            self.assertIn("class=\"source-evidence-claim-chip\"", source_page_text)

            claims_index_text = (space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn(
                (
                    "Treating quantum states as purely epistemic conflicts with independently prepared systems "
                    "in the PBR setup"
                ),
                claims_index_text,
            )
            self.assertNotIn(f">{claim_id}</a>", claims_index_text)

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
            self.assertIn(f"href=\"../claims/{claim_id}.html\"", debug_page_text)
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
            lead_idx = page.index("<h2 class=\"topic-section-heading\">Lead summary</h2>")
            key_idx = page.index("<h2 class=\"topic-section-heading\">Key points</h2>")
            refs_idx = page.index("<h2 class=\"topic-section-heading\">References</h2>")
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
            methods_idx = page.index("<h2 class=\"topic-section-heading\">Methods / approach</h2>")
            results_idx = page.index("<h2 class=\"topic-section-heading\">Results / findings</h2>")
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

    def test_build_fails_when_stylesheet_contract_files_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, _space_root = self._bootstrap_site_space(tmp_root, "alpha")
            stylesheet_path = REPO_ROOT / "web" / "styles" / "site.css"
            original = stylesheet_path.read_text()
            stylesheet_path.unlink()
            try:
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
                self.assertIn("Missing required stylesheet pipeline contract file", result.stderr)
            finally:
                stylesheet_path.write_text(original)

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

    def test_navigation_frame_tabs_and_tab_page_size_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            _site_path_2, _beta_space_root = self._bootstrap_site_space(tmp_root, "beta")
            (alpha_space_root / "subspaces.json").write_text(
                json.dumps(
                    {
                        "schema_version": "space_subspaces_v1",
                        "subspaces": [
                            {
                                "space_name": "beta",
                                "space_root": "../beta",
                                "title": "beta",
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

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
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            space_home = (alpha_space_root / "site" / "index.html").read_text()
            self.assertNotIn("class=\"site-sidebar\"", space_home)
            self.assertIn("class=\"site-root-menubar\"", space_home)
            self.assertIn("class=\"site-main site-space-main\"", space_home)
            self.assertIn("class=\"content-card\"", space_home)
            self.assertIn("class=\"top-search\"", space_home)
            self.assertIn("class=\"feed-list\"", space_home)
            self.assertIn('class="site-name site-home-link" href="../../../site/index.html">My Site</a>', space_home)
            self.assertIn('class="site-space-nav-summary current">Alpha</summary>', space_home)
            self.assertIn('class="site-space-nav-link site-space-nav-parent current" href="index.html">Alpha</a>', space_home)
            self.assertIn('href="../../beta/site/index.html">Beta</a>', space_home)
            self.assertNotIn('class="tabs"', space_home)
            self.assertIn('href="index.html">Home</a>', space_home)
            self.assertIn('href="overview/index.html" aria-label="Overview for alpha">Overview</a>', space_home)
            self.assertIn('href="sources/index.html">Sources</a>', space_home)
            self.assertIn('href="topics/index.html">Topics</a>', space_home)
            self.assertIn('href="users/index.html">Users</a>', space_home)
            self.assertIn('href="evidence/index.html">Evidence</a>', space_home)
            self.assertIn('href="claims/index.html">Claims</a>', space_home)
            self.assertNotIn('href="../../../site/sources/index.html">Sources</a>', space_home)
            self.assertTrue((alpha_space_root / "site" / "claims" / "index.html").is_file())
            overview_page = (alpha_space_root / "site" / "overview" / "index.html").read_text()
            self.assertIn("No overview has been generated for this space yet.", overview_page)
            self.assertIn(
                'class="site-tab current" href="index.html" aria-label="Overview for alpha">Overview</a>',
                overview_page,
            )

            sources_page_1 = (alpha_space_root / "site" / "sources" / "index.html").read_text()
            sources_page_2 = (alpha_space_root / "site" / "sources" / "page" / "2" / "index.html").read_text()
            self.assertIn("data-tab-page-size=\"50\"", sources_page_1)
            self.assertIn("Page size: 50", sources_page_1)
            self.assertIn("?tab_page=2", sources_page_1)
            self.assertNotIn("?feed_page=2", sources_page_1)
            page_1_feed = re.search(r"<ul class=\"feed-list\">(.*?)</ul>", sources_page_1, re.S)
            page_2_feed = re.search(r"<ul class=\"feed-list\">(.*?)</ul>", sources_page_2, re.S)
            self.assertIsNotNone(page_1_feed)
            self.assertIsNotNone(page_2_feed)
            assert page_1_feed is not None
            assert page_2_feed is not None
            self.assertEqual(len(re.findall(r'<li class=\"feed-card\">', page_1_feed.group(1))), 50)
            self.assertEqual(len(re.findall(r'<li class=\"feed-card\">', page_2_feed.group(1))), 1)
            self.assertIn("class=\"feed-card-title\"", page_1_feed.group(1))
            self.assertIn("class=\"feed-card-overview\"", page_1_feed.group(1))

            beta_home = (site_path / "spaces" / "beta" / "site" / "index.html").read_text()
            self.assertIn('class="site-space-nav-summary current">Alpha / Beta</summary>', beta_home)
            self.assertIn('class="site-space-nav-link current" href="index.html">Beta</a>', beta_home)
            self.assertIn('class="site-tab current" href="index.html">Home</a>', beta_home)
            self.assertIn('href="sources/index.html">Sources</a>', beta_home)
            self.assertNotIn('href="../../../site/topics/index.html">Topics</a>', beta_home)

    def test_parent_space_home_surfaces_subspaces_instead_of_empty_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, philosophy_root = self._bootstrap_site_space(tmp_root, "philosophy")
            self._run(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "mind"],
                check=True,
            )
            (philosophy_root / "subspaces.json").write_text(
                json.dumps(
                    {
                        "schema_version": "space_subspaces_v1",
                        "subspaces": [
                            {
                                "space_name": "mind",
                                "space_root": "../mind",
                                "title": "Mind",
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

            result = self._run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "philosophy",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            philosophy_home = (philosophy_root / "site" / "index.html").read_text()
            self.assertIn("<h2>Subspaces</h2>", philosophy_home)
            self.assertIn('href="../../mind/site/index.html">Mind</a>', philosophy_home)
            self.assertNotIn("<h2>Sources</h2>", philosophy_home)
            self.assertNotIn("<h2>Topics</h2>", philosophy_home)
            self.assertNotIn("<h2>Evidence</h2>", philosophy_home)
            self.assertNotIn("(none yet)", philosophy_home)

    def test_space_home_sources_and_topics_use_feed_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-preview-a",
                title="Source Preview A",
                summary="Source card overview text should render on the space home page.",
                authors=["Ada Lovelace", "Alan Turing"],
                source_file_rel="sources/artifacts/source-preview-a/source.pdf",
            )
            self._write_source_record(
                alpha_space_root,
                source_id="source-preview-b",
                title="Source Preview B",
                summary="Second source summary.",
                authors=["Grace Hopper"],
                source_file_rel="sources/artifacts/source-preview-b/source.pdf",
            )
            self._write_topic_record(
                alpha_space_root,
                topic_id="topic-space-home-card",
                title="Space Home Topic Card",
                source_ids=["source-preview-a"],
                sections=[
                    {
                        "heading": "Summary",
                        "body": "Topic card overview text should render on the space home page as well.",
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

            space_home = (alpha_space_root / "site" / "index.html").read_text()
            self.assertIn("<h2>Sources</h2>", space_home)
            self.assertIn("<h2>Topics</h2>", space_home)
            self.assertIn("class=\"feed-card\"", space_home)
            self.assertIn("class=\"feed-card-layout\"", space_home)
            self.assertIn("class=\"feed-card-head\"", space_home)
            self.assertIn("class=\"source-preview-feed\"", space_home)
            self.assertIn("Source card overview text should render on the space home page.", space_home)
            self.assertIn("Topic card overview text should render on the space home page as well.", space_home)
            self.assertIn("Authors:", space_home)
            self.assertIn("authors/author-ada-lovelace.html", space_home)
            self.assertIn("authors/author-alan-turing.html", space_home)
            self.assertIn("Space Home Topic Card", space_home)

    def test_space_topics_tab_uses_feed_cards_with_overview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-topic-a",
                title="Source Topic A",
                summary="A",
                authors=["Ada Lovelace"],
                source_file_rel="sources/artifacts/source-topic-a/source.pdf",
            )
            self._write_topic_record(
                alpha_space_root,
                topic_id="topic-tab-card",
                title="Topic Tab Card",
                source_ids=["source-topic-a"],
                sections=[
                    {
                        "heading": "Summary",
                        "body": "Topic tab overview text should render in a feed card, not as a bare row.",
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

            topics_page = (alpha_space_root / "site" / "topics" / "index.html").read_text()
            self.assertIn("class=\"feed-card\"", topics_page)
            self.assertIn("class=\"feed-card-layout\"", topics_page)
            self.assertIn("class=\"feed-card-head\"", topics_page)
            self.assertIn("class=\"feed-card-overview\"", topics_page)
            self.assertIn("Topic Tab Card", topics_page)
            self.assertIn("Topic tab overview text should render in a feed card, not as a bare row.", topics_page)

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

            site_root_index = (site_path / "site" / "index.html").read_text()
            self.assertIn("<h2>Latest Across Spaces</h2>", site_root_index)
            self.assertIn("class=\"feed-card\"", site_root_index)
            self.assertIn("href=\"new/index.html\">Open full New feed</a>", site_root_index)
            self.assertIn(alpha_latest_href, site_root_index)
            self.assertIn(beta_latest_href, site_root_index)
            self.assertLess(site_root_index.index(alpha_latest_href), site_root_index.index(beta_latest_href))

    def test_cross_page_search_control_and_index_consistency_across_page_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(space_root, source_id="source-search-a", title="Search Source A")
            self._write_topic_record(
                space_root,
                topic_id="topic-search-a",
                title="Search Topic A",
                source_ids=["source-search-a"],
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

            pages_with_expected_action = {
                space_root / "site" / "index.html": "action=\"search/index.html\"",
                space_root / "site" / "sources" / "source-search-a.html": "action=\"../search/index.html\"",
                space_root / "site" / "topics" / "topic-search-a.html": "action=\"../search/index.html\"",
                space_root / "site" / "users" / "index.html": "action=\"../search/index.html\"",
                space_root / "site" / "search" / "index.html": "action=\"index.html\"",
            }
            for page_path, expected_action in pages_with_expected_action.items():
                page_text = page_path.read_text()
                self.assertIn(expected_action, page_text)
                self.assertEqual(page_text.count("class=\"top-search\""), 1)

            search_page = (space_root / "site" / "search" / "index.html").read_text()
            self.assertIn("source-search-a", search_page)
            self.assertIn("topic-search-a", search_page)
            self.assertIn("../sources/source-search-a.html", search_page)
            self.assertIn("../topics/topic-search-a.html", search_page)
            persona_rows = load_seeded_persona_catalog(repo_root=REPO_ROOT)
            self.assertGreater(len(persona_rows), 0)
            first_persona = persona_rows[0]
            first_persona_id = str(first_persona["persona_id"])
            first_display_name = str(first_persona.get("display_name") or "")
            self.assertIn(first_persona_id, search_page)
            self.assertIn(first_display_name, search_page)
            self.assertIn(f"../users/persona-{first_persona_id}.html", search_page)
            self.assertIn("URLSearchParams(window.location.search)", search_page)
            self.assertIn(f"{2 + len(persona_rows)} indexed item(s)", search_page)

    def test_ui_information_architecture_integration_snapshot_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._bootstrap_site_space(tmp_root, "beta")
            self._write_source_record(space_root, source_id="source-ui-a", title="UI Source A")
            self._write_topic_record(
                space_root,
                topic_id="topic-ui-a",
                title="UI Topic A",
                source_ids=["source-ui-a"],
            )

            command = [
                "python3",
                str(REPO_ROOT / "scripts" / "build_site.py"),
                "--registry-path",
                str(site_path / "spaces.toml"),
                "alpha",
            ]
            first = self._run(command)
            self.assertEqual(first.returncode, 0, msg=first.stderr)
            first_snapshot = self._capture_html_snapshot(site_path)

            second = self._run(command)
            self.assertEqual(second.returncode, 0, msg=second.stderr)
            second_snapshot = self._capture_html_snapshot(site_path)
            self.assertEqual(first_snapshot, second_snapshot)

            self.assertIn("spaces/alpha/site/search/index.html", second_snapshot)
            self.assertIn("site/new/index.html", second_snapshot)

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

    def test_slug_like_source_titles_do_not_fabricate_author_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-slug-title-authors",
                title="alive2-pldi21",
                display_title="Alive2: Bounded Translation Validation for LLVM",
                summary=(
                    "This source frames LLVM optimization checking as bounded refinement validation over an SMT "
                    "model and discusses deployability constraints."
                ),
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

            self.assertFalse((alpha_space_root / "site" / "authors" / "index.html").exists())
            self.assertFalse((alpha_space_root / "site" / "authors" / "author-alive2.html").exists())
            self.assertFalse((alpha_space_root / "site" / "authors" / "author-pldi21.html").exists())

            sources_index = (alpha_space_root / "site" / "sources" / "index.html").read_text()
            self.assertIn("Authors: unknown", sources_index)

    def test_source_detail_and_feed_rows_render_preview_assets_and_source_pdf_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            long_summary = (
                "Source summary appears near top and this feed card overview must remain fully visible "
                "without truncation so readers can evaluate the source context directly from the New page."
            )
            self._write_source_record(
                alpha_space_root,
                source_id="source-preview-b",
                title="Preview Source B",
                summary=long_summary,
                authors=["Ada Lovelace", "Alan Turing"],
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
            self.assertIn(long_summary, source_page)
            self.assertIn("class=\"source-hero\"", source_page)
            self.assertIn("class=\"source-hero-preview\"", source_page)
            self.assertIn("class=\"source-preview-link\"", source_page)
            self.assertIn("../../../../site/assets/source_previews/source-preview-b.svg", source_page)
            self.assertIn("../../sources/artifacts/source-preview-b/source.pdf", source_page)
            self.assertNotIn("source-preview-caption", source_page)
            self.assertNotIn("Front page preview", source_page)
            self.assertNotIn("Overview and Commentary", source_page)
            self.assertNotIn("What the Source Argues", source_page)
            self.assertNotIn("source_id:", source_page)

            site_new_page = (site_path / "site" / "new" / "index.html").read_text()
            self.assertIn("class=\"feed-card\"", site_new_page)
            self.assertIn("class=\"feed-card-layout\"", site_new_page)
            self.assertIn("class=\"feed-card-head\"", site_new_page)
            self.assertIn("Apr 12, 2026", site_new_page)
            self.assertIn("Authors:", site_new_page)
            self.assertIn("../../spaces/alpha/site/authors/author-ada-lovelace.html", site_new_page)
            self.assertIn("../../spaces/alpha/site/authors/author-alan-turing.html", site_new_page)
            self.assertIn(long_summary, site_new_page)
            self.assertNotIn("without truncation so readers can evaluate the source context dire...", site_new_page)
            self.assertIn("class=\"source-preview-feed\"", site_new_page)
            self.assertIn("../assets/source_previews/source-preview-b.svg", site_new_page)

            space_new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("class=\"feed-card\"", space_new_page)
            self.assertIn("class=\"feed-card-layout\"", space_new_page)
            self.assertIn("class=\"feed-card-head\"", space_new_page)
            self.assertIn("Apr 12, 2026", space_new_page)
            self.assertIn("Authors:", space_new_page)
            self.assertIn("../authors/author-ada-lovelace.html", space_new_page)
            self.assertIn("../authors/author-alan-turing.html", space_new_page)
            self.assertIn(long_summary, space_new_page)
            self.assertNotIn("without truncation so readers can evaluate the source context dire...", space_new_page)
            self.assertIn("class=\"source-preview-feed\"", space_new_page)
            self.assertIn("../../../../site/assets/source_previews/source-preview-b.svg", space_new_page)

    def test_new_feed_source_card_displays_publication_date_over_ingested_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-publication-date",
                title="Publication Date Source",
                ingested_at="2026-04-12T00:00:00Z",
                source_date="2018-07-01",
                summary="Date label in New feed should show publication date.",
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

            site_new_page = (site_path / "site" / "new" / "index.html").read_text()
            self.assertIn("Jul 01, 2018", site_new_page)
            self.assertNotIn("Apr 12, 2026", site_new_page)

            space_new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("Jul 01, 2018", space_new_page)
            self.assertNotIn("Apr 12, 2026", space_new_page)

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

    def test_root_site_subspace_rows_are_clickable_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, computer_science_root = self._bootstrap_site_space(tmp_root, "computer-science")
            self._run(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "compilers"],
                check=True,
            )

            (computer_science_root / "subspaces.json").write_text(
                json.dumps(
                    {
                        "schema_version": "space_subspaces_v1",
                        "subspaces": [
                            {
                                "space_name": "compilers",
                                "space_root": "../compilers",
                                "title": "Compilers",
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
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

            root_index = (site_path / "site" / "index.html").read_text()
            self.assertIn(
                'href="../spaces/compilers/site/index.html">Compilers (Compilers)</a>',
                root_index,
            )

    def test_root_site_header_uses_space_navigation_without_duplicate_site_h1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, computer_science_root = self._bootstrap_site_space(tmp_root, "computer-science")
            self._run(
                ["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), "compilers"],
                check=True,
            )
            self._write_source_record(
                computer_science_root,
                source_id="source-root-nav",
                title="Root Nav Source",
                display_title="Root Nav Source",
                summary="Summary for root navigation coverage.",
            )
            self._write_topic_record(
                computer_science_root,
                topic_id="topic-root-nav",
                title="Root Nav Topic",
                source_ids=["source-root-nav", "source-root-nav-2"],
                sections=[{"heading": "Summary", "body": "Cross-source root topic."}],
            )
            self._write_source_record(
                computer_science_root,
                source_id="source-root-nav-2",
                title="Root Nav Source 2",
                display_title="Root Nav Source 2",
                summary="Another source for topic coverage.",
            )
            (computer_science_root / "subspaces.json").write_text(
                json.dumps(
                    {
                        "schema_version": "space_subspaces_v1",
                        "subspaces": [
                            {
                                "space_name": "compilers",
                                "space_root": "../compilers",
                                "title": "Compilers",
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
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

            root_index = (site_path / "site" / "index.html").read_text()
            self.assertIn('class="site-root-menubar"', root_index)
            self.assertIn('class="content-card site-root-content-card"', root_index)
            self.assertIn('class="site-name site-home-link" href="index.html">My Site</a>', root_index)
            self.assertIn('class="site-space-nav"', root_index)
            self.assertIn('class="site-space-nav-summary">Computer Science</summary>', root_index)
            self.assertIn('class="site-space-nav-link site-space-nav-parent" href="../spaces/computer-science/site/index.html">Computer Science</a>', root_index)
            self.assertIn('href="../spaces/compilers/site/index.html">Compilers</a>', root_index)
            self.assertIn('href="new/index.html">New</a>', root_index)
            self.assertIn('href="sources/index.html">Sources</a>', root_index)
            self.assertIn('href="topics/index.html">Topics</a>', root_index)
            self.assertLess(root_index.index('href="new/index.html">New</a>'), root_index.index('href="index.html">Spaces</a>'))
            self.assertIn("document.addEventListener('pointerdown'", root_index)
            self.assertIn("item.removeAttribute('open')", root_index)
            self.assertNotIn("<h1>My Site</h1>", root_index)

            site_sources = (site_path / "site" / "sources" / "index.html").read_text()
            site_topics = (site_path / "site" / "topics" / "index.html").read_text()
            self.assertIn("/spaces/computer-science/site/sources/source-root-nav.html", site_sources)
            self.assertIn("/spaces/computer-science/site/topics/topic-root-nav.html", site_topics)
            self.assertIn('class="site-root-menubar"', site_sources)

    def test_feed_rows_reject_placeholder_author_names_from_summary_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-author-fallback",
                title="Author Fallback Source",
                display_title="Author Fallback Source",
                summary="The paper validates a new compiler pass with a grounded benchmark study.",
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

            root_index = (site_path / "site" / "index.html").read_text()
            self.assertIn("Authors: unknown", root_index)
            self.assertNotIn("Authors: The", root_index)

    def test_new_feed_topic_overview_uses_full_text_without_claim_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-topic-overview"
            source_id_2 = "source-topic-overview-2"
            topic_id = "topic-topic-overview"
            topic_body = (
                "This topic overview should remain fully visible on the card and should not be clipped "
                "with ellipsis when rendered in the New feed. [[claims:claim-a,claim-b]]"
            )
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Topic Overview Source",
                summary="Source text",
            )
            self._write_source_record(
                alpha_space_root,
                source_id=source_id_2,
                title="Topic Overview Source 2",
                summary="Source text 2",
            )
            self._write_topic_record(
                alpha_space_root,
                topic_id=topic_id,
                title="Topic Overview Title",
                source_ids=[source_id, source_id_2],
                sections=[{"heading": "Summary", "body": topic_body}],
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

            expected_text = (
                "This topic overview should remain fully visible on the card and should not be clipped "
                "with ellipsis when rendered in the New feed."
            )
            new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn(expected_text, new_page)
            self.assertNotIn("[[claims:", new_page)
            self.assertNotIn("with ellipsis when rendered in the New feed....", new_page)

    def test_new_feed_topics_require_two_sources_and_never_render_preview_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(alpha_space_root, source_id="source-a", title="Source A", summary="A")
            self._write_source_record(alpha_space_root, source_id="source-b", title="Source B", summary="B")
            self._write_topic_record(
                alpha_space_root,
                topic_id="topic-single-source",
                title="Topic Single Source",
                source_ids=["source-a"],
            )
            self._write_topic_record(
                alpha_space_root,
                topic_id="topic-two-sources",
                title="Topic Two Sources",
                source_ids=["source-a", "source-b"],
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

            new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            feed_list_match = re.search(r"<ul class=\"feed-list\">(.*?)</ul>", new_page, re.S)
            self.assertIsNotNone(feed_list_match)
            feed_rows = feed_list_match.group(1)
            self.assertIn("Topic Two Sources", feed_rows)
            self.assertNotIn("Topic Single Source", feed_rows)
            self.assertNotIn(
                "class=\"source-preview-feed-link\" href=\"../topics/topic-two-sources.html\"",
                feed_rows,
            )

    def test_new_feed_does_not_derive_title_from_reference_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-paper-lowres--aaaaaaaaaaaa",
                title="paper-lowres",
                display_title="Paper Lowres",
                references=[
                    {
                        "title": (
                            "<rdf:Description rdf:about=\"\" xmlns:pdf=' /'>"
                            "<pdf:Producer>GPL Ghostscript 10.00.0</pdf:Producer>"
                        )
                    },
                    {
                        "title": (
                            "<rdf:Description rdf:about=\"\" xmlns:dc=' /' dc:format='application/pdf'>"
                            "<dc:title><rdf:Alt><rdf:li xml:lang='x-default'>"
                            "Path Tracing of Signed Distance Function Grids"
                            "</rdf:li></rdf:Alt></dc:title>"
                        )
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

            new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn(">Paper Lowres<", new_page)
            self.assertNotIn("Path Tracing of Signed Distance Function Grids", new_page)
            self.assertNotIn("GPL Ghostscript", new_page)
            self.assertNotIn(">paper-lowres<", new_page)

    def test_source_feed_uses_no_overview_placeholder_when_summary_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-no-summary--aaaaaaaaaaaa",
                title="paper-lowres",
                display_title="Paper Lowres",
                references=[{"title": "Example reference title"}],
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

            sources_page = (alpha_space_root / "site" / "sources" / "index.html").read_text()
            self.assertIn(">No overview available.<", sources_page)
            self.assertNotIn("A richer dossier summary can be regenerated from the source text.", sources_page)

    def test_author_links_point_to_unique_author_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-author-a",
                title="Source Author A",
                summary="Alpha summary.",
                authors=["Ada Lovelace"],
            )
            self._write_source_record(
                alpha_space_root,
                source_id="source-author-b",
                title="Source Author B",
                summary="Beta summary.",
                authors=[" ada   lovelace "],
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

            new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("../authors/author-ada-lovelace.html", new_page)

            authors_dir = alpha_space_root / "site" / "authors"
            author_pages = sorted(path.name for path in authors_dir.glob("author-ada-lovelace*.html"))
            self.assertEqual(author_pages, ["author-ada-lovelace.html"])

            author_page = (authors_dir / "author-ada-lovelace.html").read_text()
            self.assertIn("Source Author A", author_page)
            self.assertIn("Source Author B", author_page)

    def test_author_identity_uses_name_plus_institution_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-inst-a",
                title="Source Inst A",
                summary="Institutional author A.",
                authors=[{"name": "Alex Kim", "institution": "Institute A"}],
            )
            self._write_source_record(
                alpha_space_root,
                source_id="source-inst-b",
                title="Source Inst B",
                summary="Institutional author B.",
                authors=[{"name": "Alex Kim", "institution": "Institute B"}],
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

            new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("../authors/author-alex-kim-institute-a.html", new_page)
            self.assertIn("../authors/author-alex-kim-institute-b.html", new_page)

            authors_dir = alpha_space_root / "site" / "authors"
            self.assertTrue((authors_dir / "author-alex-kim-institute-a.html").is_file())
            self.assertTrue((authors_dir / "author-alex-kim-institute-b.html").is_file())

    def test_source_detail_renders_explicit_source_dossier_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            self._write_source_record(
                alpha_space_root,
                source_id="source-dossier",
                title="Dossier Source",
                summary="Fallback summary",
                source_file_rel="sources/artifacts/source-dossier/source.pdf",
                source_dossier={
                    "summary_short": "Explicit short dossier summary for readers.",
                    "summary_long": (
                        "This explicit dossier is authored for source-page reading.\n\n"
                        "It should appear ahead of fallback-generated prose."
                    ),
                    "sections": [
                        {
                            "heading": "What the Source Argues",
                            "body": "The source advances an explicit thesis.",
                            "grounding_claim_ids": [],
                        },
                        {
                            "heading": "How the Argument Is Built",
                            "body": "The reasoning sequence is mapped to extracted evidence.",
                            "grounding_claim_ids": [],
                        },
                        {
                            "heading": "What to Scrutinize",
                            "body": "Readers should check assumptions and transfer limits.",
                            "grounding_claim_ids": [],
                        },
                    ],
                },
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

            source_page = (alpha_space_root / "site" / "sources" / "source-dossier.html").read_text()
            self.assertIn("Overview and Commentary", source_page)
            self.assertIn("Explicit short dossier summary for readers.", source_page)
            self.assertIn("This explicit dossier is authored for source-page reading.", source_page)
            self.assertIn("What to Scrutinize", source_page)

    def test_source_detail_renders_revision_history_for_source_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            family_id = "source-family-revision-history"
            original_id = "source-revision-original--aaaaaaaaaaaa"
            update_id = "source-revision-update--bbbbbbbbbbbb"
            self._write_source_record(
                alpha_space_root,
                source_id=original_id,
                title="Revision Study Original",
                ingested_at="2026-04-10T00:00:00Z",
                source_family_id=family_id,
                source_revision={
                    "source_family_id": family_id,
                    "revision_index": 1,
                    "is_latest": False,
                    "supersedes_source_id": None,
                    "superseded_by_source_id": update_id,
                },
            )
            self._write_source_record(
                alpha_space_root,
                source_id=update_id,
                title="Revision Study Updated",
                ingested_at="2026-04-11T00:00:00Z",
                source_family_id=family_id,
                source_revision={
                    "source_family_id": family_id,
                    "revision_index": 2,
                    "is_latest": True,
                    "supersedes_source_id": original_id,
                    "superseded_by_source_id": None,
                },
            )
            self._write_source_record(
                alpha_space_root,
                source_id="source-singleton--cccccccccccc",
                title="Singleton Source",
                source_family_id="source-family-singleton",
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

            update_page = (alpha_space_root / "site" / "sources" / f"{update_id}.html").read_text()
            self.assertIn("Revisions", update_page)
            self.assertIn(f"../sources/{original_id}.html", update_page)
            self.assertIn(f"../sources/{update_id}.html", update_page)
            self.assertIn("Current", update_page)
            self.assertIn("Latest", update_page)
            self.assertLess(update_page.index("Revision 1"), update_page.index("Revision 2"))

            singleton_page = (
                alpha_space_root / "site" / "sources" / "source-singleton--cccccccccccc.html"
            ).read_text()
            self.assertNotIn("source-revisions-card", singleton_page)

    def test_source_claim_list_uses_human_claim_titles_not_reference_counters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-claim-labels"
            claim_id = "claim-claim-labels--aaaaaaaaaaaa"
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Source Claim Labels",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id,
                source_id=source_id,
                text="The paper claims that preparation independence constrains epistemic overlap regions.",
                short_title="Preparation independence constrains overlap",
            )
            self._write_topic_record(
                alpha_space_root,
                topic_id="topic-claim-labels--aaaaaaaaaaaa",
                title="Topic Claim Labels",
                source_ids=[source_id],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"Mapped claim sentence. [[claims:{claim_id}]]",
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

            source_page = (alpha_space_root / "site" / "sources" / f"{source_id}.html").read_text()
            self.assertIn("Claims Referencing This Source", source_page)
            self.assertIn(
                f"<a href=\"../claims/{claim_id}.html\">Preparation independence constrains overlap</a>",
                source_page,
            )
            self.assertNotIn(
                f"<a class=\"sentence-claim-link\" href=\"../claims/{claim_id}.html\">",
                source_page,
            )
            self.assertNotIn("class=\"source-dossier-claims\"", source_page)
            self.assertNotIn("Claim reference 1", source_page)
            self.assertNotIn("Claim reference ", source_page)
            self.assertNotIn(">Claim 1</a>", source_page)

    def test_source_claim_list_includes_direct_source_claims_without_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-direct-claims"
            claim_id = "claim-direct-claims--aaaaaaaaaaaa"
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Source Direct Claims",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id,
                source_id=source_id,
                text="Register-pressure spikes are concentrated in post-SSA lowering blocks.",
                short_title="Pressure spikes cluster post-SSA",
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

            source_page = (alpha_space_root / "site" / "sources" / f"{source_id}.html").read_text()
            self.assertIn("Claims Referencing This Source", source_page)
            self.assertIn(
                f"<a href=\"../claims/{claim_id}.html\">Pressure spikes cluster post-SSA</a>",
                source_page,
            )

    def test_source_page_surfaces_richer_metadata_and_explanatory_related_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-rich-metadata"
            claim_id = "claim-rich-metadata--aaaaaaaaaaaa"
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Source Rich Metadata",
                source_date="2024-03-14",
                citation_count=321,
                authors=["Ada Lovelace", "Alan Turing"],
                source_file_rel="sources/artifacts/source-rich-metadata/source.pdf",
                source_semantic={
                    "institution": "University of Example",
                    "doi": "10.1234/example.doi",
                },
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id,
                source_id=source_id,
                text="Height maps guide avatars around obstacles before local collision handling refines the final motion.",
                short_title="Height maps steer crowds",
            )
            self._write_evidence_record(
                alpha_space_root,
                evidence_id="evidence-rich-metadata--aaaaaaaaaaaa",
                title="Navigation grid evidence",
                excerpt="The excerpt records the raw navigation-grid setup and resulting motion traces.",
                overview="The evidence supports the claim by showing that coarse height-map routing handles the first pass of crowd movement before finer corrections.",
                evidence_type="excerpt",
                source_id=source_id,
                claim_ids=[claim_id],
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

            source_page = (alpha_space_root / "site" / "sources" / f"{source_id}.html").read_text()
            self.assertIn("Source Details", source_page)
            self.assertIn("Authors", source_page)
            self.assertIn("../authors/author-ada-lovelace", source_page)
            self.assertIn("../authors/author-alan-turing", source_page)
            self.assertIn("Institution", source_page)
            self.assertIn("University of Example", source_page)
            self.assertIn("Publication date", source_page)
            self.assertIn("2024-03-14", source_page)
            self.assertIn("Citations", source_page)
            self.assertIn("321", source_page)
            self.assertIn("10.1234/example.doi", source_page)
            self.assertIn("Claims Referencing This Source", source_page)
            self.assertIn("Height maps guide avatars around obstacles before local collision handling refines the final motion.", source_page)
            self.assertIn("Evidence from This Source", source_page)
            self.assertIn("The evidence supports the claim by showing that coarse height-map routing handles the first pass of crowd movement before finer corrections.", source_page)

    def test_source_topic_and_claim_pages_render_external_related_links_and_analysis_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-related-links"
            claim_id = "claim-related-links--aaaaaaaaaaaa"
            topic_id = "topic-related-links--aaaaaaaaaaaa"
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Related Links Source",
                display_title="Related Links Source",
                summary="Source summary for related-link rendering coverage.",
                source_file_rel=f"sources/artifacts/{source_id}/source.pdf",
                source_semantic={"doi": "10.1111/example.related"},
                source_extraction={
                    "converter_name": "markitdown",
                    "converter_version": "0.1.0",
                    "status": "success",
                    "quality_status": "usable",
                    "warnings": ["Inspect the original PDF for table layouts."],
                },
                analysis_policy={
                    "preferred_artifact": "source_markdown",
                    "fallback_artifacts": ["source_file"],
                    "quality_status": "usable",
                    "warnings": ["Inspect the original PDF for table layouts."],
                },
                external_related_links=[
                    {
                        "title": "Wikipedia overview",
                        "url": "https://en.wikipedia.org/wiki/Formal_system",
                        "domain": "en.wikipedia.org",
                        "link_type": "encyclopedia",
                        "quality_status": "trusted",
                        "confidence": "medium",
                        "rationale": "Captured from normalized source references.",
                        "provenance": {"origin": "reference_url", "source_field": "references[0].url"},
                    },
                    {
                        "title": "Logic discussion thread",
                        "url": "https://www.reddit.com/r/logic/comments/example/",
                        "domain": "www.reddit.com",
                        "link_type": "discussion_forum",
                        "quality_status": "contextual",
                        "confidence": "medium",
                        "rationale": "Captured from normalized source references.",
                        "provenance": {"origin": "reference_url", "source_field": "references[1].url"},
                    },
                ],
                related_link_enrichment={
                    "status": "enriched",
                    "warnings": [],
                    "sources": ["references"],
                    "skip_reason": None,
                },
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id,
                source_id=source_id,
                text="Formal systems expose the difference between symbolic rules and semantic interpretation.",
                short_title="Formal systems differ",
            )
            self._write_topic_record(
                alpha_space_root,
                topic_id=topic_id,
                title="Formal Systems Topic",
                source_ids=[source_id],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"Topic discussion with an anchored claim reference. [[claims:{claim_id}]]",
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

            source_page = (alpha_space_root / "site" / "sources" / f"{source_id}.html").read_text()
            topic_page = (alpha_space_root / "site" / "topics" / f"{topic_id}.html").read_text()
            claim_page = (alpha_space_root / "site" / "claims" / f"{claim_id}.html").read_text()

            self.assertIn("Analysis Inputs", source_page)
            self.assertIn("source.md", source_page)
            self.assertIn("source_extraction.json", source_page)
            self.assertIn("Markdown quality", source_page)
            self.assertIn("markitdown (0.1.0)", source_page)
            self.assertIn("External Related Links", source_page)
            self.assertIn("Wikipedia overview", source_page)
            self.assertIn("Logic discussion thread", source_page)
            self.assertIn("from reference url", source_page)

            self.assertIn("External Related Links", topic_page)
            self.assertIn("Wikipedia overview", topic_page)
            self.assertIn(f"../sources/{source_id}.html", topic_page)
            self.assertIn("via <a href=\"../sources/", topic_page)

            self.assertIn("External Related Links", claim_page)
            self.assertIn("Logic discussion thread", claim_page)
            self.assertIn(f"../sources/{source_id}.html", claim_page)

    def test_space_and_subspace_homepages_render_overview_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            _site_path_2, beta_space_root = self._bootstrap_site_space(tmp_root, "beta")
            (alpha_space_root / "subspaces.json").write_text(
                json.dumps(
                    {
                        "schema_version": "space_subspaces_v1",
                        "subspaces": [
                            {
                                "space_name": "beta",
                                "space_root": "../beta",
                                "title": "Beta Research Cell",
                            }
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

            source_id = "source-overview--aaaaaaaaaaaa"
            claim_id = "claim-overview--bbbbbbbbbbbb"
            self._write_source_record(alpha_space_root, source_id=source_id, title="Alpha Source")
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id,
                source_id=source_id,
                text="Alpha claim text.",
                short_title="Alpha claim",
            )
            self._write_overview_artifact(
                alpha_space_root,
                overview_id="space--alpha",
                space_name="alpha",
                scope_kind="space",
                title="State of the Evidence in alpha",
                summary="Alpha overview summary for the landing page.",
                source_ids=[source_id],
                claim_ids=[claim_id],
                citation_anchors=[
                    {
                        "anchor_id": "anchor-alpha-summary",
                        "label": "Alpha anchor",
                        "source_id": source_id,
                        "claim_ids": [claim_id],
                        "locator": "p. 2",
                    }
                ],
                warnings=["Inspect the original PDF for tables."],
            )

            beta_source_id = "source-beta--cccccccccccc"
            beta_claim_id = "claim-beta--dddddddddddd"
            self._write_source_record(beta_space_root, source_id=beta_source_id, title="Beta Source")
            self._write_claim_record(
                beta_space_root,
                claim_id=beta_claim_id,
                source_id=beta_source_id,
                text="Beta claim text.",
                short_title="Beta claim",
            )
            self._write_overview_artifact(
                beta_space_root,
                overview_id="subspace--beta",
                space_name="beta",
                scope_kind="subspace",
                title="State of the Evidence in beta",
                summary="Beta overview summary for the landing page.",
                source_ids=[beta_source_id],
                claim_ids=[beta_claim_id],
                citation_anchors=[
                    {
                        "anchor_id": "anchor-beta-summary",
                        "label": "Beta anchor",
                        "source_id": beta_source_id,
                        "claim_ids": [beta_claim_id],
                        "locator": "sec. 4",
                    }
                ],
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

            alpha_home = (alpha_space_root / "site" / "index.html").read_text()
            alpha_overview = (alpha_space_root / "site" / "overview" / "index.html").read_text()
            beta_home = (beta_space_root / "site" / "index.html").read_text()
            beta_overview = (beta_space_root / "site" / "overview" / "index.html").read_text()

            self.assertIn("Alpha overview summary for the landing page.", alpha_home)
            self.assertIn(
                'href="overview/index.html" aria-label="Open full overview for Alpha">Open full overview</a>',
                alpha_home,
            )
            self.assertIn("State of the Evidence in alpha", alpha_overview)
            self.assertIn("Inspect the original PDF for tables.", alpha_overview)
            self.assertIn("../sources/source-overview--aaaaaaaaaaaa.html", alpha_overview)
            self.assertIn("../claims/claim-overview--bbbbbbbbbbbb.html", alpha_overview)
            self.assertIn("Alpha anchor (p. 2)", alpha_overview)

            self.assertIn("Beta overview summary for the landing page.", beta_home)
            self.assertIn("State of the Evidence in beta", beta_overview)
            self.assertIn("Scope: subspace", beta_overview)
            self.assertIn("../sources/source-beta--cccccccccccc.html", beta_overview)

    def test_source_dossier_numeric_claim_refs_resolve_to_canonical_claim_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-dossier-numeric-claims"
            claim_id_0 = "claim-prep-independence--aaaaaaaaaaaa"
            claim_id_1 = "claim-noise-bound--bbbbbbbbbbbb"
            claim_id_2 = "claim-collapse-consequence--cccccccccccc"
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Source Dossier Numeric Claims",
                source_dossier={
                    "summary_short": "Short summary",
                    "summary_long": "Long summary paragraph.",
                    "sections": [
                        {
                            "heading": "Preparation assumptions",
                            "body": "Preparation independence blocks epistemic overlap contradictions.",
                            "grounding_claim_ids": ["0"],
                        },
                        {
                            "heading": "Noise-robust implication",
                            "body": "A noise-tolerant bound still forces near-disjoint ontic distributions.",
                            "grounding_claim_ids": ["1"],
                        },
                        {
                            "heading": "Interpretive result",
                            "body": "Real-wavefunction readings imply collapse or branching ontology.",
                            "grounding_claim_ids": ["2"],
                        },
                    ],
                },
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id_0,
                source_id=source_id,
                text=(
                    "Preparation independence blocks psi-epistemic overlap by making shared ontic states "
                    "incompatible with predicted outcomes."
                ),
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id_1,
                source_id=source_id,
                text=(
                    "Noise-tolerant overlap bounds still imply near-disjoint ontic distributions for distinct "
                    "quantum states."
                ),
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id_2,
                source_id=source_id,
                text=(
                    "If the wavefunction is physically real, collapse or branching ontology follows under the "
                    "paper's assumptions."
                ),
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

            source_page = (alpha_space_root / "site" / "sources" / f"{source_id}.html").read_text()
            self.assertNotIn("href=\"../claims/0.html\"", source_page)
            self.assertNotIn("href=\"../claims/1.html\"", source_page)
            self.assertNotIn("href=\"../claims/2.html\"", source_page)
            self.assertIn(f"href=\"../claims/{claim_id_0}.html\"", source_page)
            self.assertIn(f"href=\"../claims/{claim_id_1}.html\"", source_page)
            self.assertIn(f"href=\"../claims/{claim_id_2}.html\"", source_page)

    def test_claim_index_and_detail_use_short_claim_titles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-claim-title-index"
            claim_id = "claim-title-index--aaaaaaaaaaaa"
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Source Claim Title Index",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id,
                source_id=source_id,
                text="The paper claims that preparation independence constrains epistemic overlap regions.",
            )
            topic_id = "topic-claim-title-index--aaaaaaaaaaaa"
            self._write_topic_record(
                alpha_space_root,
                topic_id=topic_id,
                title="Topic Claim Title Index",
                source_ids=[source_id],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"A linked sentence. [[claims:{claim_id}]]",
                    }
                ],
            )
            self._write_topic_record(
                alpha_space_root,
                topic_id="topic-claim-title-index-second--aaaaaaaaaaaa",
                title="Topic Claim Title Index Second",
                source_ids=[source_id],
                sections=[
                    {
                        "heading": "Summary",
                        "body": f"Another linked sentence. [[claims:{claim_id}]]",
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

            claims_index = (alpha_space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn(
                (
                    f"<a href=\"{claim_id}.html\">"
                    "The paper claims that preparation independence constrains epistemic overlap regions"
                    "</a>"
                ),
                claims_index,
            )
            self.assertIn("<p class=\"meta\">added: ", claims_index)
            self.assertNotIn("<p class=\"meta\">score: ", claims_index)
            self.assertNotIn("class=\"claim-score-value claim-score-", claims_index)
            self.assertNotIn(f"{claim_id} | score:", claims_index)
            self.assertIn("class=\"claim-card-usage-list claim-card-usage-list-primary\"", claims_index)
            self.assertIn("class=\"claim-card-usage-list claim-card-usage-list-overflow\"", claims_index)
            self.assertIn(f"href=\"../topics/{topic_id}.html\"", claims_index)
            self.assertIn(f"href=\"../sources/{source_id}.html\"", claims_index)
            self.assertIn("class=\"claim-usage-chip claim-usage-chip-topic\"", claims_index)
            self.assertIn("class=\"claim-usage-chip claim-usage-chip-source\"", claims_index)
            self.assertNotIn("class=\"claim-card-usage-label\"", claims_index)
            self.assertRegex(claims_index, r'<a class=\"site-tab current\" href=\"[^\"]*\">Claims</a>')

            claim_page = (alpha_space_root / "site" / "claims" / f"{claim_id}.html").read_text()
            self.assertIn(
                (
                    "<h1>"
                    "The paper claims that preparation independence constrains epistemic overlap regions"
                    "</h1>"
                ),
                claim_page,
            )
            self.assertIn(
                "<p>The paper claims that preparation independence constrains epistemic overlap regions.</p>",
                claim_page,
            )
            self.assertRegex(claim_page, r'<a class=\"site-tab current\" href=\"[^\"]*\">Claims</a>')

    def test_claim_titles_preserve_curated_short_title_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            source_id = "source-claim-title-verbatim"
            claim_id = "claim-title-verbatim--aaaaaaaaaaaa"
            short_title = "Decoherence makes observables stable"
            self._write_source_record(
                alpha_space_root,
                source_id=source_id,
                title="Source Claim Title Verbatim",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=claim_id,
                source_id=source_id,
                text=(
                    "Decoherence stabilizes those agent-specified observables, yielding facts that are stable "
                    "for us without positing an absolute observer-independent basis."
                ),
                short_title=short_title,
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

            claims_index = (alpha_space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn(f"<a href=\"{claim_id}.html\">{short_title}</a>", claims_index)
            self.assertNotIn("Decoherence makes observables is stable", claims_index)

            claim_page = (alpha_space_root / "site" / "claims" / f"{claim_id}.html").read_text()
            self.assertIn(f"<h1>{short_title}</h1>", claim_page)
            self.assertNotIn("<h1>Decoherence makes observables is stable</h1>", claim_page)

    def test_claim_index_score_ranking_includes_citation_count_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            high_source_id = "source-high-citation"
            low_source_id = "source-low-citation"
            high_claim_id = "claim-high-citation-rank--aaaaaaaaaaaa"
            low_claim_id = "claim-low-citation-rank--aaaaaaaaaaaa"
            self._write_source_record(
                alpha_space_root,
                source_id=high_source_id,
                title="High Citation Source",
                citation_count=2000,
            )
            self._write_source_record(
                alpha_space_root,
                source_id=low_source_id,
                title="Low Citation Source",
                citation_count=10,
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=high_claim_id,
                source_id=high_source_id,
                text="High citation claim statement.",
                short_title="High citation claim",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id=low_claim_id,
                source_id=low_source_id,
                text="Low citation claim statement.",
                short_title="Low citation claim",
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

            claims_index = (alpha_space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn(f"<a href=\"{high_claim_id}.html\">High citation claim</a>", claims_index)
            self.assertIn(f"<a href=\"{low_claim_id}.html\">Low citation claim</a>", claims_index)
            high_match = re.search(
                rf'data-claim-id="{re.escape(high_claim_id)}".*?data-claim-score="(\d+)"',
                claims_index,
            )
            low_match = re.search(
                rf'data-claim-id="{re.escape(low_claim_id)}".*?data-claim-score="(\d+)"',
                claims_index,
            )
            self.assertIsNotNone(high_match)
            self.assertIsNotNone(low_match)
            assert high_match is not None
            assert low_match is not None
            self.assertGreater(int(high_match.group(1)), int(low_match.group(1)))

    def test_claim_index_newness_prefers_claim_added_at_then_source_ingested_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            older_source_id = "source-older"
            newer_source_id = "source-newer"
            self._write_source_record(
                alpha_space_root,
                source_id=older_source_id,
                title="Older Source",
                ingested_at="2026-01-01T00:00:00Z",
            )
            self._write_source_record(
                alpha_space_root,
                source_id=newer_source_id,
                title="Newer Source",
                ingested_at="2026-03-01T00:00:00Z",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id="claim-added-fallback-old--aaaaaaaaaaaa",
                source_id=older_source_id,
                text="Old fallback claim statement.",
                short_title="Old fallback claim",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id="claim-added-explicit-new--aaaaaaaaaaaa",
                source_id=older_source_id,
                text="Explicit newer claim statement.",
                short_title="Explicit newer claim",
                added_at="2026-04-10T12:00:00Z",
            )
            self._write_claim_record(
                alpha_space_root,
                claim_id="claim-added-fallback-newer-source--aaaaaaaaaaaa",
                source_id=newer_source_id,
                text="Source fallback newer claim statement.",
                short_title="Source fallback newer claim",
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

            claims_index = (alpha_space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn('data-claim-id="claim-added-fallback-old--aaaaaaaaaaaa"', claims_index)
            self.assertIn('data-claim-id="claim-added-explicit-new--aaaaaaaaaaaa"', claims_index)
            self.assertIn('data-claim-id="claim-added-fallback-newer-source--aaaaaaaaaaaa"', claims_index)
            self.assertIn(
                'data-claim-id="claim-added-fallback-old--aaaaaaaaaaaa" data-claim-title="old fallback claim" '
                'data-claim-score="',
                claims_index,
            )
            self.assertIn('data-claim-added-at="2026-01-01T00:00:00Z"', claims_index)
            self.assertIn('data-claim-added-at="2026-04-10T12:00:00Z"', claims_index)
            self.assertIn('data-claim-added-at="2026-03-01T00:00:00Z"', claims_index)
            self.assertIn("added: Jan 01, 2026", claims_index)
            self.assertIn("added: Mar 01, 2026", claims_index)
            self.assertIn("added: Apr 10, 2026", claims_index)
            self.assertNotIn("UTC", claims_index)

    def test_source_preview_prefers_ingested_front_page_image_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            front_page_rel = "sources/artifacts/source-preview-photo/front_page.png"
            front_page_path = alpha_space_root / front_page_rel
            front_page_bytes = b"front-page-image-bytes"
            front_page_path.parent.mkdir(parents=True, exist_ok=True)
            front_page_path.write_bytes(front_page_bytes)
            self._write_source_record(
                alpha_space_root,
                source_id="source-preview-photo",
                title="Preview Source Photo",
                summary="Preview should use ingested first-page screenshot.",
                source_file_rel="sources/artifacts/source-preview-photo/source.pdf",
                front_page_image_rel=front_page_rel,
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

            copied_preview_path = site_path / "site" / "assets" / "source_previews" / "source-preview-photo.png"
            self.assertTrue(copied_preview_path.is_file())
            self.assertEqual(copied_preview_path.read_bytes(), front_page_bytes)

            source_page = (alpha_space_root / "site" / "sources" / "source-preview-photo.html").read_text()
            self.assertIn("../../../../site/assets/source_previews/source-preview-photo.png", source_page)
            self.assertNotIn("../../../../site/assets/source_previews/source-preview-photo.svg", source_page)

            site_new_page = (site_path / "site" / "new" / "index.html").read_text()
            self.assertIn("../assets/source_previews/source-preview-photo.png", site_new_page)
            self.assertIn("aria-label=\"Open source: Preview Source Photo\"", site_new_page)

            space_new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("../../../../site/assets/source_previews/source-preview-photo.png", space_new_page)
            self.assertIn("aria-label=\"Open source: Preview Source Photo\"", space_new_page)

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
                            "persona_id": "persona-maya-santoro",
                            "display_name": "Maya Santoro",
                            "full_name": "Maya Santoro",
                            "account_status": "active",
                            "stance_profile": "neutral",
                            "biography": (
                                "I test claims by examining assumptions, evidence quality, and practical "
                                "tradeoffs before I decide whether a proposal is trustworthy. I map failure "
                                "modes, clarify who owns each mitigation, and check whether teams can detect "
                                "and recover from routine incidents under pressure. I value transparent "
                                "reasoning, explicit uncertainty, and implementation plans with measurable "
                                "checkpoints. I push back when summaries replace primary evidence or when "
                                "important caveats are hidden behind confident language. I communicate "
                                "directly, cite sources, and revise quickly when stronger data changes the "
                                "expected outcome. I also document alternatives and residual risk so collaborators "
                                "can audit and improve decisions together."
                            ),
                            "biography_profile": (
                                "I am a practical evidence reviewer known for translating complex arguments "
                                "into clear decisions. I emphasize reliability, transparent tradeoffs, and "
                                "steady communication under operational pressure."
                            ),
                            "interests": ["risk management"],
                            "hot_topics": ["operational readiness"],
                            "anger_topics": ["misleading claims"],
                            "profile_image_path": "personas/profile_images/maya-santoro.jpg",
                            "profile_image_prompt": (
                                "Photorealistic portrait photo of this person at home in a study, natural "
                                "window light, calm expression, realistic skin detail, documentary style."
                            ),
                            "short_cv": [
                                "Operations Advisor, Example Systems (2022-present)",
                                "SRE Manager, Example Infra (2018-2022)",
                                "MSc, Reliability Engineering, Example University (2016-2018)",
                            ],
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
                self.assertNotIn(alpha_profile_href, site_users_page)
                self.assertNotIn(beta_profile_href, site_users_page)
                self.assertIn("class=\"user-card-grid\"", site_users_page)
                self.assertIn("class=\"user-card site-user-card\"", site_users_page)
                self.assertIn("class=\"user-card-photo\"", site_users_page)
                self.assertIn("class=\"user-card-name\"", site_users_page)
                self.assertNotIn("class=\"site-user-card-id\"", site_users_page)
                self.assertNotIn("user-card-scopes", site_users_page)
                self.assertNotIn(f">{persona_id}<", site_users_page)

                alpha_users_page = (alpha_space_root / "site" / "users" / "index.html").read_text()
                self.assertIn(f"href=\"persona-{persona_id}.html\"", alpha_users_page)
                self.assertNotIn(f"/beta/site/users/persona-{persona_id}.html", alpha_users_page)
                self.assertIn("class=\"user-card-grid\"", alpha_users_page)
                self.assertIn("class=\"user-card\"", alpha_users_page)
                self.assertIn("class=\"user-card-photo\"", alpha_users_page)
                self.assertIn("class=\"user-card-name\"", alpha_users_page)
                self.assertIn(f"assets/persona_profiles/{persona_id}.jpg", alpha_users_page)

                alpha_profile_page = alpha_space_root / "site" / "users" / f"persona-{persona_id}.html"
                self.assertTrue(alpha_profile_page.is_file())
                alpha_profile_html = alpha_profile_page.read_text()
                self.assertNotIn("full_name:", alpha_profile_html)
                self.assertNotIn("persona_id:", alpha_profile_html)
                self.assertNotIn("Space-scoped profile page for this persona.", alpha_profile_html)
                self.assertIn("class=\"profile-biography\"", alpha_profile_html)
                self.assertIn("class=\"profile-biography-copy\"", alpha_profile_html)
                self.assertIn("class=\"profile-photo\"", alpha_profile_html)
                self.assertIn("class=\"profile-cv\"", alpha_profile_html)
                self.assertIn("class=\"profile-cv-list\"", alpha_profile_html)
                self.assertIn("class=\"profile-cv-item\"", alpha_profile_html)
                self.assertIn("class=\"profile-cv-role\">Operations Advisor</p>", alpha_profile_html)
                self.assertIn("class=\"profile-cv-org\">Example Systems</p>", alpha_profile_html)
                self.assertIn("class=\"profile-cv-period\">2022-present</span>", alpha_profile_html)
                self.assertLess(
                    alpha_profile_html.index("class=\"profile-biography-copy\""),
                    alpha_profile_html.index("class=\"profile-photo-frame\""),
                )
                self.assertIn(f"assets/persona_profiles/{persona_id}.jpg", alpha_profile_html)
                self.assertIn("Biography", alpha_profile_html)
                self.assertIn("Short CV", alpha_profile_html)
                self.assertIn("I am a practical evidence reviewer", alpha_profile_html)
                self.assertIn("Operations Advisor</p><p class=\"profile-cv-org\">Example Systems", alpha_profile_html)
                self.assertIn("<title>Alpha - Maya Santoro</title>", alpha_profile_html)
                alpha_profile_photo_path = (
                    alpha_space_root / "site" / "assets" / "persona_profiles" / f"{persona_id}.jpg"
                )
                self.assertTrue(alpha_profile_photo_path.is_file())
                alpha_avatar_path = (
                    alpha_space_root / "site" / "assets" / "persona_avatars" / f"{persona_id}.jpg"
                )
                self.assertTrue(alpha_avatar_path.is_file())
            finally:
                catalog_path.write_text(original_catalog)

    def test_user_profile_pages_use_full_res_photo_and_comments_keep_thumbnail_avatar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            catalog_path = REPO_ROOT / "personas" / "social_users.json"
            profile_images_root = REPO_ROOT / "personas" / "profile_images"
            original_catalog = catalog_path.read_text()
            full_res_path = profile_images_root / "test-photo-user.jpg"
            thumb_path = profile_images_root / "test-photo-user-thumb.jpg"
            full_res_original = full_res_path.read_bytes() if full_res_path.exists() else None
            thumb_original = thumb_path.read_bytes() if thumb_path.exists() else None
            try:
                full_res_bytes = b"high-res-photo-bytes"
                thumb_bytes = b"thumb-photo-bytes"
                full_res_path.write_bytes(full_res_bytes)
                thumb_path.write_bytes(thumb_bytes)

                seeded_catalog = {
                    "schema_version": "social_users_v1",
                    "count": 1,
                    "users": [
                        {
                            "persona_id": "persona-test-photo-user",
                            "display_name": "Test Photo User",
                            "full_name": "Test Photo User",
                            "account_status": "active",
                            "stance_profile": "neutral",
                            "biography": (
                                "I assess technical claims by inspecting assumptions, tracing evidence to primary "
                                "records, and documenting tradeoffs that affect reliability. I prioritize "
                                "decision quality, operational realism, and explicit uncertainty handling in every "
                                "review I produce. I map failure modes, verify mitigation ownership, and test "
                                "whether teams can detect and recover from common incidents without improvisation. "
                                "I challenge conclusions that skip caveats, exaggerate confidence, or hide "
                                "material limitations behind polished language. I communicate directly, cite "
                                "sources, and revise quickly when stronger evidence changes expected outcomes. I "
                                "also record alternatives and residual risk so collaborators can audit the logic, "
                                "compare options, and improve follow-through over time."
                            ),
                            "biography_profile": (
                                "I am a practical reviewer focused on reliability, clear tradeoffs, and evidence "
                                "that can withstand scrutiny. I value direct communication, measurable plans, and "
                                "documented residual risk so teams can make better decisions under pressure."
                            ),
                            "interests": ["risk management"],
                            "hot_topics": ["operational readiness"],
                            "anger_topics": ["misleading claims"],
                            "profile_image_path": "personas/profile_images/test-photo-user.jpg",
                            "profile_image_prompt": (
                                "Photorealistic portrait photo of this person in a home office, natural window "
                                "light, realistic skin detail, documentary style, single person subject."
                            ),
                            "short_cv": [
                                "Operations Advisor, Example Systems (2022-present)",
                                "SRE Manager, Example Infra (2018-2022)",
                                "MSc, Reliability Engineering, Example University (2016-2018)",
                            ],
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
                        "alpha",
                    ]
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)

                persona_id = "persona-test-photo-user"
                profile_page = (
                    alpha_space_root / "site" / "users" / f"persona-{persona_id}.html"
                ).read_text()
                self.assertIn(f"assets/persona_profiles/{persona_id}.jpg", profile_page)
                self.assertNotIn(f"assets/persona_avatars/{persona_id}.jpg", profile_page)

                profile_asset = (
                    alpha_space_root / "site" / "assets" / "persona_profiles" / f"{persona_id}.jpg"
                )
                avatar_asset = (
                    alpha_space_root / "site" / "assets" / "persona_avatars" / f"{persona_id}.jpg"
                )
                self.assertTrue(profile_asset.is_file())
                self.assertTrue(avatar_asset.is_file())
                self.assertEqual(profile_asset.read_bytes(), full_res_bytes)
                self.assertEqual(avatar_asset.read_bytes(), thumb_bytes)
            finally:
                catalog_path.write_text(original_catalog)
                if full_res_original is None:
                    full_res_path.unlink(missing_ok=True)
                else:
                    full_res_path.write_bytes(full_res_original)
                if thumb_original is None:
                    thumb_path.unlink(missing_ok=True)
                else:
                    thumb_path.write_bytes(thumb_original)

    def test_user_profile_page_lists_comments_written_by_persona(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            catalog_path = REPO_ROOT / "personas" / "social_users.json"
            profile_images_root = REPO_ROOT / "personas" / "profile_images"
            original_catalog = catalog_path.read_text()
            profile_image_path = profile_images_root / "comment-author.jpg"
            profile_image_original = profile_image_path.read_bytes() if profile_image_path.exists() else None
            try:
                persona_id = "persona-comment-author"
                profile_image_path.write_bytes(b"comment-author-photo")
                seeded_catalog = {
                    "schema_version": "social_users_v1",
                    "count": 1,
                    "users": [
                        {
                            "persona_id": persona_id,
                            "display_name": "Comment Author",
                            "full_name": "Comment Author",
                            "account_status": "active",
                            "stance_profile": "neutral",
                            "biography": (
                                "I evaluate complex arguments by tracking assumptions, pressure-testing evidence, "
                                "and explaining tradeoffs that matter for concrete decisions. I map failure modes, "
                                "identify hidden dependencies, and document what must be true for a conclusion to "
                                "hold in practice. I compare competing interpretations against primary sources, then "
                                "write plain-language summaries that preserve uncertainty and scope limits. I care "
                                "about whether claims survive scrutiny when definitions shift, edge cases appear, or "
                                "new evidence conflicts with earlier framing. I also track what teams actually do "
                                "after discussion, because reasoning quality should improve actions rather than stay "
                                "as abstract debate. I revise quickly when stronger data arrives and I annotate why "
                                "a change in view happened."
                            ),
                            "biography_profile": (
                                "I write analytical comments that challenge weak inferences, reward clear "
                                "evidence handling, and connect abstract claims back to what can actually be "
                                "verified in sources. I focus on clarity, testability, and practical decision value."
                            ),
                            "interests": ["evidence quality"],
                            "hot_topics": ["argument structure"],
                            "anger_topics": ["unsupported assertions"],
                            "profile_image_path": "personas/profile_images/comment-author.jpg",
                            "profile_image_prompt": (
                                "Photorealistic portrait photo of a single person in natural indoor light, "
                                "documentary style head-and-shoulders framing."
                            ),
                            "short_cv": ["Researcher, Example Org (2020-present)"],
                        }
                    ],
                }
                catalog_path.write_text(json.dumps(seeded_catalog, indent=2, sort_keys=True) + "\n")
                self._write_topic_record(
                    alpha_space_root,
                    topic_id="topic-profile-comments--aaaaaaaaaaaa",
                    title="Profile Comment Topic",
                    source_ids=[],
                    comment_section={
                        "page_ref": "topic:topic-profile-comments--aaaaaaaaaaaa",
                        "comments": [
                            {
                                "comment_uid": "comment-profile-1",
                                "comment_no": "1",
                                "persona_id": persona_id,
                                "body": "This is a profile-visible comment.",
                                "permalink": "#comment-profile-1",
                                "social_vote": {"upvotes": 20, "downvotes": 5, "score": 15},
                                "thread_state_key": "comment-profile-1",
                                "thread_expansion_key": "comment-profile-1",
                            }
                        ],
                    },
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

                profile_page = (
                    alpha_space_root / "site" / "users" / f"persona-{persona_id}.html"
                ).read_text()
                self.assertIn("Comments by This User", profile_page)
                self.assertIn("../topics/topic-profile-comments--aaaaaaaaaaaa.html#comment-profile-1", profile_page)
                self.assertIn("This is a profile-visible comment.", profile_page)
                self.assertIn("Score: 15", profile_page)
            finally:
                catalog_path.write_text(original_catalog)
                if profile_image_original is None:
                    profile_image_path.unlink(missing_ok=True)
                else:
                    profile_image_path.write_bytes(profile_image_original)

    def test_user_profile_page_hides_empty_comment_activity_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path, alpha_space_root = self._bootstrap_site_space(tmp_root, "alpha")
            catalog_path = REPO_ROOT / "personas" / "social_users.json"
            profile_images_root = REPO_ROOT / "personas" / "profile_images"
            original_catalog = catalog_path.read_text()
            profile_image_path = profile_images_root / "commentless-author.jpg"
            profile_image_original = profile_image_path.read_bytes() if profile_image_path.exists() else None
            try:
                persona_id = "persona-commentless-author"
                profile_image_path.write_bytes(b"commentless-author-photo")
                seeded_catalog = {
                    "schema_version": "social_users_v1",
                    "count": 1,
                    "users": [
                        {
                            "persona_id": persona_id,
                            "display_name": "Commentless Author",
                            "full_name": "Commentless Author",
                            "account_status": "active",
                            "stance_profile": "neutral",
                            "biography": (
                                "I evaluate complex arguments by tracking assumptions, pressure-testing evidence, "
                                "and explaining tradeoffs that matter for concrete decisions. I map failure modes, "
                                "identify hidden dependencies, and document what must be true for a conclusion to "
                                "hold in practice. I compare competing interpretations against primary sources, then "
                                "write plain-language summaries that preserve uncertainty and scope limits. I care "
                                "about whether claims survive scrutiny when definitions shift, edge cases appear, or "
                                "new evidence conflicts with earlier framing. I also track what teams actually do "
                                "after discussion, because reasoning quality should improve actions rather than stay "
                                "as abstract debate. I revise quickly when stronger data arrives and I annotate why "
                                "a change in view happened."
                            ),
                            "biography_profile": (
                                "I write analytical comments that challenge weak inferences, reward clear "
                                "evidence handling, and connect abstract claims back to what can actually be "
                                "verified in sources. I focus on clarity, testability, and practical decision value."
                            ),
                            "interests": ["evidence quality"],
                            "hot_topics": ["argument structure"],
                            "anger_topics": ["unsupported assertions"],
                            "profile_image_path": "personas/profile_images/commentless-author.jpg",
                            "profile_image_prompt": (
                                "Photorealistic portrait photo of a single person in natural indoor light, "
                                "documentary style head-and-shoulders framing."
                            ),
                            "short_cv": ["Reviewer, Example Org (2021-present)"],
                        }
                    ],
                }
                catalog_path.write_text(json.dumps(seeded_catalog, indent=2, sort_keys=True) + "\n")
                self._write_topic_record(
                    alpha_space_root,
                    topic_id="topic-commentless-profile--aaaaaaaaaaaa",
                    title="Commentless Profile Topic",
                    source_ids=[],
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

                profile_page = (
                    alpha_space_root / "site" / "users" / f"persona-{persona_id}.html"
                ).read_text()
                self.assertNotIn("Comments by This User", profile_page)
                self.assertNotIn("(no comments yet)", profile_page)
            finally:
                catalog_path.write_text(original_catalog)
                if profile_image_original is None:
                    profile_image_path.unlink(missing_ok=True)
                else:
                    profile_image_path.write_bytes(profile_image_original)

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
        source_date: str | None = None,
        citation_count: int | float | None = None,
        summary: str | None = None,
        display_title: str | None = None,
        authors: list[object] | None = None,
        references: list[dict[str, object]] | None = None,
        source_file_rel: str | None = None,
        source_markdown_rel: str | None = None,
        source_extraction_rel: str | None = None,
        front_page_image_rel: str | None = None,
        source_dossier: dict[str, object] | None = None,
        source_semantic: dict[str, object] | None = None,
        source_extraction: dict[str, object] | None = None,
        analysis_policy: dict[str, object] | None = None,
        external_related_links: list[dict[str, object]] | None = None,
        related_link_enrichment: dict[str, object] | None = None,
        source_family_id: str | None = None,
        source_revision: dict[str, object] | None = None,
    ) -> None:
        payload = {
            "schema_version": "source_record_v1",
            "source_id": source_id,
            "title": title,
            "date": source_date if source_date is not None else ingested_at.split("T", 1)[0],
            "ingested_at": ingested_at,
        }
        if summary is not None:
            payload["summary"] = summary
        if citation_count is not None:
            payload["citation_count"] = citation_count
        if display_title is not None:
            payload["display_title"] = display_title
        if authors is not None:
            payload["authors"] = authors
        if references is not None:
            payload["references"] = references
        if source_dossier is not None:
            payload["source_dossier"] = source_dossier
        if source_semantic is not None:
            payload["source_semantic"] = source_semantic
        if source_extraction is not None:
            payload["source_extraction"] = source_extraction
        if analysis_policy is not None:
            payload["analysis_policy"] = analysis_policy
        if external_related_links is not None:
            payload["external_related_links"] = external_related_links
        if related_link_enrichment is not None:
            payload["related_link_enrichment"] = related_link_enrichment
        if source_family_id is not None:
            payload["source_family_id"] = source_family_id
        if source_revision is not None:
            payload["source_revision"] = source_revision
        if source_file_rel is not None:
            payload["artifacts"] = {
                "source_file": source_file_rel,
                "source_markdown": source_markdown_rel or f"sources/artifacts/{source_id}/source.md",
                "source_extraction": source_extraction_rel or f"sources/artifacts/{source_id}/source_extraction.json",
                "source_provenance": f"sources/artifacts/{source_id}/source_provenance.md",
                "front_page_image": front_page_image_rel,
            }
        path = space_root / "sources" / "records" / f"{source_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_claim_record(
        self,
        space_root: Path,
        *,
        claim_id: str,
        source_id: str,
        text: str,
        evidence_excerpts: list[str] | None = None,
        short_title: str | None = None,
        added_at: str | None = None,
    ) -> None:
        payload = {
            "schema_version": "claim_record_v1",
            "claim_id": claim_id,
            "source_id": source_id,
            "text": text,
            "evidence_excerpts": evidence_excerpts if evidence_excerpts is not None else [],
        }
        if short_title is not None:
            payload["short_title"] = short_title
        if added_at is not None:
            payload["added_at"] = added_at
        path = space_root / "claims" / f"{claim_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_evidence_record(
        self,
        space_root: Path,
        *,
        evidence_id: str,
        title: str,
        excerpt: str,
        overview: str,
        evidence_type: str,
        source_id: str,
        claim_ids: list[str],
        page_refs: list[str] | None = None,
    ) -> None:
        payload = {
            "schema_version": "evidence_record_v1",
            "evidence_id": evidence_id,
            "title": title,
            "excerpt": excerpt,
            "overview": overview,
            "evidence_type": evidence_type,
            "source_id": source_id,
            "claim_ids": claim_ids,
            "page_refs": page_refs if page_refs is not None else [],
        }
        path = space_root / "evidence" / f"{evidence_id}.json"
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
        comment_section: dict[str, object] | None = None,
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
        if comment_section is not None:
            payload["comment_section"] = comment_section
        path = space_root / "topics" / f"{topic_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _write_overview_artifact(
        self,
        space_root: Path,
        *,
        overview_id: str,
        space_name: str,
        scope_kind: str,
        title: str,
        summary: str,
        source_ids: list[str],
        claim_ids: list[str],
        citation_anchors: list[dict[str, object]],
        warnings: list[str] | None = None,
    ) -> None:
        payload = {
            "schema_version": "space_overview_v1",
            "metadata": {
                "overview_id": overview_id,
                "scope_kind": scope_kind,
                "space_name": space_name,
                "scope_name": space_name,
                "title": title,
                "summary": summary,
            },
            "sections": [
                {
                    "section_id": "topic_framing",
                    "heading": "Topic framing",
                    "body": "Overview framing paragraph one.\n\nOverview framing paragraph two.",
                    "source_ids": source_ids,
                    "claim_ids": claim_ids,
                    "citation_anchor_ids": [str(anchor["anchor_id"]) for anchor in citation_anchors],
                },
                {
                    "section_id": "key_themes",
                    "heading": "Key themes",
                    "body": "Overview key themes paragraph.",
                    "source_ids": source_ids,
                    "claim_ids": claim_ids,
                    "citation_anchor_ids": [str(anchor["anchor_id"]) for anchor in citation_anchors],
                },
                {
                    "section_id": "agreement_and_disagreement",
                    "heading": "Agreement and disagreement",
                    "body": "Agreement and disagreement summary.",
                    "source_ids": source_ids,
                    "claim_ids": claim_ids,
                    "citation_anchor_ids": [str(anchor["anchor_id"]) for anchor in citation_anchors],
                },
                {
                    "section_id": "methods_and_evidence",
                    "heading": "Methods and evidence",
                    "body": "Methods and evidence summary.",
                    "source_ids": source_ids,
                    "claim_ids": claim_ids,
                    "citation_anchor_ids": [str(anchor["anchor_id"]) for anchor in citation_anchors],
                },
                {
                    "section_id": "open_questions",
                    "heading": "Open questions",
                    "body": "Open questions summary.",
                    "source_ids": source_ids,
                    "claim_ids": claim_ids,
                    "citation_anchor_ids": [str(anchor["anchor_id"]) for anchor in citation_anchors],
                },
            ],
            "references": {
                "source_ids": source_ids,
                "claim_ids": claim_ids,
                "citation_anchors": citation_anchors,
            },
            "freshness": {
                "generated_at": "2026-04-24T09:00:00Z",
                "input_signature": "overview-signature",
                "source_record_count": len(source_ids),
                "claim_count": len(claim_ids),
                "relation_count": 0,
                "topic_count": 0,
            },
            "warnings": warnings if warnings is not None else [],
        }
        path = space_root / "outputs" / "space_overview" / overview_id / "overview.json"
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
