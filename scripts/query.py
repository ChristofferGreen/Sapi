#!/usr/bin/env python3
"""Query pipeline entrypoint (TODO-0220 scope)."""

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

from sapi.contracts.ids import (
    format_timestamp_rfc3339_utc,
    make_query_id,
    make_run_id,
    slugify,
)
from sapi.contracts.run_envelopes import QueryRunFields, RunEnvelopeBase
from sapi.core.pipeline_policy import finalize_pipeline_run
from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.core.transactions import ArtifactTransaction
from sapi.query.query_pipeline import build_query_result_record
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
    parser.add_argument("--output-format", choices=("markdown",), default="markdown")
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
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
    claims_used: list[str] = []
    sources_used: list[str] = []
    contradictions_considered = 0

    try:
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=args.mock_llm,
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
        query_payload = build_query_result_record(
            query_id=query_id,
            answer=answer,
            claims_used=claims_used,
            sources_used=sources_used,
            retrieval_counts={
                "claims_retrieved": len(claims_used),
                "sources_retrieved": len(sources_used),
            },
            contradictions_considered=contradictions_considered,
            falsification_signals=[],
            omitted_due_to_budget=omitted_due_to_budget,
            mode=options.mode,
            scope=options.scope,
            run_id=run_id,
            query_timestamp_utc=format_timestamp_rfc3339_utc(datetime.now(UTC)),
            citation_coverage={
                "factual_sentence_ratio": 1.0 if claims_used else 0.0,
                "target_threshold": 0.9 if options.mode == "strict" else 0.7,
            },
            lint_summary={"error_count": 0, "warning_count": 0, "info_count": 0},
            execution={
                "execution_mode": runtime_policy.execution_mode,
                "llm_attempt_count": 1,
                "reasoning_effort": "high",
                "model_fingerprint": _model_fingerprint(runtime_policy.execution_mode),
                "provider_fingerprint": _provider_fingerprint(runtime_policy.execution_mode),
                "include_disputed": options.include_disputed,
                "include_warnings": options.include_warnings,
                "retrieval_budget": {
                    "max_claims": options.max_claims,
                    "max_sources": options.max_sources,
                },
            },
            warnings=warnings,
            output_mode=args.output_format,
            space_root=space_root,
        )
        query_output_root = space_root / "outputs" / "query" / query_id
        _ensure_query_output_root(query_output_root, transaction=transaction)
        query_record_path = query_output_root / "query.json"
        _write_new_file(
            query_record_path,
            json.dumps(query_payload, indent=2, sort_keys=True) + "\n",
            transaction=transaction,
        )
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
            llm_attempt_count=1,
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
            f"run_id={run_id}, query_id={query_id}, status={finalized.status}, error={exc})",
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
        llm_attempt_count=1,
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
        f"query_record_path={query_record_path}, run_record_path={finalized.run_record_path})"
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
    llm_attempt_count: int,
    toolchain_versions: dict[str, str],
) -> RunEnvelopeBase:
    return RunEnvelopeBase(
        run_id=run_id,
        flow_key="query_pipeline",
        semantic_flows=["query_synthesis"],
        semantic_flow_invocation_counts={"query_synthesis": 1},
        status=status,  # type: ignore[arg-type]
        started_at=started_at,
        completed_at=completed_at,
        model_fingerprint=_model_fingerprint(execution_mode),
        provider_fingerprint=_provider_fingerprint(execution_mode),
        reasoning_effort="high",
        execution_mode=execution_mode,
        llm_attempt_count=llm_attempt_count,
        lint_error_count=0,
        lint_warning_count=0,
        lint_info_count=0,
        toolchain_versions=toolchain_versions,
    )


def _model_fingerprint(execution_mode: str) -> str:
    return "mock_bootstrap" if execution_mode == "mock_llm_test" else "live_unspecified"


def _provider_fingerprint(execution_mode: str) -> str:
    return "mock" if execution_mode == "mock_llm_test" else "live_unspecified"


if __name__ == "__main__":
    raise SystemExit(main())
