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
from sapi.core.runtime_flags import (
    RuntimeFlagSnapshot,
    add_runtime_flag_arguments,
    runtime_flags_summary_dict,
    snapshot_runtime_flags,
    validate_runtime_flag_arguments,
)
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.core.transactions import ArtifactTransaction
from sapi.core.display_titles import resolve_display_title
from sapi.ingest.citations import run_reference_extraction_and_link_backfill
from sapi.ingest.ingest_pipeline import plan_ingest_semantic_execution
from sapi.ingest.records_writer import (
    IngestExtractionPersistResult,
    SourceIngestResult,
    ingest_source_artifacts_and_record,
    run_ingest_extraction_and_persist_canonical,
)
from sapi.ingest.source_content import SourceDateResolution, resolve_publication_date
from sapi.ingest.topic_generator import (
    TopicGenerationPersistResult,
    run_topic_generation_and_persist_canonical,
)
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import (
    SemanticBackendConfig,
    generate_semantic_json_live,
)
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
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--verbose", action="store_true")
    add_runtime_flag_arguments(parser)
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
    runtime_flags = None

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
        validate_runtime_flag_arguments(args)
        runtime_flags = snapshot_runtime_flags(args)
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=runtime_flags.mock_llm,
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
            _track_source_ingest_writes_for_rollback(
                transaction=transaction,
                result=result,
            )
            reference_result = run_reference_extraction_and_link_backfill(
                space_root=space_root,
                source_id=result.source_id,
            )
            if args.simulate_terminal_failure:
                raise RuntimeError("Simulated terminal ingest failure.")
            if not source_only:
                source_record = json.loads(result.record_path.read_text())
                source_title = resolve_display_title(
                    candidates=[
                        source_record.get("display_title") if isinstance(source_record, dict) else None,
                        source_record.get("title") if isinstance(source_record, dict) else None,
                    ],
                    fallback=result.source_id,
                )
                _record_semantic_invocation(
                    flow_key="ingest_extraction",
                    semantic_flows=semantic_flows,
                    semantic_flow_invocation_counts=semantic_flow_invocation_counts,
                )
                extraction_result = run_ingest_extraction_and_persist_canonical(
                    space_root=space_root,
                    source_id=result.source_id,
                    run_id=run_id,
                    llm_client=_build_ingest_extraction_client(
                        runtime_flags=runtime_flags,
                        source_id=result.source_id,
                        source_title=source_title,
                        source_date_resolution=source_date_resolution,
                        source_record=source_record if isinstance(source_record, dict) else {},
                    ),
                    trace_ctx=trace_ctx,
                )
                _track_ingest_extraction_writes_for_rollback(
                    transaction=transaction,
                    space_root=space_root,
                    run_id=run_id,
                    extraction_result=extraction_result,
                )
                llm_attempt_count += 1
                _record_semantic_invocation(
                    flow_key="topic_generation",
                    semantic_flows=semantic_flows,
                    semantic_flow_invocation_counts=semantic_flow_invocation_counts,
                )
                topic_result = run_topic_generation_and_persist_canonical(
                    space_root=space_root,
                    source_id=result.source_id,
                    run_id=run_id,
                    llm_client=_build_topic_generation_client(
                        runtime_flags=runtime_flags,
                        space_root=space_root,
                        source_id=result.source_id,
                        source_title=source_title,
                        claim_ids=[path.stem for path in extraction_result.claim_paths],
                    ),
                    trace_ctx=trace_ctx,
                )
                _track_topic_generation_writes_for_rollback(
                    transaction=transaction,
                    topic_result=topic_result,
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
        if space_root is not None and runtime_policy is not None and runtime_flags is not None:
            completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
            base = _make_run_base(
                run_id=run_id,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                execution_mode=runtime_policy.execution_mode,
                llm_backend=runtime_flags.llm_backend,
                llm_model=runtime_flags.llm_model,
                reasoning_effort=runtime_flags.llm_reasoning_effort,
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
                force_mode=bool(args.force),
                rollback_skipped=bool(args.force),
            )
            finalized = finalize_pipeline_run(
                space_root=space_root,
                base=base,
                flow_fields=flow_fields,
                transaction=transaction,
                force_mode=bool(args.force),
                summary=(
                    "Ingest failed in force mode; invocation artifacts preserved for forensics."
                    if args.force
                    else "Ingest failed; invocation-scoped outputs rolled back."
                ),
                errors=str(exc),
            )
            if args.force:
                print(
                    "scripts/ingest_source.py source ingested "
                    f"(execution_mode={runtime_policy.execution_mode}, "
                    f"run_id={run_id}, "
                    f"status={finalized.status}, "
                    f"run_record_path={finalized.run_record_path}, "
                    f"error={str(exc)})",
                    file=sys.stderr,
                )
            else:
                print(str(exc), file=sys.stderr)
            return finalized.exit_code
        print(str(exc), file=sys.stderr)
        return 1

    assert runtime_policy is not None
    assert runtime_flags is not None
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
        llm_backend=runtime_flags.llm_backend,
        llm_model=runtime_flags.llm_model,
        reasoning_effort=runtime_flags.llm_reasoning_effort,
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
            f", topic_ids={topic_result.topic_ids}, "
            f"topic_count={len(topic_result.topics)}"
        )
    if build_manifest_path is not None:
        summary += f", build_manifest_path={build_manifest_path}"
    summary += ")"
    summary += f" runtime_flags={runtime_flags_summary_dict(runtime_flags)}"
    print(summary)
    return finalized.exit_code


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
    llm_backend: str,
    llm_model: str,
    reasoning_effort: str,
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
        model_fingerprint="mock_semantic_fixture" if execution_mode == "mock_llm_test" else llm_model,
        provider_fingerprint="mock" if execution_mode == "mock_llm_test" else llm_backend,
        reasoning_effort=reasoning_effort,
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
        topic_pages_changed = len(topic_result.topics)
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


def _track_source_ingest_writes_for_rollback(
    *,
    transaction: ArtifactTransaction,
    result: SourceIngestResult,
) -> None:
    transaction.mark_create(result.source_artifact_path)
    transaction.mark_create(result.overview_markdown_path)
    if result.front_page_image_path is not None:
        transaction.mark_create(result.front_page_image_path)
    transaction.mark_create(result.record_path)


def _track_ingest_extraction_writes_for_rollback(
    *,
    transaction: ArtifactTransaction,
    space_root: Path,
    run_id: str,
    extraction_result: IngestExtractionPersistResult,
) -> None:
    transaction.mark_mkdir(space_root / "runs" / run_id)
    transaction.mark_create(extraction_result.semantic_output_path)
    for claim_path in extraction_result.claim_paths:
        transaction.mark_create(claim_path)
    for evidence_path in extraction_result.evidence_paths:
        transaction.mark_create(evidence_path)
    for relation_path in extraction_result.relation_paths:
        transaction.mark_create(relation_path)


def _track_topic_generation_writes_for_rollback(
    *,
    transaction: ArtifactTransaction,
    topic_result: TopicGenerationPersistResult,
) -> None:
    transaction.mark_create(topic_result.semantic_output_path)
    for topic_path in topic_result.topic_paths:
        transaction.mark_create(topic_path)


def _build_ingest_extraction_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    source_id: str,
    source_title: str | None,
    source_date_resolution: SourceDateResolution,
    source_record: dict[str, object],
):
    if runtime_flags.mock_llm:
        return _MockIngestExtractionClient(
            source_id=source_id,
            source_title=source_title,
            source_date_resolution=source_date_resolution,
        )
    return _LiveIngestExtractionClient(
        backend_config=_backend_config_from_runtime_flags(runtime_flags),
        source_id=source_id,
        source_title=source_title,
        source_date_resolution=source_date_resolution,
        source_record=source_record,
    )


def _build_topic_generation_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    space_root: Path,
    source_id: str,
    source_title: str | None,
    claim_ids: list[str],
):
    sources_context = _load_source_context(space_root=space_root)
    if runtime_flags.mock_llm:
        return _MockTopicGenerationClient(
            source_id=source_id,
            source_title=source_title,
            claim_ids=claim_ids,
            sources_context=sources_context,
        )
    claims_context = _load_claim_context(space_root=space_root)
    return _LiveTopicGenerationClient(
        backend_config=_backend_config_from_runtime_flags(runtime_flags),
        source_id=source_id,
        source_title=source_title,
        claim_ids=claim_ids,
        claims_context=claims_context,
        sources_context=sources_context,
    )


def _backend_config_from_runtime_flags(runtime_flags: RuntimeFlagSnapshot) -> SemanticBackendConfig:
    return SemanticBackendConfig(
        backend=runtime_flags.llm_backend,
        model=runtime_flags.llm_model,
        reasoning_effort=runtime_flags.llm_reasoning_effort,
        timeout_secs=runtime_flags.llm_timeout_secs,
    )


class _MockIngestExtractionClient:
    """Deterministic semantic client for explicit --mock-llm test mode."""

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
        display_title = resolve_display_title(
            candidates=[self._source_title],
            fallback=self._source_id,
        )
        payload = {
            "source_date_inference": dict(self._source_date_resolution.source_date_inference),
            "source": {
                "source_id": self._source_id,
                "title": self._source_title,
                "display_title": display_title,
            },
            "claims": [
                {
                    "text": f"Key proposition from `{self._source_title}` requires synthesis.",
                    "evidence_excerpts": [
                        "Mock theorem setup: under deterministic fixture assumptions, the extracted proposition "
                        "is treated as the central formal claim for this source."
                    ],
                }
            ],
            "evidence_items": [
                {
                    "evidence_id": "evidence-mock-core-proposition--0123456789ab",
                    "title": "Fixture theorem setup",
                    "excerpt": (
                        "Mock theorem setup: under deterministic fixture assumptions, the extracted proposition "
                        "is treated as the central formal claim for this source."
                    ),
                    "overview": (
                        "This mock evidence item anchors the claim in a formal fixture statement so deterministic "
                        "test runs exercise canonical evidence pages and claim-evidence linking."
                    ),
                    "evidence_type": "formal_argument",
                    "claim_refs": ["0"],
                    "source_id": self._source_id,
                    "page_refs": ["p.1"],
                }
            ],
            "relations": [],
            "summary": "Mock ingest extraction completed.",
            "source_dossier": {
                "summary_short": (
                    f"{display_title} proposes a central argument that is captured by the extracted claims."
                ),
                "summary_long": (
                    f"{display_title} is represented in mock mode with a conservative overview that keeps the "
                    "source argument, evidence path, and practical interpretation explicit for readers who "
                    "need a quick understanding before opening the PDF. The long-form narrative is intentionally "
                    "verbose so the source page can exercise full dossier rendering behavior in deterministic "
                    "test environments, including section hierarchy, metadata adjacency, and grounded-claim "
                    "link slots.\n\n"
                    "In this scaffold, the argument is framed in plain language, then expanded into method and "
                    "evidence interpretation, followed by assumptions, limitations, and transfer guidance. "
                    "That shape mirrors the production expectation that users can absorb a substantial overview "
                    "without immediately opening the primary document, while still preserving an audit trail "
                    "into canonical claim artifacts.\n\n"
                    "This dossier is deterministic scaffold content intended to satisfy contract shape and "
                    "rendering behavior in tests and local workflows. It prioritizes readability, explicit "
                    "boundary conditions, and stable output length over novelty so contract tests can assert "
                    "the presence of long-form commentary blocks with predictable section anchors."
                ),
                "sections": [
                    {
                        "heading": "What the Source Argues",
                        "body": (
                            f"The source frames a core thesis around {display_title} and the extracted claims "
                            "capture the most direct statement of that thesis. This section provides a concise "
                            "argument map so readers can understand the principal claim before reviewing any "
                            "detailed evidence links or relation records."
                        ),
                        "grounding_claim_ids": [],
                    },
                    {
                        "heading": "How the Argument Is Built",
                        "body": (
                            "The reasoning sequence is represented through claim extraction and relation "
                            "normalization, allowing downstream pages to link commentary back to canonical evidence. "
                            "In production, this section should make explicit where inference steps are strongest "
                            "and where assumptions are doing most of the explanatory work."
                        ),
                        "grounding_claim_ids": [],
                    },
                    {
                        "heading": "Evidence and Interpretation",
                        "body": (
                            "Evidence handling in this scaffold is intentionally conservative: claims are linked "
                            "as explicit references and no new factual assertions are introduced beyond extracted "
                            "content. The goal is to demonstrate commentary structure, not to synthesize new facts."
                        ),
                        "grounding_claim_ids": [],
                    },
                    {
                        "heading": "Assumptions and Limitations",
                        "body": (
                            "Readers should validate scope conditions, assumptions, and evidentiary limits before "
                            "transferring these conclusions into broader cross-source synthesis. This section calls "
                            "out where argument portability may fail when context changes."
                        ),
                        "grounding_claim_ids": [],
                    },
                    {
                        "heading": "How to Use This Source in the Space",
                        "body": (
                            "Use this source as a traceable evidence anchor in topic pages and claim references. "
                            "Start with the summary for orientation, then inspect grounded claim links to verify "
                            "that any downstream synthesis remains faithful to source scope."
                        ),
                        "grounding_claim_ids": [],
                    },
                ],
            },
            "warnings": list(self._source_date_resolution.warnings),
        }
        return json.dumps(payload)


class _LiveIngestExtractionClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        source_id: str,
        source_title: str | None,
        source_date_resolution: SourceDateResolution,
        source_record: dict[str, object],
    ) -> None:
        self._backend_config = backend_config
        self._source_id = source_id
        self._source_title = source_title or source_id
        self._source_date_resolution = source_date_resolution
        self._source_record = source_record

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "must_include_source_id": self._source_id,
                    "must_include_source_title": self._source_title,
                    "minimum_claim_count": 3,
                    "maximum_claim_count": 12,
                    "source_dossier_policy": (
                        "Include source_dossier with summary_short, summary_long, and sectioned commentary "
                        "grounded in extracted claims whenever evidence quality allows."
                    ),
                    "source_dossier_depth_target": (
                        "Write summary_long at substantial depth (>=900 chars) and produce 5..8 sections "
                        "with concrete analysis rather than generic restatement."
                    ),
                    "relation_policy": (
                        "Emit relations only when src/dst claims are grounded and can reference "
                        "generated claim indices or IDs."
                    ),
                    "evidence_items_policy": (
                        "Emit canonical evidence_items that are concrete artifacts (measurement/proof/equation/"
                        "table/figure/formal argument), each with evidence_id/title/excerpt/overview/"
                        "evidence_type/claim_refs/source_id."
                    ),
                },
                "source_date_inference": dict(self._source_date_resolution.source_date_inference),
                "source_date_warnings": list(self._source_date_resolution.warnings),
                "source_record": self._source_record,
            },
        )


class _MockTopicGenerationClient:
    """Deterministic topic-generation client for explicit --mock-llm mode."""

    def __init__(
        self,
        *,
        source_id: str,
        source_title: str | None,
        claim_ids: list[str],
        sources_context: list[dict[str, object]],
    ) -> None:
        self._source_id = source_id
        self._source_title = source_title or source_id
        self._claim_ids = claim_ids
        self._sources_context = sources_context

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        related_source_ids = [
            str(row.get("source_id"))
            for row in self._sources_context
            if isinstance(row, dict) and str(row.get("source_id")) not in ("", self._source_id)
        ]
        topics: list[dict[str, object]] = []
        if related_source_ids:
            topics = [
                {
                    "title": f"Shared concept: {self._source_title}",
                    "structure_type": "wiki",
                    "sections": [
                        {
                            "heading": "Summary",
                            "body": (
                                f"Mock cross-source synthesis for `{self._source_title}`."
                            ),
                        }
                    ],
                    "claim_ids": list(self._claim_ids),
                    "source_ids": [self._source_id, related_source_ids[0]],
                }
            ]
        payload = {"topics": topics}
        return json.dumps(payload)


class _LiveTopicGenerationClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        source_id: str,
        source_title: str | None,
        claim_ids: list[str],
        claims_context: list[dict[str, object]],
        sources_context: list[dict[str, object]],
    ) -> None:
        self._backend_config = backend_config
        self._source_id = source_id
        self._source_title = source_title or source_id
        self._claim_ids = list(claim_ids)
        self._claims_context = claims_context
        self._sources_context = sources_context

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "must_include_ingested_source_id_per_topic": self._source_id,
                    "must_include_claim_ids_from_ingested_source": self._claim_ids,
                    "source_cardinality_policy": (
                        "Each topic must include at least two distinct source_ids; "
                        "if no cross-source concept is justified, emit topics=[]"
                    ),
                    "target_style": (
                        "Generate 0..n topics as synthesis-worthy shared concepts across sources."
                    ),
                },
                "seed_source": {
                    "source_id": self._source_id,
                    "source_title": self._source_title,
                },
                "available_sources": self._sources_context,
                "available_claims": self._claims_context,
            },
        )


def _load_claim_context(*, space_root: Path, limit: int = 180) -> list[dict[str, object]]:
    claims_root = space_root / "claims"
    if not claims_root.is_dir():
        return []
    claim_rows: list[dict[str, object]] = []
    for claim_path in sorted(claims_root.glob("claim-*.json"))[:limit]:
        try:
            payload = json.loads(claim_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        claim_rows.append(
            {
                "claim_id": payload.get("claim_id"),
                "source_id": payload.get("source_id"),
                "text": payload.get("text"),
                "evidence_excerpts": payload.get("evidence_excerpts"),
            }
        )
    return claim_rows


def _load_source_context(*, space_root: Path, limit: int = 80) -> list[dict[str, object]]:
    sources_root = space_root / "sources" / "records"
    if not sources_root.is_dir():
        return []
    source_rows: list[dict[str, object]] = []
    for source_path in sorted(sources_root.glob("source-*.json"))[:limit]:
        try:
            payload = json.loads(source_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        source_semantic = payload.get("source_semantic")
        display_title = resolve_display_title(
            candidates=[
                payload.get("display_title"),
                source_semantic.get("display_title") if isinstance(source_semantic, dict) else None,
                source_semantic.get("article_title") if isinstance(source_semantic, dict) else None,
                payload.get("title"),
            ],
            fallback=payload.get("source_id"),
        )
        source_rows.append(
            {
                "source_id": payload.get("source_id"),
                "title": display_title,
                "date": payload.get("date"),
                "summary": payload.get("summary"),
                "article_kind": payload.get("article_kind"),
                "citation_count": payload.get("citation_count"),
            }
        )
    return source_rows


if __name__ == "__main__":
    raise SystemExit(main())
