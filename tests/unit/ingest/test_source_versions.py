from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.core.transactions import ArtifactTransaction
from sapi.ingest.source_versions import (
    apply_source_revision_link,
    build_source_revision_detection_context,
    is_certain_revision_decision,
    run_source_revision_detection,
    select_source_revision_candidates,
)
from tests.conftest import create_deterministic_mock_llm_fixture


class SourceVersionTests(unittest.TestCase):
    def test_explicit_revision_link_writes_family_chain_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            old_id = "source-study-original--aaaaaaaaaaaa"
            new_id = "source-study-update--bbbbbbbbbbbb"
            _write_source_record(space_root, source_id=old_id, title="Study Original")
            _write_source_record(space_root, source_id=new_id, title="Study Update")

            transaction = ArtifactTransaction()
            result = apply_source_revision_link(
                space_root=space_root,
                new_source_id=new_id,
                revises_source_id=old_id,
                transaction=transaction,
                link_context={"method": "operator_cli", "certainty": True},
            )

            self.assertEqual(result.revision_count, 2)
            old_record = _read_source_record(space_root, old_id)
            new_record = _read_source_record(space_root, new_id)
            self.assertEqual(old_record["source_family_id"], result.source_family_id)
            self.assertEqual(new_record["source_family_id"], result.source_family_id)
            self.assertEqual(old_record["source_revision"]["revision_index"], 1)
            self.assertEqual(old_record["source_revision"]["superseded_by_source_id"], new_id)
            self.assertEqual(new_record["source_revision"]["revision_index"], 2)
            self.assertTrue(new_record["source_revision"]["is_latest"])
            self.assertEqual(new_record["source_revision"]["supersedes_source_id"], old_id)
            self.assertEqual(new_record["source_revision"]["link_context"]["method"], "operator_cli")

            manifest = json.loads(result.manifest_path.read_text())
            self.assertEqual(manifest["schema_version"], "source_revision_family_v1")
            self.assertEqual(manifest["latest_source_id"], new_id)
            self.assertEqual([item["source_id"] for item in manifest["revisions"]], [old_id, new_id])

    def test_candidate_shortlist_is_not_a_revision_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            old_id = "source-shared-title--aaaaaaaaaaaa"
            new_id = "source-shared-title--bbbbbbbbbbbb"
            _write_source_record(space_root, source_id=old_id, title="Shared Meditation Review")
            _write_source_record(space_root, source_id=new_id, title="Shared Meditation Review Updated")

            candidates = select_source_revision_candidates(space_root=space_root, new_source_id=new_id)
            self.assertEqual([candidate.source_id for candidate in candidates], [old_id])
            self.assertFalse(
                is_certain_revision_decision(
                    payload={
                        "decision": "uncertain",
                        "certainty": False,
                        "matched_source_id": old_id,
                    },
                    candidate_source_ids={old_id},
                )
            )
            self.assertFalse(
                is_certain_revision_decision(
                    payload={
                        "decision": "revision",
                        "certainty": True,
                        "matched_source_id": "source-other--cccccccccccc",
                    },
                    candidate_source_ids={old_id},
                )
            )

    def test_revision_detection_flow_uses_canonical_schema_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            old_id = "source-context-original--aaaaaaaaaaaa"
            new_id = "source-context-update--bbbbbbbbbbbb"
            _write_source_record(space_root, source_id=old_id, title="Context Original")
            _write_source_record(space_root, source_id=new_id, title="Context Update")
            candidates = select_source_revision_candidates(space_root=space_root, new_source_id=new_id)
            task_context = build_source_revision_detection_context(
                space_root=space_root,
                new_source_id=new_id,
                candidates=candidates,
            )
            client = create_deterministic_mock_llm_fixture(
                mode="valid",
                valid_payload={
                    "decision": "revision",
                    "certainty": True,
                    "matched_source_id": old_id,
                    "candidate_source_ids": [old_id],
                    "rationale": "Matching title and explicit update marker.",
                    "evidence": ["The updated source title marks this as a revision."],
                },
            )

            result = run_source_revision_detection(
                space_root=space_root,
                source_id=new_id,
                run_id="run-20260427T120000Z--revision",
                llm_client=client,
            )

            self.assertEqual(result.payload["decision"], "revision")
            self.assertEqual(result.attempt_count, 1)
            self.assertTrue(result.semantic_output_path.is_file())
            self.assertEqual(client.call_count, 1)
            request = client.requests[0]
            self.assertEqual(request.flow_key, "source_revision_detection")
            self.assertTrue(any(path.endswith("/sources/artifacts") for path in request.context_paths))
            self.assertEqual(
                task_context["revision_policy"]["default_reading_order"][0],
                "source.md",
            )


def _write_source_record(space_root: Path, *, source_id: str, title: str) -> None:
    artifact_root = space_root / "sources" / "artifacts" / source_id
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "source.md").write_text(f"# {title}\n")
    (artifact_root / "source_extraction.json").write_text(
        json.dumps({"quality_status": "usable", "input_sha256": source_id}, sort_keys=True) + "\n"
    )
    (artifact_root / "source.txt").write_text(title + "\n")
    record_path = space_root / "sources" / "records" / f"{source_id}.json"
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(
        json.dumps(
            {
                "schema_version": "source_record_v1",
                "source_id": source_id,
                "title": title,
                "display_title": title,
                "date": "2026-04-27",
                "ingested_at": "2026-04-27T12:00:00Z",
                "source_locator": f"{title}.txt",
                "artifacts": {
                    "source_file": f"sources/artifacts/{source_id}/source.txt",
                    "source_markdown": f"sources/artifacts/{source_id}/source.md",
                    "source_extraction": f"sources/artifacts/{source_id}/source_extraction.json",
                },
                "analysis_policy": {
                    "preferred_artifact": "source_markdown",
                    "fallback_artifacts": ["source_file"],
                    "quality_status": "usable",
                    "warnings": [],
                },
                "source_extraction": {
                    "quality_status": "usable",
                    "input_sha256": source_id,
                    "warnings": [],
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _read_source_record(space_root: Path, source_id: str) -> dict[str, object]:
    return json.loads((space_root / "sources" / "records" / f"{source_id}.json").read_text())


if __name__ == "__main__":
    unittest.main()
