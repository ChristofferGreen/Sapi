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
            self.assertIn("class=\"comment-thread\"", topic_page_text)
            self.assertIn("No comments yet for this page.", topic_page_text)
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
                    "alpha",
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
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            topic_page_text = (space_root / "site" / "topics" / "topic-fallback--bbbbbbbbbbbb.html").read_text()
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
                    "Preparation independence constrains epistemic overlaps between</a>"
                ),
                topic_page_text,
            )
            self.assertIn(
                (
                    f"<a class=\"sentence-claim-option\" href=\"../claims/{claim_id_2}.html\">"
                    "Joint measurements reveal incompatibility with psi-epistemic</a>"
                ),
                topic_page_text,
            )
            self.assertNotIn("The paper claims that", topic_page_text)
            self.assertNotIn(">The paper ", topic_page_text)
            self.assertNotIn(">This paper ", topic_page_text)
            self.assertNotIn("Claim reference 1", topic_page_text)
            self.assertNotIn("Claim reference 2", topic_page_text)
            option_labels = re.findall(r'class=\"sentence-claim-option\" href=\"[^\"]+\">([^<]+)</a>', topic_page_text)
            self.assertGreaterEqual(len(option_labels), 2)
            self.assertTrue(all(3 <= len(label.split()) <= 7 for label in option_labels))

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
                    "alpha",
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
                evidence_excerpts=[
                    "The contradiction appears when independently prepared systems are measured jointly.",
                    "Equation (7) shows overlap assumptions produce predictions incompatible with quantum theory.",
                ],
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
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            claim_page_text = (space_root / "site" / "claims" / f"{claim_id}.html").read_text()
            self.assertIn(f"<h1>{claim_text}</h1>", claim_page_text)
            self.assertIn("<h2>Claim Statement</h2>", claim_page_text)
            self.assertIn("Overview and Interpretation", claim_page_text)
            self.assertIn(
                "epistemic-only interpretation fails once preparation independence",
                claim_page_text,
            )
            self.assertIn("Pages Using This Claim", claim_page_text)
            self.assertIn("href=\"../topics/topic-claim-rich--aaaaaaaaaaaa.html\"", claim_page_text)
            self.assertIn("href=\"../sources/source-a.html\"", claim_page_text)
            self.assertIn("Evidence Items", claim_page_text)
            self.assertIn("href=\"../evidence/", claim_page_text)
            self.assertIn("jointly", claim_page_text)
            self.assertIn("Strength and Support Stats", claim_page_text)
            self.assertIn(
                "score = 100 * (0.80 * evidence_factor + 0.20 * source_factor)",
                claim_page_text,
            )
            self.assertIn("Topic usages (informational only)", claim_page_text)
            self.assertIn("do not contribute to score", claim_page_text)
            self.assertIn("class=\"comment-thread\"", claim_page_text)
            evidence_links = re.findall(r'href=\"\.\./evidence/(evidence-[^\"]+)\.html\"', claim_page_text)
            self.assertGreaterEqual(len(evidence_links), 2)

            evidence_index_text = (space_root / "site" / "evidence" / "index.html").read_text()
            self.assertIn("<h1>Evidence</h1>", evidence_index_text)
            self.assertIn("independently prepared systems", evidence_index_text)

            claims_index_text = (space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn("id=\"claims-sort-direction\"", claims_index_text)
            self.assertIn("<option value=\"alphabetical\">Alphabetical</option>", claims_index_text)
            self.assertIn("<option value=\"score\">Score</option>", claims_index_text)
            self.assertIn("<option value=\"reverse_score\">Reverse score</option>", claims_index_text)
            self.assertIn("id=\"claims-index-list\"", claims_index_text)
            self.assertIn("data-claim-score=\"", claims_index_text)
            self.assertIn("rows.sort(function(a,b){return compareRows(a,b,mode);});", claims_index_text)
            self.assertIn(f"href=\"{evidence_links[0]}.html\"", evidence_index_text)

            topic_page_text = (space_root / "site" / "topics" / "topic-claim-rich--aaaaaaaaaaaa.html").read_text()
            self.assertIn("Evidence Used by This Topic", topic_page_text)
            self.assertIn("../evidence/", topic_page_text)

            source_page_text = (space_root / "site" / "sources" / "source-a.html").read_text()
            self.assertIn("Evidence from This Source", source_page_text)
            self.assertIn("../evidence/", source_page_text)

            claims_index_text = (space_root / "site" / "claims" / "index.html").read_text()
            self.assertIn("Treating quantum states as purely epistemic", claims_index_text)
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
            self.assertIn("class=\"site-sidebar\"", space_home)
            self.assertIn("class=\"site-main\"", space_home)
            self.assertIn("class=\"content-card\"", space_home)
            self.assertIn("class=\"top-search\"", space_home)
            self.assertIn("class=\"feed-list\"", space_home)
            self.assertIn("<summary>Spaces</summary>", space_home)
            self.assertIn(">Space Home</a>", space_home)
            self.assertIn("href=\"index.html\">alpha</a>", space_home)
            self.assertIn("href=\"../../beta/site/index.html\">beta</a>", space_home)
            self.assertIn("<summary>Sources</summary>", space_home)
            self.assertIn("href=\"sources/source-000.html\">", space_home)
            self.assertIn("<summary>Topics</summary>", space_home)
            self.assertIn("href=\"new/index.html\">New</a>", space_home)
            self.assertIn("href=\"sources/index.html\">Sources</a>", space_home)
            self.assertIn("href=\"topics/index.html\">Topics</a>", space_home)
            self.assertIn("href=\"users/index.html\">Users</a>", space_home)
            self.assertIn("href=\"evidence/index.html\">Evidence</a>", space_home)
            self.assertIn("href=\"claims/index.html\">Claims</a>", space_home)
            self.assertTrue((alpha_space_root / "site" / "claims" / "index.html").is_file())

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
            self.assertEqual(len(re.findall(r'href=\"source-\d{3}\.html\"', page_1_feed.group(1))), 50)
            self.assertEqual(len(re.findall(r'href=\"\.\./\.\./source-\d{3}\.html\"', page_2_feed.group(1))), 1)

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
            self.assertIn("class=\"source-hero\"", source_page)
            self.assertIn("class=\"source-hero-preview\"", source_page)
            self.assertIn("class=\"source-preview-link\"", source_page)
            self.assertIn("../../../../site/assets/source_previews/source-preview-b.svg", source_page)
            self.assertIn("../../sources/artifacts/source-preview-b/source.pdf", source_page)
            self.assertIn("Overview and Commentary", source_page)
            self.assertIn("What the Source Argues", source_page)
            self.assertNotIn("source_id:", source_page)

            site_new_page = (site_path / "site" / "new" / "index.html").read_text()
            self.assertIn("class=\"source-preview-feed\"", site_new_page)
            self.assertIn("../assets/source_previews/source-preview-b.svg", site_new_page)

            space_new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("class=\"source-preview-feed\"", space_new_page)
            self.assertIn("../../../../site/assets/source_previews/source-preview-b.svg", space_new_page)

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
            self.assertIn(
                f"<a class=\"sentence-claim-link\" href=\"../claims/{claim_id}.html\">",
                source_page,
            )
            self.assertNotIn("class=\"source-dossier-claims\"", source_page)
            self.assertNotIn("Claim reference 1", source_page)
            self.assertNotIn("Claim reference ", source_page)
            self.assertNotIn(">Claim 1</a>", source_page)

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

            space_new_page = (alpha_space_root / "site" / "new" / "index.html").read_text()
            self.assertIn("../../../../site/assets/source_previews/source-preview-photo.png", space_new_page)

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
                self.assertIn(alpha_profile_href, site_users_page)
                self.assertIn(beta_profile_href, site_users_page)

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
        front_page_image_rel: str | None = None,
        source_dossier: dict[str, object] | None = None,
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
        if source_dossier is not None:
            payload["source_dossier"] = source_dossier
        if source_file_rel is not None:
            payload["artifacts"] = {
                "source_file": source_file_rel,
                "overview_markdown": f"sources/artifacts/{source_id}/overview.md",
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
        path = space_root / "claims" / f"{claim_id}.json"
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
