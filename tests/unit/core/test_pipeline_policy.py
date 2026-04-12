from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sapi.contracts.run_envelopes import (
    CommentRunFields,
    IngestRunFields,
    PersonaProfileRunFields,
    QueryRunFields,
    RunEnvelopeBase,
)
from sapi.core.pipeline_policy import (
    exit_code_for_status,
    finalize_pipeline_run,
    finalize_run_status,
    initialize_run_status,
)
from sapi.core.transactions import ArtifactTransaction


class PipelinePolicyTests(unittest.TestCase):
    def test_status_transitions_follow_shared_contract(self) -> None:
        self.assertEqual(initialize_run_status(), "pending")
        self.assertEqual(
            finalize_run_status(
                lint_error_count=0,
                lint_warning_count=0,
                warning_budget=200,
            ),
            "success",
        )
        self.assertEqual(
            finalize_run_status(
                lint_error_count=0,
                lint_warning_count=201,
                warning_budget=200,
            ),
            "success_with_warnings",
        )
        self.assertEqual(
            finalize_run_status(
                lint_error_count=1,
                lint_warning_count=0,
                warning_budget=200,
            ),
            "failed",
        )
        self.assertEqual(
            finalize_run_status(
                lint_error_count=0,
                lint_warning_count=0,
                warning_budget=200,
                terminal_error=True,
            ),
            "failed",
        )
        self.assertEqual(
            finalize_run_status(
                lint_error_count=0,
                lint_warning_count=0,
                warning_budget=200,
                aborted=True,
            ),
            "aborted",
        )

    def test_exit_code_mapping_uses_zero_only_for_success_statuses(self) -> None:
        self.assertEqual(exit_code_for_status("success"), 0)
        self.assertEqual(exit_code_for_status("success_with_warnings"), 0)
        self.assertNotEqual(exit_code_for_status("failed"), 0)
        self.assertNotEqual(exit_code_for_status("aborted"), 0)
        with self.assertRaises(ValueError):
            exit_code_for_status("pending")

    def test_default_failure_prunes_run_container_while_ingest_force_preserves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space"

            # Default-mode failure: rollback and no committed run container.
            query_base = _base(flow_key="query_pipeline", run_id="run-20260412T120001Z--query000001")
            query_base.status = "failed"
            query_tx = ArtifactTransaction()
            query_run_md = space_root / "runs" / query_base.run_id / "run.md"
            _write_file(query_run_md, "transient")
            query_tx.mark_mkdir(query_run_md.parent)
            query_tx.mark_create(query_run_md)

            failed = finalize_pipeline_run(
                space_root=space_root,
                base=query_base,
                flow_fields=_query_fields(),
                transaction=query_tx,
                force_mode=False,
            )
            self.assertEqual(failed.exit_code, 1)
            self.assertIsNone(failed.run_record_path)
            self.assertIsNotNone(failed.rollback_disposition)
            self.assertTrue(failed.rollback_disposition.rollback_applied)  # type: ignore[union-attr]
            self.assertFalse((space_root / "runs" / query_base.run_id).exists())

            # Ingest force-mode failure: preserve artifacts and commit failure run record.
            ingest_base = _base(flow_key="ingest_pipeline", run_id="run-20260412T120002Z--ingest00001")
            ingest_base.status = "failed"
            ingest_tx = ArtifactTransaction()
            source_artifact = space_root / "sources" / "source-a.json"
            _write_file(source_artifact, '{"id":"source-a"}')
            ingest_tx.mark_create(source_artifact)

            forced = finalize_pipeline_run(
                space_root=space_root,
                base=ingest_base,
                flow_fields=_ingest_fields(),
                transaction=ingest_tx,
                force_mode=True,
            )
            self.assertEqual(forced.exit_code, 1)
            self.assertIsNotNone(forced.run_record_path)
            self.assertIsNotNone(forced.rollback_disposition)
            self.assertTrue(forced.rollback_disposition.rollback_skipped)  # type: ignore[union-attr]
            self.assertTrue((space_root / "runs" / ingest_base.run_id).exists())
            self.assertTrue(source_artifact.exists())

    def test_ingest_force_failure_requires_force_and_rollback_flags_in_run_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space"
            ingest_base = _base(flow_key="ingest_pipeline", run_id="run-20260412T120003Z--ingest00002")
            ingest_base.status = "failed"
            ingest_tx = ArtifactTransaction()

            with self.assertRaises(ValueError):
                finalize_pipeline_run(
                    space_root=space_root,
                    base=ingest_base,
                    flow_fields=IngestRunFields(
                        ingest_scope="space",
                        source_ids=["source-a"],
                        parent_run_id=None,
                        claims_changed=0,
                        relations_changed=0,
                        topic_pages_changed=0,
                        build_deferred=False,
                        deferred_build_reason=None,
                        force_mode=False,
                        rollback_skipped=False,
                    ),
                    transaction=ingest_tx,
                    force_mode=True,
                )

    def test_default_failure_prunes_run_container_for_comment_and_profile_pipelines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space"

            cases = [
                ("comment_section_pipeline", _comment_fields(), "run-20260412T120004Z--comments000"),
                ("persona_profile_pipeline", _profile_fields(), "run-20260412T120005Z--profiles000"),
            ]
            for flow_key, flow_fields, run_id in cases:
                with self.subTest(flow_key=flow_key):
                    base = _base(flow_key=flow_key, run_id=run_id)
                    base.status = "failed"
                    tx = ArtifactTransaction()
                    run_md = space_root / "runs" / run_id / "run.md"
                    _write_file(run_md, "transient")
                    tx.mark_mkdir(run_md.parent)
                    tx.mark_create(run_md)

                    result = finalize_pipeline_run(
                        space_root=space_root,
                        base=base,
                        flow_fields=flow_fields,
                        transaction=tx,
                        force_mode=False,
                    )
                    self.assertEqual(result.exit_code, 1)
                    self.assertIsNone(result.run_record_path)
                    self.assertIsNotNone(result.rollback_disposition)
                    self.assertTrue(result.rollback_disposition.rollback_applied)  # type: ignore[union-attr]
                    self.assertFalse((space_root / "runs" / run_id).exists())


def _base(*, flow_key: str, run_id: str) -> RunEnvelopeBase:
    return RunEnvelopeBase(
        run_id=run_id,
        flow_key=flow_key,  # type: ignore[arg-type]
        semantic_flows=["ingest_extraction", "topic_generation"],
        semantic_flow_invocation_counts={"ingest_extraction": 1, "topic_generation": 1},
        status="success",
        started_at="2026-04-12T12:00:00Z",
        completed_at="2026-04-12T12:00:05Z",
        model_fingerprint="model-x",
        provider_fingerprint="provider-y",
        reasoning_effort="high",
        execution_mode="live_llm",
        llm_attempt_count=2,
        lint_error_count=0,
        lint_warning_count=0,
        lint_info_count=0,
        toolchain_versions={"python": "3.12"},
    )


def _query_fields() -> QueryRunFields:
    return QueryRunFields(
        query_id="query-20260412T120000Z-question--abcdefghij",
        mode="strict",
        scope="space",
        claims_used=1,
        sources_used=1,
        contradictions_considered=0,
        manifest_path=None,
    )


def _ingest_fields() -> IngestRunFields:
    return IngestRunFields(
        ingest_scope="space",
        source_ids=["source-a"],
        parent_run_id=None,
        claims_changed=0,
        relations_changed=0,
        topic_pages_changed=0,
        build_deferred=False,
        deferred_build_reason=None,
        force_mode=True,
        rollback_skipped=True,
    )


def _comment_fields() -> CommentRunFields:
    return CommentRunFields(
        target_page_refs=["topic:topic-a"],
        comment_user_filters=["alice"],
        requested_count=3,
        comments_added=0,
        evidence_mode="none",
        evidence_snapshot_path=None,
    )


def _profile_fields() -> PersonaProfileRunFields:
    return PersonaProfileRunFields(
        persona_ids=["alice"],
        history_generated=0,
        history_updated=0,
        history_reused=0,
        pages_changed=0,
    )


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n")


if __name__ == "__main__":
    unittest.main()
