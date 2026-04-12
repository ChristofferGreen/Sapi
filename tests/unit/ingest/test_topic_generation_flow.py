from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from sapi.ingest.records_writer import ingest_source_artifacts_and_record
from sapi.ingest.topic_generator import (
    derive_default_topic_id_for_source,
    run_topic_generation_and_persist_canonical,
)
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.semantic_executor import SemanticFlowError


REPO_ROOT = Path(__file__).resolve().parents[3]


class _StaticTopicClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.last_request: SemanticLlmRequest | None = None

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        self.last_request = request
        return json.dumps(self._payload)


class TopicGenerationFlowTests(unittest.TestCase):
    def test_topic_flow_uses_canonical_spec_schema_and_writes_topics_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = _bootstrap_source(Path(tmp))
            topic_id = derive_default_topic_id_for_source(space_root=space_root, source_id=source_id)
            payload = {
                "topic_id": topic_id,
                "title": "Topic title",
                "structure_type": "wiki",
                "sections": [{"heading": "Summary", "body": "Body"}],
                "claim_ids": ["claim-a--111111111111"],
                "source_ids": [source_id],
            }
            topic_client = _StaticTopicClient(payload)

            result = run_topic_generation_and_persist_canonical(
                space_root=space_root,
                source_id=source_id,
                run_id="run-topic-001",
                topic_id=topic_id,
                llm_client=topic_client,
            )

            expected_topic_path = space_root / "topics" / f"{topic_id}.json"
            self.assertEqual(result.topic_path.resolve(), expected_topic_path.resolve())
            self.assertTrue(expected_topic_path.is_file())
            self.assertIsNotNone(topic_client.last_request)
            assert topic_client.last_request is not None
            self.assertEqual(topic_client.last_request.flow_key, "topic_generation")
            self.assertTrue(topic_client.last_request.schema_path.endswith("schemas/topic_generation.v1.schema.json"))
            self.assertEqual(
                Path(topic_client.last_request.output_json_path).resolve(),
                expected_topic_path.resolve(),
            )
            stored = json.loads(expected_topic_path.read_text())
            self.assertEqual(stored["topic_id"], topic_id)
            self.assertEqual(stored["source_ids"], [source_id])

    def test_topic_flow_validation_fails_when_required_schema_keys_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root, source_id = _bootstrap_source(Path(tmp))
            topic_id = derive_default_topic_id_for_source(space_root=space_root, source_id=source_id)
            invalid_payload = {
                "topic_id": topic_id,
                "title": "Topic title",
                "structure_type": "wiki",
                "sections": [],
                "claim_ids": [],
            }
            with self.assertRaises(SemanticFlowError):
                run_topic_generation_and_persist_canonical(
                    space_root=space_root,
                    source_id=source_id,
                    run_id="run-topic-invalid",
                    topic_id=topic_id,
                    llm_client=_StaticTopicClient(invalid_payload),
                    max_repair_loops=0,
                )
            self.assertFalse((space_root / "topics" / f"{topic_id}.json").exists())

    def test_ingest_entrypoint_triggers_topic_generation_and_deterministic_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            source_path = tmp_root / "source.txt"
            source_path.write_text("topic generation ingest contract\n")

            result = _run(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "ingest_source.py"),
                    "alpha",
                    str(source_path),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--source-title",
                    "Topic Source",
                    "--mock-llm",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("topic_id=", result.stdout)
            self.assertIn("build_manifest_path=", result.stdout)

            space_root = site_path / "spaces" / "alpha"
            topics_dir = space_root / "topics"
            topic_files = sorted(topics_dir.glob("topic-*.json"))
            self.assertEqual(len(topic_files), 1)
            topic_payload = json.loads(topic_files[0].read_text())
            source_record = json.loads(next((space_root / "sources" / "records").glob("*.json")).read_text())
            self.assertEqual(topic_payload["source_ids"], [source_record["source_id"]])

            manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest_payload = json.loads(manifest_path.read_text())
            self.assertEqual(manifest_payload["workflow_key"], "build_site")
            self.assertEqual(manifest_payload["space_targets"], ["alpha"])

            site_new_index_path = site_path / "site" / "new" / "index.html"
            self.assertTrue(site_new_index_path.is_file())
            site_new_html = site_new_index_path.read_text()
            self.assertIn(source_record["title"], site_new_html)
            self.assertIn(topic_payload["title"], site_new_html)

            runs_root = space_root / "runs"
            run_dirs = sorted(path for path in runs_root.glob("run-*") if path.is_dir())
            self.assertEqual(len(run_dirs), 1)
            run_md_path = run_dirs[0] / "run.md"
            lint_path = run_dirs[0] / "lint.json"
            self.assertTrue(run_md_path.is_file())
            self.assertTrue(lint_path.is_file())
            self.assertIn("## Lint Summary", run_md_path.read_text())
            lint_payload = json.loads(lint_path.read_text())
            self.assertEqual(lint_payload["workflow"], "ingest_source")
            self.assertEqual(lint_payload["error_count"], 0)
            self.assertEqual(lint_payload["warning_count"], 0)
            self.assertEqual(lint_payload["info_count"], 0)


def _bootstrap_source(tmp_root: Path) -> tuple[Path, str]:
    space_root = tmp_root / "spaces" / "alpha"
    source_path = tmp_root / "source.txt"
    source_path.write_text("topic generation fixture\n")
    result = ingest_source_artifacts_and_record(
        space_root=space_root,
        source_path_or_url=str(source_path),
        source_title_override="Fixture Topic Source",
    )
    return space_root, result.source_id


def _bootstrap_site_and_space(tmp_root: Path, space_name: str) -> Path:
    site_path = tmp_root / "site-a"
    _run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
    _run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
    return site_path


def _run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
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
