#!/usr/bin/env python3
"""Ingest source acquisition entrypoint (TODO-0210 scope)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import os
from pathlib import Path
import sys
import json
import subprocess

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc, make_run_id
from sapi.contracts.run_envelopes import IngestRunFields, RunEnvelopeBase, RunStatus
from sapi.core.registry import resolve_registry_path, resolve_site_path_from_registry, resolve_space_root
from sapi.core.locks import IngestLockHeldError, ingest_lock
from sapi.core.pipeline_policy import finalize_pipeline_run
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.core.transactions import ArtifactTransaction
from sapi.ingest.citations import run_reference_extraction_and_link_backfill
from sapi.ingest.ingest_pipeline import plan_ingest_semantic_execution
from sapi.ingest.records_writer import (
    IngestExtractionPersistResult,
    ingest_source_artifacts_and_record,
    run_ingest_extraction_and_persist_canonical,
)
from sapi.ingest.source_content import SourceDateResolution, resolve_publication_date
from sapi.ingest.topic_generator import (
    TopicGenerationPersistResult,
    derive_default_topic_id_for_source,
    run_topic_generation_and_persist_canonical,
)
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.trace import SiteLlmTraceContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("source_path_or_url")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--source-title")
    parser.add_argument("--source-media-type")
    parser.add_argument("--source-type")
    parser.add_argument("--source-family-id")
    parser.add_argument("--canonical-identifier")
    parser.add_argument("--source-date")
    parser.add_argument("--require-source-date", action="store_true")
    parser.add_argument("--article-kind")
    parser.add_argument("--citation-count", type=float)
    parser.add_argument("--citation-count-as-of")
    parser.add_argument("--citation-count-provider")
    parser.add_argument("--citation-count-confidence")
    parser.add_argument("--enable-comment-enrichment", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--comment-count", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--comment-page", action="append", default=[], help=argparse.SUPPRESS)
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--query-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--build-deferred", action="store_true")
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source_only = False
    ingest_semantic_plan = None
    source_date_resolution: SourceDateResolution | None = None
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    run_id = make_run_id()
    toolchain_versions = {"python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"}

    runtime_policy = None
    registry_path = None
    site_path = None
    space_root = None
    result = None
    extraction_result = None
    topic_result = None
    build_manifest_path = None
    build_deferred = False
    deferred_build_reason = None
    reference_result = None
    semantic_flows: list[str] = []
    semantic_flow_invocation_counts: dict[str, int] = {}
    llm_attempt_count = 0
    trace_ctx: SiteLlmTraceContext | None = None
    transaction = ArtifactTransaction()

    try:
        source_only = _normalize_source_only_mode(args)
        ingest_semantic_plan = plan_ingest_semantic_execution(
            source_only=source_only,
            enable_comment_enrichment=args.enable_comment_enrichment,
            requested_comment_count=args.comment_count,
            comment_target_page_refs=args.comment_page if args.comment_page else None,
        )
        if ingest_semantic_plan.comment_enrichment_enabled:
            raise ValueError(
                "Inline ingest comment enrichment is not available yet; run create_comments.sh as an explicit "
                "follow-up step after ingest."
            )
        source_date_resolution = resolve_publication_date(
            explicit_source_date=args.source_date,
            inferred_source_date=None,
            require_source_date=args.require_source_date,
        )
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=args.mock_llm,
            env=os.environ,
        )
        registry_path = resolve_registry_path(args.registry_path)
        site_path = resolve_site_path_from_registry(registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        if args.verbose:
            trace_ctx = SiteLlmTraceContext(
                site_path=site_path,
                verbose=True,
            )
        with ingest_lock(space_root):
            result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=args.source_path_or_url,
                source_title_override=args.source_title,
                source_media_type_override=args.source_media_type,
                source_type_override=args.source_type,
                source_family_id=args.source_family_id,
                canonical_identifier=args.canonical_identifier,
                source_date=source_date_resolution.publication_date,
                article_kind=args.article_kind,
                citation_count=args.citation_count,
                citation_count_as_of=args.citation_count_as_of,
                citation_count_provider=args.citation_count_provider,
                citation_count_confidence=args.citation_count_confidence,
            )
            reference_result = run_reference_extraction_and_link_backfill(
                space_root=space_root,
                source_id=result.source_id,
            )
            if args.simulate_terminal_failure:
                raise RuntimeError("Simulated terminal ingest failure.")
            if not source_only:
                source_record = json.loads(result.record_path.read_text())
                source_title = source_record.get("title")
                _record_semantic_invocation(
                    flow_key="ingest_extraction",
                    semantic_flows=semantic_flows,
                    semantic_flow_invocation_counts=semantic_flow_invocation_counts,
                )
                extraction_result = run_ingest_extraction_and_persist_canonical(
                    space_root=space_root,
                    source_id=result.source_id,
                    run_id=run_id,
                    llm_client=_BootstrapIngestExtractionClient(
                        source_id=result.source_id,
                        source_title=source_title if isinstance(source_title, str) else None,
                        source_date_resolution=source_date_resolution,
                    ),
                    trace_ctx=trace_ctx,
                )
                llm_attempt_count += 1
                topic_id = derive_default_topic_id_for_source(
                    space_root=space_root,
                    source_id=result.source_id,
                )
                _record_semantic_invocation(
                    flow_key="topic_generation",
                    semantic_flows=semantic_flows,
                    semantic_flow_invocation_counts=semantic_flow_invocation_counts,
                )
                topic_result = run_topic_generation_and_persist_canonical(
                    space_root=space_root,
                    source_id=result.source_id,
                    run_id=run_id,
                    topic_id=topic_id,
                    llm_client=_BootstrapTopicGenerationClient(
                        source_id=result.source_id,
                        source_title=source_title if isinstance(source_title, str) else None,
                        topic_id=topic_id,
                        claim_ids=[path.stem for path in extraction_result.claim_paths],
                    ),
                    trace_ctx=trace_ctx,
                )
                llm_attempt_count += 1
                if args.build_deferred:
                    build_deferred = True
                    deferred_build_reason = "operator_requested_build_deferred"
                else:
                    build_manifest_path = _run_coalesced_ingest_topic_postprocess(
                        registry_path=registry_path,
                        space_name=args.space_name,
                        site_path=site_path,
                    )
    except IngestLockHeldError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - exercised by CLI contract tests.
        if args.force and space_root is not None and runtime_policy is not None:
            completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
            base = _make_run_base(
                run_id=run_id,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                execution_mode=runtime_policy.execution_mode,
                semantic_flows=semantic_flows,
                semantic_flow_invocation_counts=semantic_flow_invocation_counts,
                llm_attempt_count=llm_attempt_count,
                toolchain_versions=toolchain_versions,
            )
            flow_fields = _make_ingest_flow_fields(
                source_id=result.source_id if result is not None else None,
                extraction_result=extraction_result,
                topic_result=topic_result,
                build_deferred=build_deferred,
                deferred_build_reason=deferred_build_reason,
                force_mode=True,
                rollback_skipped=True,
            )
            finalized = finalize_pipeline_run(
                space_root=space_root,
                base=base,
                flow_fields=flow_fields,
                transaction=transaction,
                force_mode=True,
                summary="Ingest failed in force mode; invocation artifacts preserved for forensics.",
                errors=str(exc),
            )
            print(
                "scripts/ingest_source.py source ingested "
                f"(execution_mode={runtime_policy.execution_mode}, "
                f"run_id={run_id}, "
                f"status={finalized.status}, "
                f"run_record_path={finalized.run_record_path}, "
                f"error={str(exc)})",
                file=sys.stderr,
            )
        print(str(exc), file=sys.stderr)
        return 1

    assert runtime_policy is not None
    assert result is not None
    assert space_root is not None
    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    status = "success_with_warnings" if build_deferred else "success"
    base = _make_run_base(
        run_id=run_id,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        execution_mode=runtime_policy.execution_mode,
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )
    flow_fields = _make_ingest_flow_fields(
        source_id=result.source_id,
        extraction_result=extraction_result,
        topic_result=topic_result,
        build_deferred=build_deferred,
        deferred_build_reason=deferred_build_reason,
        force_mode=False,
        rollback_skipped=False,
    )
    if ingest_semantic_plan is not None and semantic_flow_invocation_counts != ingest_semantic_plan.semantic_flow_invocation_counts:
        raise RuntimeError(
            "Ingest semantic flow invocation counts violated boundary contract "
            f"(expected={ingest_semantic_plan.semantic_flow_invocation_counts}, "
            f"actual={semantic_flow_invocation_counts})."
        )
    finalized = finalize_pipeline_run(
        space_root=space_root,
        base=base,
        flow_fields=flow_fields,
        transaction=transaction,
        force_mode=False,
        summary="Ingest completed successfully.",
        changes=(
            f"claims_changed={flow_fields.claims_changed}, "
            f"relations_changed={flow_fields.relations_changed}, "
            f"topic_pages_changed={flow_fields.topic_pages_changed}"
        ),
        lint_summary="lint_error_count=0 lint_warning_count=0 lint_info_count=0",
        errors="",
    )

    summary = (
        "scripts/ingest_source.py source ingested "
        f"(execution_mode={runtime_policy.execution_mode}, "
        f"run_id={run_id}, "
        f"status={status}, "
        f"source_id={result.source_id}, "
        f"record_path={result.record_path}, "
        f"semantic_flows={semantic_flows}, "
        f"semantic_flow_invocation_counts={semantic_flow_invocation_counts}, "
        f"build_deferred={build_deferred}, "
        f"deferred_build_reason={deferred_build_reason}, "
        f"run_record_path={finalized.run_record_path}"
    )
    if reference_result is not None:
        summary += (
            f", references_extracted={reference_result.reference_count}, "
            f"linked_source_ids={reference_result.linked_source_ids}, "
            f"backfilled_source_ids={reference_result.backfilled_source_ids}"
        )
    if extraction_result is not None:
        summary += (
            f"claims_written={len(extraction_result.claim_paths)}, "
            f"relations_written={len(extraction_result.relation_paths)}"
        )
    if topic_result is not None:
        summary += (
            f", topic_id={topic_result.topic_id}, "
            f"topic_path={topic_result.topic_path}"
        )
    if build_manifest_path is not None:
        summary += f", build_manifest_path={build_manifest_path}"
    summary += ")"
    print(summary)
    return finalized.exit_code


class _BootstrapIngestExtractionClient:
    """Repository-local deterministic semantic client used for reconstruction bootstrap."""

    def __init__(
        self,
        *,
        source_id: str,
        source_title: str | None,
        source_date_resolution: SourceDateResolution,
    ) -> None:
        self._source_id = source_id
        self._source_title = source_title or source_id
        self._source_date_resolution = source_date_resolution

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        payload = {
            "source_date_inference": dict(self._source_date_resolution.source_date_inference),
            "source": {
                "source_id": self._source_id,
                "title": self._source_title,
            },
            "claims": [
                {
                    "text": f"Source `{self._source_title}` was ingested successfully.",
                    "evidence_excerpts": [],
                }
            ],
            "relations": [],
            "summary": "Bootstrap ingest extraction completed.",
            "warnings": list(self._source_date_resolution.warnings),
        }
        return json.dumps(payload)


class _BootstrapTopicGenerationClient:
    """Repository-local deterministic topic-generation client for reconstruction bootstrap."""

    def __init__(
        self,
        *,
        source_id: str,
        source_title: str | None,
        topic_id: str,
        claim_ids: list[str],
    ) -> None:
        self._source_id = source_id
        self._source_title = source_title or source_id
        self._topic_id = topic_id
        self._claim_ids = claim_ids

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        payload = {
            "topic_id": self._topic_id,
            "title": f"Topic: {self._source_title}",
            "structure_type": "wiki",
            "sections": [
                {
                    "heading": "Summary",
                    "body": f"Auto-generated topic scaffold for source `{self._source_title}`.",
                }
            ],
            "claim_ids": list(self._claim_ids),
            "source_ids": [self._source_id],
        }
        return json.dumps(payload)


def _trigger_deterministic_topic_postprocess(
    *,
    registry_path: Path,
    space_name: str,
    site_path: Path,
) -> Path:
    command = [
        "python3",
        str(_REPO_ROOT / "scripts" / "build_site.py"),
        "--workflow-key",
        "build_site",
        "--registry-path",
        str(registry_path),
        space_name,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "Topic deterministic post-processing failed: "
            f"stdout={result.stdout.strip()} stderr={result.stderr.strip()}"
        )
    manifest_path = site_path / "outputs" / "build_site" / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("Topic deterministic post-processing did not emit build manifest.")
    return manifest_path


def _run_coalesced_ingest_topic_postprocess(
    *,
    registry_path: Path,
    space_name: str,
    site_path: Path,
) -> Path:
    """Run one coalesced deterministic post-processing pass for chained ingest+topic flows."""
    return _trigger_deterministic_topic_postprocess(
        registry_path=registry_path,
        space_name=space_name,
        site_path=site_path,
    )


def _normalize_source_only_mode(args: argparse.Namespace) -> bool:
    if args.source_only and args.query_only:
        raise ValueError("cannot combine --source-only with alias --query-only")
    if args.query_only:
        print("Warning: --query-only is deprecated; use --source-only.", file=sys.stderr)
    return bool(args.source_only or args.query_only)


def _record_semantic_invocation(
    *,
    flow_key: str,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
) -> None:
    if flow_key not in semantic_flow_invocation_counts:
        semantic_flows.append(flow_key)
        semantic_flow_invocation_counts[flow_key] = 0
    semantic_flow_invocation_counts[flow_key] += 1


def _make_run_base(
    *,
    run_id: str,
    status: RunStatus,
    started_at: str,
    completed_at: str,
    execution_mode: str,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
    llm_attempt_count: int,
    toolchain_versions: dict[str, str],
) -> RunEnvelopeBase:
    return RunEnvelopeBase(
        run_id=run_id,
        flow_key="ingest_pipeline",
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        model_fingerprint="mock_bootstrap" if execution_mode == "mock_llm_test" else "live_unspecified",
        provider_fingerprint="mock" if execution_mode == "mock_llm_test" else "live_unspecified",
        reasoning_effort="high",
        execution_mode=execution_mode,
        llm_attempt_count=llm_attempt_count,
        lint_error_count=0,
        lint_warning_count=0,
        lint_info_count=0,
        toolchain_versions=toolchain_versions,
    )


def _make_ingest_flow_fields(
    *,
    source_id: str | None,
    extraction_result: IngestExtractionPersistResult | None,
    topic_result: TopicGenerationPersistResult | None,
    build_deferred: bool,
    deferred_build_reason: str | None,
    force_mode: bool,
    rollback_skipped: bool,
) -> IngestRunFields:
    claims_changed = 0
    relations_changed = 0
    topic_pages_changed = 0
    if extraction_result is not None:
        claims_changed = len(extraction_result.claim_paths)
        relations_changed = len(extraction_result.relation_paths)
    if topic_result is not None:
        topic_pages_changed = 1
    return IngestRunFields(
        ingest_scope="space",
        source_ids=[source_id] if source_id is not None else [],
        parent_run_id=None,
        claims_changed=claims_changed,
        relations_changed=relations_changed,
        topic_pages_changed=topic_pages_changed,
        build_deferred=build_deferred,
        deferred_build_reason=deferred_build_reason,
        force_mode=force_mode,
        rollback_skipped=rollback_skipped,
    )


if __name__ == "__main__":
    raise SystemExit(main())
