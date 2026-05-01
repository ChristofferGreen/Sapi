from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.conftest import (
    REPO_ROOT,
    assert_lint_artifact,
    assert_run_frontmatter_fields,
    bootstrap_site_and_space,
    latest_run_directory,
    run_directories,
    run_command,
    write_source_fixture,
)


class IngestPipelineIntegrationTests(unittest.TestCase):
    def test_ingest_mock_mode_writes_canonical_artifacts_and_run_lint_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            source_path = write_source_fixture(tmp_root, content="tier3 ingest fixture\n")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Tier3 Ingest Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            claim_records = sorted((space_root / "claims").glob("claim-*.json"))
            relation_records = sorted((space_root / "relations").glob("rel-*.json"))
            topic_records = sorted((space_root / "topics").glob("topic-*.json"))
            self.assertEqual(len(source_records), 1)
            self.assertGreaterEqual(len(claim_records), 1)
            self.assertTrue((space_root / "relations").is_dir())
            self.assertEqual(len(topic_records), 0)

            run_dir = latest_run_directory(space_root)
            run_md_path = run_dir / "run.md"
            lint_path = run_dir / "lint.json"

            frontmatter = assert_run_frontmatter_fields(
                run_md_path,
                expected_fields={
                    "flow_key": "ingest_pipeline",
                    "status": "success",
                    "execution_mode": "mock_llm_test",
                    "semantic_flows": ["ingest_extraction", "topic_generation"],
                    "source_ids": [source_records[0].stem],
                    "claims_changed": len(claim_records),
                    "relations_changed": len(relation_records),
                    "topic_pages_changed": len(topic_records),
                    "question_mapping_status": "no_active_questions",
                    "question_matches_changed": 0,
                    "lint_error_count": 0,
                    "lint_warning_count": 0,
                    "lint_info_count": 0,
                },
            )
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"ingest_extraction": 1, "topic_generation": 1},
            )
            self.assertEqual(frontmatter["run_id"], run_dir.name)

            assert_lint_artifact(
                lint_path,
                expected_workflow="ingest_source",
                expected_error_count=0,
                expected_warning_count=0,
                expected_info_count=0,
            )

            build_manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            self.assertTrue(build_manifest_path.is_file())
            self.assertIn("build_manifest_path=", result.stdout)

    def test_ingest_maps_new_source_to_active_prepared_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            questions_tsv = tmp_root / "questions.tsv"
            questions_tsv.write_text(
                "alpha\tquestion-protein-intake\t1\tWhat protein intake supports muscle growth?\n"
                "alpha\tquestion-inactive\t2\tinactive\tWhich inactive question should stay hidden?\n"
            )
            create_questions = run_command(
                [
                    "bash",
                    str(REPO_ROOT / "create_questions.sh"),
                    str(site_path),
                    str(questions_tsv),
                ]
            )
            self.assertEqual(create_questions.returncode, 0, msg=create_questions.stderr)
            source_path = write_source_fixture(tmp_root, content="prepared question mapping fixture\n")

            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Prepared Question Mapping Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            source_record = sorted((space_root / "sources" / "records").glob("source-*.json"))[0]
            question_path = space_root / "questions" / "question-protein-intake.json"
            question_payload = json.loads(question_path.read_text())
            self.assertEqual(question_payload["linked_source_ids"], [source_record.stem])
            self.assertEqual(len(question_payload["claim_ids"]), 1)
            self.assertEqual(len(question_payload["evidence_ids"]), 1)
            self.assertIn("short_answer", question_payload["synthesis"])
            self.assertEqual(len(question_payload["measurement_ids"]), 1)
            self.assertEqual(
                question_payload["freshness"]["question_synthesis"]["status"],
                "refreshed",
            )
            self.assertEqual(
                question_payload["freshness"]["question_measurement_extraction"]["status"],
                "refreshed",
            )
            self.assertEqual(
                question_payload["freshness"]["question_relevance_mappings"][0]["source_id"],
                source_record.stem,
            )
            inactive_payload = json.loads((space_root / "questions" / "question-inactive.json").read_text())
            self.assertEqual(inactive_payload["linked_source_ids"], [])

            run_dir = latest_run_directory(space_root)
            frontmatter = assert_run_frontmatter_fields(
                run_dir / "run.md",
                expected_fields={
                    "semantic_flows": [
                        "ingest_extraction",
                        "question_relevance_mapping",
                        "question_measurement_extraction",
                        "question_synthesis",
                        "topic_generation",
                    ],
                    "question_mapping_status": "mapped",
                    "question_matches_changed": 1,
                    "question_measurement_status": "refreshed",
                    "question_measurements_changed": 1,
                    "question_synthesis_status": "refreshed",
                    "question_syntheses_changed": 1,
                },
            )
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {
                    "ingest_extraction": 1,
                    "question_relevance_mapping": 1,
                    "question_measurement_extraction": 1,
                    "question_synthesis": 1,
                    "topic_generation": 1,
                },
            )
            self.assertEqual(frontmatter["llm_attempt_count"], 5)
            self.assertTrue((run_dir / "semantic" / "question_relevance_mapping.json").is_file())
            self.assertTrue(
                (
                    run_dir
                    / "semantic"
                    / "question_measurement_extraction"
                    / "question-protein-intake.json"
                ).is_file()
            )
            self.assertTrue(
                (run_dir / "semantic" / "question_synthesis" / "question-protein-intake.json").is_file()
            )

    def test_explicit_revision_ingest_links_family_without_detection_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            first_source_path = write_source_fixture(
                tmp_root,
                filename="source-v1.txt",
                content="revision fixture v1\n",
            )
            first_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(first_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Revision Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(first_result.returncode, 0, msg=first_result.stderr)
            first_source_id = sorted((space_root / "sources" / "records").glob("source-*.json"))[0].stem

            second_source_path = write_source_fixture(
                tmp_root,
                filename="source-v2.txt",
                content="revision fixture v2\n",
            )
            second_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(second_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Revision Fixture Updated",
                    "--revises-source-id",
                    first_source_id,
                    "--mock-llm",
                ]
            )
            self.assertEqual(second_result.returncode, 0, msg=second_result.stderr)

            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(len(source_records), 2)
            records_by_id = {path.stem: json.loads(path.read_text()) for path in source_records}
            second_source_id = next(source_id for source_id in records_by_id if source_id != first_source_id)
            self.assertEqual(
                records_by_id[first_source_id]["source_revision"]["superseded_by_source_id"],
                second_source_id,
            )
            self.assertTrue(records_by_id[second_source_id]["source_revision"]["is_latest"])
            family_id = records_by_id[second_source_id]["source_family_id"]
            manifest_path = space_root / "sources" / "versions" / f"{family_id}.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["latest_source_id"], second_source_id)

            run_md_path = latest_run_directory(space_root) / "run.md"
            frontmatter = assert_run_frontmatter_fields(
                run_md_path,
                expected_fields={
                    "flow_key": "ingest_pipeline",
                    "status": "success",
                    "execution_mode": "mock_llm_test",
                    "semantic_flows": ["ingest_extraction", "topic_generation"],
                    "source_ids": [second_source_id],
                },
            )
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {"ingest_extraction": 1, "topic_generation": 1},
            )
            self.assertNotIn("source_revision_detection", frontmatter["semantic_flows"])
            self.assertIn("source_family_id=", second_result.stdout)

    def test_live_revision_detection_links_only_certain_candidate_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            first_source_path = write_source_fixture(
                tmp_root,
                filename="detected-v1.txt",
                content="detected revision fixture v1\n",
            )
            first_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(first_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Detected Revision Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(first_result.returncode, 0, msg=first_result.stderr)
            first_source_id = sorted((space_root / "sources" / "records").glob("source-*.json"))[0].stem

            fake_bin = tmp_root / "bin"
            fake_bin.mkdir()
            fake_codex = fake_bin / "codex"
            fake_codex.write_text(_fake_codex_revision_script(matched_source_id=first_source_id))
            fake_codex.chmod(0o755)

            second_source_path = write_source_fixture(
                tmp_root,
                filename="detected-v2.txt",
                content="detected revision fixture v2\n",
            )
            env = dict(os.environ)
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            second_result = subprocess.run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(second_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Detected Revision Fixture Updated",
                    "--llm-model",
                    "gpt-5.5",
                    "--llm-reasoning-effort",
                    "high",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(second_result.returncode, 0, msg=second_result.stderr)

            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            records_by_id = {path.stem: json.loads(path.read_text()) for path in source_records}
            second_source_id = next(source_id for source_id in records_by_id if source_id != first_source_id)
            self.assertEqual(
                records_by_id[second_source_id]["source_revision"]["link_context"]["method"],
                "source_revision_detection",
            )
            self.assertEqual(
                records_by_id[second_source_id]["source_revision"]["supersedes_source_id"],
                first_source_id,
            )

            run_md_path = latest_run_directory(space_root) / "run.md"
            frontmatter = assert_run_frontmatter_fields(
                run_md_path,
                expected_fields={
                    "execution_mode": "live_llm",
                    "semantic_flows": [
                        "source_revision_detection",
                        "ingest_extraction",
                        "topic_generation",
                    ],
                },
            )
            self.assertEqual(
                frontmatter["semantic_flow_invocation_counts"],
                {
                    "source_revision_detection": 1,
                    "ingest_extraction": 1,
                    "topic_generation": 1,
                },
            )
            semantic_payload = json.loads(
                (latest_run_directory(space_root) / "semantic" / "source_revision_detection.json").read_text()
            )
            self.assertEqual(semantic_payload["matched_source_id"], first_source_id)

    def test_live_revision_detection_uncertain_candidate_remains_independent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            first_source_path = write_source_fixture(
                tmp_root,
                filename="near-miss-v1.txt",
                content="near miss revision fixture v1\n",
            )
            first_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(first_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Near Miss Revision Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(first_result.returncode, 0, msg=first_result.stderr)
            first_source_id = sorted((space_root / "sources" / "records").glob("source-*.json"))[0].stem

            detection_payload = {
                "decision": "uncertain",
                "certainty": False,
                "matched_source_id": None,
                "candidate_source_ids": [first_source_id],
                "rationale": "The sources share title tokens but no version marker or identifier proves a revision.",
                "evidence": ["This fake near-miss keeps the new source independent."],
            }
            fake_bin = tmp_root / "bin"
            fake_bin.mkdir()
            fake_codex = fake_bin / "codex"
            fake_codex.write_text(
                _fake_codex_revision_script(
                    matched_source_id=first_source_id,
                    detection_payload=detection_payload,
                )
            )
            fake_codex.chmod(0o755)

            second_source_path = write_source_fixture(
                tmp_root,
                filename="near-miss-v2.txt",
                content="near miss revision fixture v2\n",
            )
            env = dict(os.environ)
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            second_result = subprocess.run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(second_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Near Miss Revision Fixture Updated",
                    "--llm-model",
                    "gpt-5.5",
                    "--llm-reasoning-effort",
                    "high",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(second_result.returncode, 0, msg=second_result.stderr)

            source_records = sorted((space_root / "sources" / "records").glob("source-*.json"))
            self.assertEqual(len(source_records), 2)
            records_by_id = {path.stem: json.loads(path.read_text()) for path in source_records}
            self.assertNotIn("source_revision", records_by_id[first_source_id])
            second_source_id = next(source_id for source_id in records_by_id if source_id != first_source_id)
            self.assertNotIn("source_revision", records_by_id[second_source_id])
            self.assertFalse(list((space_root / "sources" / "versions").glob("*.json")))

            frontmatter = assert_run_frontmatter_fields(
                latest_run_directory(space_root) / "run.md",
                expected_fields={
                    "execution_mode": "live_llm",
                    "semantic_flows": [
                        "source_revision_detection",
                        "ingest_extraction",
                        "topic_generation",
                    ],
                },
            )
            self.assertEqual(frontmatter["semantic_flow_invocation_counts"]["source_revision_detection"], 1)
            self.assertIn("source_revision_detection_decision=uncertain", second_result.stdout)
            self.assertNotIn("source_family_id=", second_result.stdout)

    def test_explicit_revision_failure_rolls_back_records_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"
            first_source_path = write_source_fixture(
                tmp_root,
                filename="rollback-v1.txt",
                content="rollback revision fixture v1\n",
            )
            first_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(first_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Rollback Revision Fixture",
                    "--mock-llm",
                ]
            )
            self.assertEqual(first_result.returncode, 0, msg=first_result.stderr)
            first_record_path = sorted((space_root / "sources" / "records").glob("source-*.json"))[0]
            first_source_id = first_record_path.stem
            original_first_record_text = first_record_path.read_text()
            original_run_dirs = [path.name for path in run_directories(space_root)]

            second_source_path = write_source_fixture(
                tmp_root,
                filename="rollback-v2.txt",
                content="rollback revision fixture v2\n",
            )
            second_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(second_source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Rollback Revision Fixture Updated",
                    "--revises-source-id",
                    first_source_id,
                    "--simulate-terminal-failure",
                    "--mock-llm",
                ]
            )
            self.assertEqual(second_result.returncode, 1)
            self.assertIn("Simulated terminal ingest failure", second_result.stderr)
            self.assertEqual([path.name for path in run_directories(space_root)], original_run_dirs)
            self.assertEqual(first_record_path.read_text(), original_first_record_text)
            self.assertEqual(
                [path.stem for path in sorted((space_root / "sources" / "records").glob("source-*.json"))],
                [first_source_id],
            )
            self.assertFalse(list((space_root / "sources" / "versions").glob("*.json")))


def _fake_codex_revision_script(
    *,
    matched_source_id: str,
    detection_payload: dict[str, object] | None = None,
) -> str:
    payload = detection_payload or {
        "decision": "revision",
        "certainty": True,
        "matched_source_id": matched_source_id,
        "candidate_source_ids": [matched_source_id],
        "rationale": "The fake live canary marks the candidate as a certain revision.",
        "evidence": ["The candidate id was provided by deterministic shortlisting."],
    }
    detection_payload_json = json.dumps(payload, sort_keys=True)
    return f"""#!/usr/bin/env python3
import json
import re
import sys

prompt = sys.stdin.read()
DETECTION_PAYLOAD = json.loads({json.dumps(detection_payload_json)})

def emit(payload):
    print(json.dumps({{"item": {{"type": "agent_message", "text": json.dumps(payload)}}}}))

if '"flow_key": "source_revision_detection"' in prompt:
    emit(DETECTION_PAYLOAD)
elif '"flow_key": "ingest_extraction"' in prompt:
    match = re.search(r'"must_include_source_id":\\s*"([^"]+)"', prompt)
    source_id = match.group(1) if match else "source-live-fixture--0123456789ab"
    title_match = re.search(r'"must_include_source_title":\\s*"([^"]+)"', prompt)
    title = title_match.group(1) if title_match else source_id
    long_summary = (
        "This fake live revision summary gives the source page enough validated dossier material to exercise "
        "the production ingest path without calling a real model. It explains that the updated document is "
        "being treated as a revision only because the prior source revision detection flow returned a certain "
        "candidate match. The text is intentionally long enough to satisfy the same source dossier schema used "
        "by live runs, so the integration test covers schema validation, canonical writes, and deterministic "
        "rendering after revision metadata has already been linked. "
    ) * 3
    section_body = (
        "The fake live flow emits a section body that is long enough for the dossier schema and remains focused "
        "on the revision-ingest contract: semantic detection decides the source family, while deterministic "
        "post-processing only writes stored metadata and links."
    )
    emit({{
        "source_date_inference": {{"date": None, "origin": "unknown", "confidence": "unknown", "rationale": None}},
        "source": {{"source_id": source_id, "title": title, "display_title": title}},
        "claims": [{{"text": "Detected revision fixtures preserve the same underlying source across versions."}}],
        "evidence_items": [
            {{
                "evidence_id": "evidence-detected-revision--0123456789ab",
                "title": "Detected revision fixture",
                "excerpt": "Detected revision fixtures preserve the same underlying source across versions.",
                "overview": "A fake live Codex response provides a concrete evidence artifact for integration coverage.",
                "evidence_type": "formal_argument",
                "claim_refs": ["0"],
                "source_id": source_id,
                "page_refs": []
            }}
        ],
        "relations": [],
        "summary": "Fake live ingest extraction completed.",
        "source_dossier": {{
            "summary_short": "Fake live revision summary for schema-valid integration coverage.",
            "summary_long": long_summary,
            "sections": [
                {{"heading": "Revision", "body": section_body, "grounding_claim_ids": []}},
                {{"heading": "Evidence", "body": section_body, "grounding_claim_ids": []}},
                {{"heading": "Method", "body": section_body, "grounding_claim_ids": []}},
                {{"heading": "Limits", "body": section_body, "grounding_claim_ids": []}},
                {{"heading": "Use", "body": section_body, "grounding_claim_ids": []}}
            ]
        }},
        "warnings": []
    }})
elif '"flow_key": "topic_generation"' in prompt:
    emit({{"topics": []}})
else:
    emit({{"value": "unsupported fake codex prompt"}})
"""


if __name__ == "__main__":
    unittest.main()
