#!/usr/bin/env python3
"""Overview generation pipeline entrypoint (TODO-0339 scope)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc, make_run_id
from sapi.contracts.run_envelopes import OverviewRunFields, RunEnvelopeBase
from sapi.core.pipeline_policy import finalize_pipeline_run
from sapi.core.pipeline_runtime import (
    add_llm_attempts,
    build_run_envelope_base,
    record_semantic_invocation,
    track_path_for_write,
    write_json_with_transaction,
)
from sapi.core.registry import (
    resolve_registry_path,
    resolve_site_path_from_registry,
    resolve_space_root,
)
from sapi.core.runtime_flags import (
    RuntimeFlagSnapshot,
    add_runtime_flag_arguments,
    runtime_flags_summary_dict,
    snapshot_runtime_flags,
    validate_runtime_flag_arguments,
)
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.core.transactions import ArtifactTransaction
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import SemanticBackendConfig, generate_semantic_json_live
from sapi.llm.semantic_executor import build_semantic_spec_from_contract, run_semantic_flow
from sapi.overview.overview_pipeline import (
    build_overview_context_payload,
    load_overview_inputs,
    render_overview_article_markdown,
    resolve_overview_scope,
    validate_overview_semantic_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
    add_runtime_flag_arguments(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    run_id = make_run_id()
    transaction = ArtifactTransaction()
    toolchain_versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    semantic_flows: list[str] = []
    semantic_flow_invocation_counts: dict[str, int] = {}
    llm_attempt_count = 0

    overview_scope = None
    overview_inputs = None
    context_path: Path | None = None
    article_path: Path | None = None

    try:
        validate_runtime_flag_arguments(args)
        runtime_flags = snapshot_runtime_flags(args)
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=runtime_flags.mock_llm,
            env=os.environ,
        )
        registry_path = resolve_registry_path(args.registry_path)
        site_path = resolve_site_path_from_registry(registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        overview_scope = resolve_overview_scope(site_path=site_path, space_name=args.space_name)
        overview_inputs = load_overview_inputs(space_root=space_root, scope=overview_scope)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    overview_output_root = space_root / "outputs" / "space_overview" / overview_scope.overview_id
    context_path = overview_output_root / "context.json"
    article_path = overview_output_root / "article.md"

    try:
        _ensure_overview_output_root(overview_output_root, transaction=transaction)
        context_payload = build_overview_context_payload(
            scope=overview_scope,
            inputs=overview_inputs,
            generated_at=started_at,
        )
        write_json_with_transaction(context_path, context_payload, transaction=transaction)

        record_semantic_invocation(
            flow_key="space_overview_generation",
            semantic_flows=semantic_flows,
            semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        )
        semantic_spec = build_semantic_spec_from_contract(
            "space_overview_generation",
            repo_root=_REPO_ROOT,
            path_tokens={
                "space_root": space_root,
                "overview_id": overview_scope.overview_id,
            },
        )
        if semantic_spec.output_json_path.resolve() != (overview_output_root / "overview.json").resolve():
            raise RuntimeError(
                "space_overview_generation semantic output path drifted from canonical overview artifact path."
            )
        track_path_for_write(semantic_spec.output_json_path, transaction=transaction)
        overview_client = _build_overview_client(
            runtime_flags=runtime_flags,
            scope=overview_scope,
            inputs=overview_inputs,
            generated_at=started_at,
        )
        semantic_payload, attempt_count = run_semantic_flow(
            spec=semantic_spec,
            llm_client=overview_client,
        )
        llm_attempt_count = add_llm_attempts(
            llm_attempt_count=llm_attempt_count,
            attempt_count=attempt_count,
        )
        validate_overview_semantic_payload(
            payload=semantic_payload,
            scope=overview_scope,
            inputs=overview_inputs,
        )

        article_markdown = render_overview_article_markdown(semantic_payload)
        track_path_for_write(article_path, transaction=transaction)
        article_path.write_text(article_markdown)

        if args.simulate_terminal_failure:
            raise RuntimeError("Simulated terminal overview failure.")
    except Exception as exc:
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
        flow_fields = _make_flow_fields(
            scope=overview_scope,
            inputs=overview_inputs,
            article_path=article_path,
        )
        finalized = finalize_pipeline_run(
            space_root=space_root,
            base=base,
            flow_fields=flow_fields,
            transaction=transaction,
            force_mode=False,
            summary="Overview generation failed; invocation-scoped outputs rolled back.",
            errors=str(exc),
        )
        print(
            "scripts/generate_overview.py overview failed "
            f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
            f"overview_id={overview_scope.overview_id}, status={finalized.status}, "
            f"runtime_flags={runtime_flags_summary_dict(runtime_flags)}, error={exc})",
            file=sys.stderr,
        )
        return finalized.exit_code

    warnings = context_payload["warnings"]
    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    status = "success_with_warnings" if warnings else "success"
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
    flow_fields = _make_flow_fields(
        scope=overview_scope,
        inputs=overview_inputs,
        article_path=article_path,
    )
    finalized = finalize_pipeline_run(
        space_root=space_root,
        base=base,
        flow_fields=flow_fields,
        transaction=transaction,
        force_mode=False,
        summary="Overview generation completed successfully.",
        changes=(
            f"overview_id={overview_scope.overview_id}, scope_kind={overview_scope.scope_kind}, "
            f"source_records_used={len(overview_inputs.source_records)}, claims_used={len(overview_inputs.claims)}, "
            f"relations_used={len(overview_inputs.relations)}, topics_used={len(overview_inputs.topics)}"
        ),
        lint_summary="lint_error_count=0 lint_warning_count=0 lint_info_count=0",
        errors="",
    )
    print(
        "scripts/generate_overview.py overview complete "
        f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
        f"overview_id={overview_scope.overview_id}, scope_kind={overview_scope.scope_kind}, "
        f"run_record_path={finalized.run_record_path}, "
        f"runtime_flags={runtime_flags_summary_dict(runtime_flags)})"
    )
    return finalized.exit_code


def _make_run_base(
    *,
    run_id: str,
    status: str,
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
    return build_run_envelope_base(
        run_id=run_id,
        flow_key="overview_pipeline",
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        execution_mode=execution_mode,
        llm_backend=llm_backend,
        llm_model=llm_model,
        reasoning_effort=reasoning_effort,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )


def _make_flow_fields(
    *,
    scope,
    inputs,
    article_path: Path | None,
) -> OverviewRunFields:
    return OverviewRunFields(
        overview_id=scope.overview_id,
        scope_kind=scope.scope_kind,
        scope_name=scope.scope_name,
        source_records_used=len(inputs.source_records),
        claims_used=len(inputs.claims),
        relations_used=len(inputs.relations),
        topics_used=len(inputs.topics),
        article_path=str(article_path.resolve()) if article_path is not None else None,
    )


def _ensure_overview_output_root(path: Path, *, transaction: ArtifactTransaction) -> None:
    if path.exists():
        if not path.is_dir():
            raise RuntimeError(f"Overview output root is not a directory: {path}")
        return
    path.mkdir(parents=True, exist_ok=False)
    transaction.mark_mkdir(path)


def _build_overview_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    scope,
    inputs,
    generated_at: str,
):
    if runtime_flags.mock_llm:
        return _MockOverviewClient(
            scope=scope,
            inputs=inputs,
            generated_at=generated_at,
        )
    return _LiveOverviewClient(
        backend_config=SemanticBackendConfig(
            backend=runtime_flags.llm_backend,
            model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            timeout_secs=runtime_flags.llm_timeout_secs,
        ),
        scope=scope,
        inputs=inputs,
        generated_at=generated_at,
    )


class _MockOverviewClient:
    def __init__(self, *, scope, inputs, generated_at: str) -> None:
        self._scope = scope
        self._inputs = inputs
        self._generated_at = generated_at

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        citation_anchors = _build_mock_citation_anchors(self._inputs)
        anchor_ids = [row["anchor_id"] for row in citation_anchors]
        warnings = _build_mock_warnings(self._inputs)
        sections: list[dict[str, object]] = []
        source_ids = list(self._inputs.source_ids[: min(3, len(self._inputs.source_ids))])
        claim_ids = list(self._inputs.claim_ids[: min(6, len(self._inputs.claim_ids))])
        for section_id, heading in (
            ("topic_framing", "Topic framing"),
            ("key_themes", "Key themes"),
            ("agreement_and_disagreement", "Agreement and disagreement"),
            ("methods_and_evidence", "Methods and evidence"),
            ("open_questions", "Open questions"),
        ):
            sections.append(
                {
                    "section_id": section_id,
                    "heading": heading,
                    "body": _mock_section_body(
                        section_id=section_id,
                        scope_name=self._scope.scope_name,
                        source_count=len(self._inputs.source_records),
                        claim_count=len(self._inputs.claims),
                        relation_count=len(self._inputs.relations),
                        topic_count=len(self._inputs.topics),
                    ),
                    "source_ids": source_ids,
                    "claim_ids": claim_ids,
                    "citation_anchor_ids": list(anchor_ids),
                }
            )
        title = (
            f"State of the Evidence in {self._scope.title}"
            if self._scope.title
            else f"State of the Evidence in {self._scope.scope_name}"
        )
        payload = {
            "schema_version": "space_overview_v1",
            "metadata": {
                "overview_id": self._scope.overview_id,
                "scope_kind": self._scope.scope_kind,
                "space_name": self._scope.space_name,
                "scope_name": self._scope.scope_name,
                "title": title,
                "summary": _mock_summary(scope=self._scope, inputs=self._inputs),
            },
            "sections": sections,
            "references": {
                "source_ids": list(self._inputs.source_ids),
                "claim_ids": list(self._inputs.claim_ids),
                "citation_anchors": citation_anchors,
            },
            "freshness": {
                "generated_at": self._generated_at,
                "input_signature": self._inputs.input_signature,
                "source_record_count": len(self._inputs.source_records),
                "claim_count": len(self._inputs.claims),
                "relation_count": len(self._inputs.relations),
                "topic_count": len(self._inputs.topics),
            },
            "warnings": warnings,
        }
        return json.dumps(payload)


class _LiveOverviewClient:
    def __init__(self, *, backend_config: SemanticBackendConfig, scope, inputs, generated_at: str) -> None:
        self._backend_config = backend_config
        self._scope = scope
        self._inputs = inputs
        self._generated_at = generated_at

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "overview_id": self._scope.overview_id,
                    "scope_kind": self._scope.scope_kind,
                    "space_name": self._scope.space_name,
                    "scope_name": self._scope.scope_name,
                    "parent_space_name": self._scope.parent_space_name,
                    "generated_at": self._generated_at,
                    "input_signature": self._inputs.input_signature,
                    "source_record_count": len(self._inputs.source_records),
                    "claim_count": len(self._inputs.claims),
                    "relation_count": len(self._inputs.relations),
                    "topic_count": len(self._inputs.topics),
                    "required_section_ids": [
                        "topic_framing",
                        "key_themes",
                        "agreement_and_disagreement",
                        "methods_and_evidence",
                        "open_questions",
                    ],
                    "no_source_context": not self._inputs.source_records,
                }
            },
        )


def _build_mock_citation_anchors(inputs) -> list[dict[str, object]]:
    anchors: list[dict[str, object]] = []
    for index, source_id in enumerate(inputs.source_ids[: min(3, len(inputs.source_ids))], start=1):
        related_claim_ids = list(inputs.claim_ids[: min(2, len(inputs.claim_ids))])
        anchors.append(
            {
                "anchor_id": f"anchor-s{index}",
                "label": f"[S{index}]",
                "source_id": source_id,
                "claim_ids": related_claim_ids,
                "locator": None,
            }
        )
    return anchors


def _build_mock_warnings(inputs) -> list[str]:
    warnings: list[str] = []
    if not inputs.source_records:
        warnings.append("No ingested source records are available for this scope yet.")
    if not inputs.claims:
        warnings.append("No canonical claims are available for this scope yet.")
    if not inputs.topics:
        warnings.append("No canonical topic pages are available for this scope yet.")
    return warnings


def _mock_summary(*, scope, inputs) -> str:
    if not inputs.source_records:
        return (
            f"No ingested source records are available yet for `{scope.scope_name}`. "
            "Run ingest before relying on this overview."
        )
    return (
        f"Overview for `{scope.scope_name}` synthesized from {len(inputs.source_records)} source records, "
        f"{len(inputs.claims)} claims, {len(inputs.relations)} relations, and {len(inputs.topics)} topics."
    )


def _mock_section_body(
    *,
    section_id: str,
    scope_name: str,
    source_count: int,
    claim_count: int,
    relation_count: int,
    topic_count: int,
) -> str:
    if source_count == 0:
        return (
            f"No ingested sources are available for `{scope_name}` yet, so this section records the current absence "
            "of evidence and the need for future ingest before synthesis can become substantive."
        )
    templates = {
        "topic_framing": (
            f"`{scope_name}` currently contains {source_count} source records and {topic_count} topic pages, "
            "which establish the main framing for the overview."
        ),
        "key_themes": (
            f"The available material clusters around {claim_count} canonical claims, surfacing the dominant themes "
            "captured by the current ingest set."
        ),
        "agreement_and_disagreement": (
            f"{relation_count} canonical relations provide the current map of agreement, contradiction, and "
            "remaining ambiguity across the synthesized claims."
        ),
        "methods_and_evidence": (
            "The methods and evidence landscape is constrained to canonical source records and the claim/relation "
            "graph already persisted for this scope."
        ),
        "open_questions": (
            "Open questions remain wherever the current sources are sparse, claims are weakly connected, or topic "
            "coverage is too thin to settle interpretation."
        ),
    }
    return templates[section_id]


if __name__ == "__main__":
    raise SystemExit(main())
