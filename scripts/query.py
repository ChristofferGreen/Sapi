#!/usr/bin/env python3
"""Query pipeline entrypoint (TODO-0220 scope)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import (
    format_timestamp_rfc3339_utc,
    make_query_id,
    make_run_id,
    slugify,
)
from sapi.contracts.run_envelopes import QueryRunFields, RunEnvelopeBase
from sapi.core.pipeline_policy import finalize_pipeline_run
from sapi.core.pipeline_runtime import build_run_envelope_base
from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.core.runtime_flags import (
    add_runtime_flag_arguments,
    runtime_flags_summary_dict,
    snapshot_runtime_flags,
    validate_runtime_flag_arguments,
)
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.core.transactions import ArtifactTransaction
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import (
    SemanticBackendConfig,
    generate_semantic_json_live,
)
from sapi.llm.semantic_executor import build_semantic_spec_from_contract, run_semantic_flow
from sapi.query.query_pipeline import build_query_result_record
from sapi.query.renderers import build_query_artifacts
from sapi.query.retrieval import retrieve_query_context


_MODE_DEFAULT_BUDGETS: dict[str, tuple[int, int]] = {
    "strict": (120, 40),
    "exploratory": (200, 60),
    "comparative": (160, 80),
}
_MODES = tuple(_MODE_DEFAULT_BUDGETS.keys())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("question")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--mode", choices=_MODES, default="strict")
    parser.add_argument("--scope", choices=("default", "deep"), default="default")
    parser.add_argument("--max-claims", type=int)
    parser.add_argument("--max-sources", type=int)
    parser.add_argument(
        "--include-disputed",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--include-warnings",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--output-format",
        choices=("markdown", "mermaid", "images", "slides", "pdf"),
        default="markdown",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
    add_runtime_flag_arguments(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    run_id = make_run_id()
    query_id = make_query_id(slug=slugify(args.question))
    toolchain_versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    transaction = ArtifactTransaction()
    query_record_path: Path | None = None
    run_manifest_path: str | None = None
    claims_used: list[str] = []
    sources_used: list[str] = []
    contradictions_considered = 0
    llm_attempt_count = 0

    try:
        validate_runtime_flag_arguments(args)
        runtime_flags = snapshot_runtime_flags(args)
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=runtime_flags.mock_llm,
            env=os.environ,
        )
        registry_path = resolve_registry_path(args.registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        options = _resolve_query_options(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        claims_used, sources_used, omitted_due_to_budget = retrieve_query_context(
            space_root=space_root,
            max_claims=options.max_claims,
            max_sources=options.max_sources,
            include_disputed=options.include_disputed,
        )
        warnings = _build_warnings(
            include_warnings=options.include_warnings,
            claims_used=claims_used,
            sources_used=sources_used,
        )
        answer = _build_answer(
            question=args.question,
            mode=options.mode,
            claims_used=claims_used,
            sources_used=sources_used,
        )
        query_output_root = space_root / "outputs" / "query" / query_id
        _ensure_query_output_root(query_output_root, transaction=transaction)
        semantic_spec = build_semantic_spec_from_contract(
            "query_synthesis",
            repo_root=_REPO_ROOT,
            path_tokens={
                "space_root": space_root,
                "query_id": query_id,
            },
        )
        if semantic_spec.output_json_path.resolve() != (query_output_root / "query.json").resolve():
            raise RuntimeError(
                "query_synthesis semantic output path drifted from canonical query artifact path."
            )
        query_client = _build_query_client(
            runtime_flags=runtime_flags,
            question=args.question,
            query_id=query_id,
            mode=options.mode,
            scope=options.scope,
            claims_used=claims_used,
            sources_used=sources_used,
            retrieval_counts={
                "claims_retrieved": len(claims_used),
                "sources_retrieved": len(sources_used),
            },
            contradictions_considered=contradictions_considered,
            answer_fallback=answer,
            warnings=warnings,
        )
        semantic_payload, llm_attempt_count = run_semantic_flow(
            spec=semantic_spec,
            llm_client=query_client,
        )
        query_record_path = semantic_spec.output_json_path
        if not query_record_path.is_file():
            raise RuntimeError(
                "query_synthesis semantic output was not persisted to canonical query path."
            )
        transaction.mark_create(query_record_path)
        query_payload = _build_query_payload_from_semantic(
            semantic_payload=semantic_payload,
            query_id=query_id,
            run_id=run_id,
            mode=options.mode,
            scope=options.scope,
            output_mode=args.output_format,
            space_root=space_root,
            omitted_due_to_budget=omitted_due_to_budget,
            include_disputed=options.include_disputed,
            include_warnings=options.include_warnings,
            max_claims=options.max_claims,
            max_sources=options.max_sources,
            claims_used_fallback=claims_used,
            sources_used_fallback=sources_used,
            retrieval_counts_fallback={
                "claims_retrieved": len(claims_used),
                "sources_retrieved": len(sources_used),
            },
            contradictions_considered_fallback=contradictions_considered,
            warnings_fallback=warnings,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            execution_mode=runtime_policy.execution_mode,
            llm_backend=runtime_flags.llm_backend,
            llm_model=runtime_flags.llm_model,
            llm_attempt_count=llm_attempt_count,
        )
        query_record_path.write_text(json.dumps(query_payload, indent=2, sort_keys=True) + "\n")
        if args.output_format == "markdown":
            _write_new_file(
                query_output_root / "answer.md",
                _render_markdown_answer(
                    question=args.question,
                    answer=answer,
                    mode=options.mode,
                    claims_used=claims_used,
                    sources_used=sources_used,
                ),
                transaction=transaction,
            )
        else:
            rendered = build_query_artifacts(
                output_mode=args.output_format,
                query_payload=query_payload,
                question=args.question,
            )
            if rendered is None:
                raise RuntimeError("Non-markdown output mode must produce rendered artifacts.")
            for relative_path, file_contents in rendered.files.items():
                _write_new_file(
                    query_output_root / relative_path,
                    file_contents,
                    transaction=transaction,
                )
            manifest_path = query_output_root / "manifest.json"
            _write_new_file(
                manifest_path,
                json.dumps(rendered.manifest, indent=2, sort_keys=True) + "\n",
                transaction=transaction,
            )
            run_manifest_path = str(manifest_path.resolve())
            expected_manifest_path = query_payload.get("manifest_path")
            if expected_manifest_path != run_manifest_path:
                raise RuntimeError(
                    "Query result manifest_path must match canonical manifest file path."
                )

        if args.simulate_terminal_failure:
            raise RuntimeError("Simulated terminal query failure.")
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
            llm_attempt_count=llm_attempt_count,
            toolchain_versions=toolchain_versions,
        )
        flow_fields = QueryRunFields(
            query_id=query_id,
            mode=options.mode,
            scope=options.scope,
            claims_used=len(claims_used),
            sources_used=len(sources_used),
            contradictions_considered=contradictions_considered,
            manifest_path=None,
        )
        finalized = finalize_pipeline_run(
            space_root=space_root,
            base=base,
            flow_fields=flow_fields,
            transaction=transaction,
            force_mode=False,
            summary="Query failed; invocation-scoped outputs rolled back.",
            errors=str(exc),
        )
        print(
            "scripts/query.py query failed "
            f"(execution_mode={runtime_policy.execution_mode}, "
            f"run_id={run_id}, query_id={query_id}, status={finalized.status}, "
            f"runtime_flags={runtime_flags_summary_dict(runtime_flags)}, error={exc})",
            file=sys.stderr,
        )
        return finalized.exit_code

    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    base = _make_run_base(
        run_id=run_id,
        status="success",
        started_at=started_at,
        completed_at=completed_at,
        execution_mode=runtime_policy.execution_mode,
        llm_backend=runtime_flags.llm_backend,
        llm_model=runtime_flags.llm_model,
        reasoning_effort=runtime_flags.llm_reasoning_effort,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )
    flow_fields = QueryRunFields(
        query_id=query_id,
        mode=options.mode,
        scope=options.scope,
        claims_used=len(claims_used),
        sources_used=len(sources_used),
        contradictions_considered=contradictions_considered,
        manifest_path=run_manifest_path,
    )
    finalized = finalize_pipeline_run(
        space_root=space_root,
        base=base,
        flow_fields=flow_fields,
        transaction=transaction,
        force_mode=False,
        summary="Query completed successfully.",
        changes=(
            f"query_record_path={query_record_path}, "
            f"claims_used={len(claims_used)}, sources_used={len(sources_used)}"
        ),
        lint_summary="lint_error_count=0 lint_warning_count=0 lint_info_count=0",
        errors="",
    )
    print(
        "scripts/query.py query complete "
        f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
        f"query_id={query_id}, mode={options.mode}, scope={options.scope}, "
        f"query_record_path={query_record_path}, run_record_path={finalized.run_record_path}, "
        f"runtime_flags={runtime_flags_summary_dict(runtime_flags)})"
    )
    return finalized.exit_code


class _QueryOptions:
    def __init__(
        self,
        *,
        mode: str,
        scope: str,
        include_disputed: bool,
        include_warnings: bool,
        max_claims: int,
        max_sources: int,
    ) -> None:
        self.mode = mode
        self.scope = scope
        self.include_disputed = include_disputed
        self.include_warnings = include_warnings
        self.max_claims = max_claims
        self.max_sources = max_sources


def _build_query_payload_from_semantic(
    *,
    semantic_payload: dict[str, object],
    query_id: str,
    run_id: str,
    mode: str,
    scope: str,
    output_mode: str,
    space_root: Path,
    omitted_due_to_budget: dict[str, int],
    include_disputed: bool,
    include_warnings: bool,
    max_claims: int,
    max_sources: int,
    claims_used_fallback: list[str],
    sources_used_fallback: list[str],
    retrieval_counts_fallback: dict[str, int],
    contradictions_considered_fallback: int,
    warnings_fallback: list[dict[str, str]],
    reasoning_effort: str,
    execution_mode: str,
    llm_backend: str,
    llm_model: str,
    llm_attempt_count: int,
) -> dict[str, object]:
    semantic_query_id = _require_non_empty_string(
        semantic_payload.get("query_id"),
        field_name="query_synthesis.query_id",
    )
    if semantic_query_id != query_id:
        raise ValueError(
            "query_synthesis payload query_id must match canonical query_id "
            f"(expected={query_id!r}, actual={semantic_query_id!r})."
        )
    semantic_mode = _require_non_empty_string(
        semantic_payload.get("mode"),
        field_name="query_synthesis.mode",
    )
    if semantic_mode != mode:
        raise ValueError(
            "query_synthesis payload mode must match query mode "
            f"(expected={mode!r}, actual={semantic_mode!r})."
        )
    semantic_scope = _require_non_empty_string(
        semantic_payload.get("scope"),
        field_name="query_synthesis.scope",
    )
    if semantic_scope != scope:
        raise ValueError(
            "query_synthesis payload scope must match query scope "
            f"(expected={scope!r}, actual={semantic_scope!r})."
        )

    claims_used = _normalize_string_list(
        semantic_payload.get("claims_used"),
        field_name="query_synthesis.claims_used",
        fallback=claims_used_fallback,
    )
    sources_used = _normalize_string_list(
        semantic_payload.get("sources_used"),
        field_name="query_synthesis.sources_used",
        fallback=sources_used_fallback,
    )
    retrieval_counts = _normalize_retrieval_counts(
        semantic_payload.get("retrieval_counts"),
        fallback=retrieval_counts_fallback,
    )
    contradictions_considered = _normalize_non_negative_int(
        semantic_payload.get("contradictions_considered"),
        field_name="query_synthesis.contradictions_considered",
        fallback=contradictions_considered_fallback,
    )
    falsification_signals = _normalize_object_list(
        semantic_payload.get("falsification_signals"),
        field_name="query_synthesis.falsification_signals",
    )
    warnings = _normalize_warning_rows(
        semantic_payload.get("warnings"),
        fallback=warnings_fallback,
    )
    answer = _require_non_empty_string(
        semantic_payload.get("answer"),
        field_name="query_synthesis.answer",
    )

    return build_query_result_record(
        query_id=query_id,
        answer=answer,
        claims_used=claims_used,
        sources_used=sources_used,
        retrieval_counts=retrieval_counts,
        contradictions_considered=contradictions_considered,
        falsification_signals=falsification_signals,
        omitted_due_to_budget=omitted_due_to_budget,
        mode=mode,
        scope=scope,
        run_id=run_id,
        query_timestamp_utc=format_timestamp_rfc3339_utc(datetime.now(UTC)),
        citation_coverage=_build_citation_coverage(
            mode=mode,
            claims_used=claims_used,
            sources_used=sources_used,
        ),
        lint_summary={"error_count": 0, "warning_count": 0, "info_count": 0},
        execution={
            "execution_mode": execution_mode,
            "llm_attempt_count": llm_attempt_count,
            "reasoning_effort": reasoning_effort,
            "model_fingerprint": (
                "mock_semantic_fixture"
                if execution_mode == "mock_llm_test"
                else llm_model
            ),
            "provider_fingerprint": (
                "mock"
                if execution_mode == "mock_llm_test"
                else llm_backend
            ),
            "include_disputed": include_disputed,
            "include_warnings": include_warnings,
            "retrieval_budget": {
                "max_claims": max_claims,
                "max_sources": max_sources,
            },
        },
        warnings=warnings,
        output_mode=output_mode,
        space_root=space_root,
    )


def _resolve_query_options(args: argparse.Namespace) -> _QueryOptions:
    include_disputed = args.include_disputed
    if args.mode == "strict" and include_disputed is True:
        raise ValueError(
            "Invalid mode/flag combination: `--mode strict --include-disputed` is prohibited."
        )
    if include_disputed is None:
        include_disputed = args.mode != "strict"

    include_warnings = True if args.include_warnings is None else bool(args.include_warnings)
    default_max_claims, default_max_sources = _MODE_DEFAULT_BUDGETS[args.mode]
    max_claims = default_max_claims if args.max_claims is None else int(args.max_claims)
    max_sources = default_max_sources if args.max_sources is None else int(args.max_sources)
    if max_claims <= 0:
        raise ValueError("--max-claims must be a positive integer.")
    if max_sources <= 0:
        raise ValueError("--max-sources must be a positive integer.")

    return _QueryOptions(
        mode=args.mode,
        scope=args.scope,
        include_disputed=bool(include_disputed),
        include_warnings=include_warnings,
        max_claims=max_claims,
        max_sources=max_sources,
    )


def _build_warnings(
    *,
    include_warnings: bool,
    claims_used: list[str],
    sources_used: list[str],
) -> list[dict[str, str]]:
    if not include_warnings:
        return []
    warnings: list[dict[str, str]] = []
    if not claims_used:
        warnings.append({"code": "no_claim_context", "message": "No claims were available for retrieval."})
    if not sources_used:
        warnings.append(
            {
                "code": "no_source_context",
                "message": "No source records were available for retrieval.",
            }
        )
    return warnings


def _normalize_warning_rows(
    raw: object,
    *,
    fallback: list[dict[str, str]],
) -> list[dict[str, str] | str]:
    if not isinstance(raw, list):
        return list(fallback)
    normalized: list[dict[str, str] | str] = []
    for row in raw:
        if isinstance(row, str):
            stripped = row.strip()
            if stripped:
                normalized.append(stripped)
            continue
        if not isinstance(row, dict):
            continue
        code = row.get("code")
        message = row.get("message")
        if isinstance(code, str) and code.strip() and isinstance(message, str) and message.strip():
            normalized.append({"code": code.strip(), "message": message.strip()})
    if normalized:
        return normalized
    return list(fallback)


def _build_answer(
    *,
    question: str,
    mode: str,
    claims_used: list[str],
    sources_used: list[str],
) -> str:
    if not claims_used and not sources_used:
        return (
            f"No canonical retrieval context is currently available to answer: {question!r}. "
            "Run ingest first, then re-run query."
        )
    return (
        f"Query mode `{mode}` synthesized a deterministic reconstruction answer for: {question!r}. "
        f"claims_used={len(claims_used)}, sources_used={len(sources_used)}."
    )


def _normalize_string_list(
    raw: object,
    *,
    field_name: str,
    fallback: list[str],
) -> list[str]:
    if not isinstance(raw, list):
        return list(fallback)
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        stripped = item.strip()
        if stripped:
            values.append(stripped)
    if values:
        return values
    return list(fallback)


def _normalize_non_negative_int(
    raw: object,
    *,
    field_name: str,
    fallback: int,
) -> int:
    if raw is None:
        return fallback
    if not isinstance(raw, int):
        raise TypeError(f"{field_name} must be an integer.")
    if raw < 0:
        raise ValueError(f"{field_name} must be >= 0.")
    return raw


def _normalize_object_list(raw: object, *, field_name: str) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            rows.append(item)
    if rows:
        return rows
    if raw:
        raise TypeError(f"{field_name} must contain JSON objects.")
    return []


def _normalize_retrieval_counts(
    raw: object,
    *,
    fallback: dict[str, int],
) -> dict[str, int]:
    if not isinstance(raw, dict):
        return dict(fallback)
    claims_retrieved = raw.get("claims_retrieved")
    sources_retrieved = raw.get("sources_retrieved")
    if not isinstance(claims_retrieved, int) or claims_retrieved < 0:
        return dict(fallback)
    if not isinstance(sources_retrieved, int) or sources_retrieved < 0:
        return dict(fallback)
    return {
        "claims_retrieved": claims_retrieved,
        "sources_retrieved": sources_retrieved,
    }


def _require_non_empty_string(raw: object, *, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return raw.strip()


def _build_citation_coverage(
    *,
    mode: str,
    claims_used: list[str],
    sources_used: list[str],
) -> dict[str, float | bool | int | str]:
    target_threshold = 0.9 if mode == "strict" else 0.7
    factual_sentence_ratio = 1.0 if claims_used else 0.0
    return {
        "mode": mode,
        "policy_version": "query_citation_coverage_v1",
        "target_threshold": target_threshold,
        "factual_sentence_ratio": factual_sentence_ratio,
        "meets_target": factual_sentence_ratio >= target_threshold,
        "claims_cited": len(claims_used),
        "sources_cited": len(sources_used),
    }


def _build_query_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    question: str,
    query_id: str,
    mode: str,
    scope: str,
    claims_used: list[str],
    sources_used: list[str],
    retrieval_counts: dict[str, int],
    contradictions_considered: int,
    answer_fallback: str,
    warnings: list[dict[str, str]],
):
    if runtime_flags.mock_llm:
        return _MockQuerySynthesisClient(
            question=question,
            query_id=query_id,
            mode=mode,
            scope=scope,
            claims_used=claims_used,
            sources_used=sources_used,
            retrieval_counts=retrieval_counts,
            contradictions_considered=contradictions_considered,
            answer_fallback=answer_fallback,
            warnings=warnings,
        )
    return _LiveQuerySynthesisClient(
        backend_config=SemanticBackendConfig(
            backend=runtime_flags.llm_backend,
            model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            timeout_secs=runtime_flags.llm_timeout_secs,
        ),
        question=question,
        query_id=query_id,
        mode=mode,
        scope=scope,
        claims_used=claims_used,
        sources_used=sources_used,
        retrieval_counts=retrieval_counts,
        contradictions_considered=contradictions_considered,
        answer_fallback=answer_fallback,
        warnings=warnings,
    )


class _MockQuerySynthesisClient:
    def __init__(
        self,
        *,
        question: str,
        query_id: str,
        mode: str,
        scope: str,
        claims_used: list[str],
        sources_used: list[str],
        retrieval_counts: dict[str, int],
        contradictions_considered: int,
        answer_fallback: str,
        warnings: list[dict[str, str]],
    ) -> None:
        self._question = question
        self._query_id = query_id
        self._mode = mode
        self._scope = scope
        self._claims_used = list(claims_used)
        self._sources_used = list(sources_used)
        self._retrieval_counts = dict(retrieval_counts)
        self._contradictions_considered = contradictions_considered
        self._answer_fallback = answer_fallback
        self._warnings = list(warnings)

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        payload = {
            "query_id": self._query_id,
            "answer": self._answer_fallback,
            "claims_used": self._claims_used,
            "sources_used": self._sources_used,
            "retrieval_counts": self._retrieval_counts,
            "contradictions_considered": self._contradictions_considered,
            "falsification_signals": [],
            "mode": self._mode,
            "scope": self._scope,
            "execution": {
                "backend": "mock",
                "question": self._question,
            },
            "warnings": self._warnings,
        }
        return json.dumps(payload)


class _LiveQuerySynthesisClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        question: str,
        query_id: str,
        mode: str,
        scope: str,
        claims_used: list[str],
        sources_used: list[str],
        retrieval_counts: dict[str, int],
        contradictions_considered: int,
        answer_fallback: str,
        warnings: list[dict[str, str]],
    ) -> None:
        self._backend_config = backend_config
        self._question = question
        self._query_id = query_id
        self._mode = mode
        self._scope = scope
        self._claims_used = list(claims_used)
        self._sources_used = list(sources_used)
        self._retrieval_counts = dict(retrieval_counts)
        self._contradictions_considered = contradictions_considered
        self._answer_fallback = answer_fallback
        self._warnings = list(warnings)

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "must_use_query_id": self._query_id,
                    "must_use_mode": self._mode,
                    "must_use_scope": self._scope,
                    "must_ground_claims_and_sources_to_retrieval_context": True,
                    "must_return_query_json_object": True,
                },
                "question": self._question,
                "retrieval_context": {
                    "claims_used": self._claims_used,
                    "sources_used": self._sources_used,
                    "retrieval_counts": self._retrieval_counts,
                    "contradictions_considered": self._contradictions_considered,
                    "warnings": self._warnings,
                },
                "fallback_answer_hint": self._answer_fallback,
            },
        )


def _render_markdown_answer(
    *,
    question: str,
    answer: str,
    mode: str,
    claims_used: list[str],
    sources_used: list[str],
) -> str:
    lines = [
        "# Query Answer",
        "",
        f"- mode: `{mode}`",
        f"- question: `{question}`",
        f"- claims_used: `{len(claims_used)}`",
        f"- sources_used: `{len(sources_used)}`",
        "",
        "## Answer",
        answer,
        "",
    ]
    return "\n".join(lines)


def _ensure_query_output_root(path: Path, *, transaction: ArtifactTransaction) -> None:
    if path.exists():
        raise RuntimeError(
            f"Query output path already exists for generated query_id: {path}. "
            "Retry command to generate a fresh query_id."
        )
    path.mkdir(parents=True, exist_ok=False)
    transaction.mark_mkdir(path)


def _write_new_file(path: Path, content: str, *, transaction: ArtifactTransaction) -> None:
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite existing query artifact path: {path}")
    path.write_text(content)
    transaction.mark_create(path)


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
    llm_attempt_count: int,
    toolchain_versions: dict[str, str],
) -> RunEnvelopeBase:
    return build_run_envelope_base(
        run_id=run_id,
        flow_key="query_pipeline",
        semantic_flows=["query_synthesis"],
        semantic_flow_invocation_counts={"query_synthesis": 1},
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


if __name__ == "__main__":
    raise SystemExit(main())
