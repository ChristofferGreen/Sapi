from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sapi.core.transactions import ArtifactTransaction, apply_terminal_failure_policy


class TransactionRollbackTests(unittest.TestCase):
    def test_force_mode_override_is_ingest_only(self) -> None:
        tx = ArtifactTransaction()
        with self.assertRaises(ValueError):
            apply_terminal_failure_policy(
                transaction=tx,
                pipeline_flow_key="query_pipeline",
                force_mode=True,
                run_container_path=None,
            )

    def test_default_failure_rolls_back_writes_and_removes_run_container(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_container = root / "spaces/alpha/runs/run-20260412T120000Z--abc123def0"
            canonical_path = root / "spaces/alpha/sources/source-a.json"
            run_md_path = run_container / "run.md"
            lint_path = run_container / "lint.json"

            _write_file(canonical_path, '{"id":"source-a"}')
            _write_file(run_md_path, "status: failed\n")
            _write_file(lint_path, '{"error_count":1}')

            tx = ArtifactTransaction()
            tx.mark_create(canonical_path)
            tx.mark_mkdir(run_container)
            tx.mark_create(run_md_path)
            tx.mark_create(lint_path)

            disposition = apply_terminal_failure_policy(
                transaction=tx,
                pipeline_flow_key="query_pipeline",
                force_mode=False,
                run_container_path=run_container,
            )

            self.assertTrue(disposition.rollback_applied)
            self.assertFalse(disposition.rollback_skipped)
            self.assertTrue(disposition.run_container_removed)
            self.assertFalse(canonical_path.exists())
            self.assertFalse(run_md_path.exists())
            self.assertFalse(lint_path.exists())
            self.assertFalse(run_container.exists())

    def test_ingest_force_failure_may_preserve_artifacts_and_run_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_container = root / "spaces/alpha/runs/run-20260412T120000Z--abc123def0"
            run_md_path = run_container / "run.md"
            semantic_path = run_container / "semantic/ingest_extraction.json"
            canonical_path = root / "spaces/alpha/sources/source-a.json"

            _write_file(run_md_path, "status: failed\nforce_mode: true\nrollback_skipped: true\n")
            _write_file(semantic_path, '{"source":{}}')
            _write_file(canonical_path, '{"id":"source-a"}')

            tx = ArtifactTransaction()
            tx.mark_mkdir(run_container)
            tx.mark_create(run_md_path)
            tx.mark_create(semantic_path)
            tx.mark_create(canonical_path)

            disposition = apply_terminal_failure_policy(
                transaction=tx,
                pipeline_flow_key="ingest_pipeline",
                force_mode=True,
                run_container_path=run_container,
            )

            self.assertFalse(disposition.rollback_applied)
            self.assertTrue(disposition.rollback_skipped)
            self.assertTrue(run_container.exists())
            self.assertTrue(run_md_path.exists())
            self.assertTrue(semantic_path.exists())
            self.assertTrue(canonical_path.exists())

    def test_rollback_covers_canonical_derived_and_run_lint_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "run-20260412T120000Z--abc123def0"
            run_container = root / f"spaces/alpha/runs/{run_id}"

            canonical_paths = [
                root / "spaces/alpha/sources/source-a.json",
                root / "spaces/alpha/claims/claim-a.json",
                root / "spaces/alpha/relations/relation-a.json",
                root / "spaces/alpha/topics/topic-a.json",
            ]
            derived_paths = [
                root / "spaces/alpha/site/topics/topic-a/index.html",
                root / "spaces/alpha/outputs/query/query-1/result.md",
            ]
            invocation_paths = [
                run_container / "run.md",
                run_container / "lint.json",
                run_container / "semantic/topic_generation.json",
            ]

            tx = ArtifactTransaction()
            tx.mark_mkdir(run_container)
            for path in [*canonical_paths, *derived_paths, *invocation_paths]:
                _write_file(path, "{}")
                tx.mark_create(path)

            tx.rollback()

            for path in [*canonical_paths, *derived_paths, *invocation_paths]:
                self.assertFalse(path.exists(), f"expected rollback removal for {path}")
            self.assertFalse(run_container.exists())


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n")


if __name__ == "__main__":
    unittest.main()
