#!/usr/bin/env python3
"""Comment-section generation pipeline entrypoint (TODO-0223 scope)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.comments.comments_pipeline import (
    EVIDENCE_MODE_WEB_AUGMENTED,
    collect_comment_targets,
    normalize_evidence_mode,
    page_ref_key,
    validate_comment_count,
)
from sapi.comments.controls import (
    SiteDiscussionControls,
    apply_canonical_page_discussion_controls,
    load_site_discussion_controls,
    resolve_page_discussion_controls,
)
from sapi.comments.merge_normalize import (
    apply_merged_comments_to_page,
    merge_comment_section,
)
from sapi.comments.quality import build_comment_quality_manifest
from sapi.contracts.ids import format_timestamp_rfc3339_utc, make_run_id
from sapi.contracts.run_envelopes import CommentRunFields, RunEnvelopeBase
from sapi.core.pipeline_policy import finalize_pipeline_run
from sapi.core.registry import resolve_registry_path, resolve_site_path_from_registry, resolve_space_root
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
from sapi.llm.runtime_backend import (
    SemanticBackendConfig,
    generate_semantic_json_live,
)
from sapi.llm.semantic_executor import build_semantic_spec_from_contract, run_semantic_flow
from sapi.profiles.persona_catalog import load_seeded_persona_catalog

_ARGUMENTATIVE_POSITIONS = {"support", "challenge", "rebuttal", "synthesis"}
_GENERATION_ISOLATION_SCHEMA_VERSION = "comment_section_generation_context_v1"
_ADJUDICATION_RUBRIC_ID = "comment_section_adjudication_v1"
_COMMENT_SECTION_MAX_REPAIR_LOOPS = 0
_GENERATION_ISOLATION_LEAK_TERMS: tuple[str, ...] = (
    "adjudication rubric",
    "scoring rubric",
    "score weights",
    "rubric criteria",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--count", required=True, type=int)
    parser.add_argument("--comment-user", action="append", default=[])
    parser.add_argument("--user", action="append", default=[], help=argparse.SUPPRESS)
    parser.add_argument("--comment-page", action="append", default=[])
    parser.add_argument("--page", action="append", default=[], help=argparse.SUPPRESS)
    parser.add_argument("--comment-seed")
    parser.add_argument("--comment-evidence-mode")
    parser.add_argument("--comment-web-evidence", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--verbose", action="store_true")
    add_runtime_flag_arguments(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    run_id = make_run_id()
    toolchain_versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    transaction = ArtifactTransaction()
    runtime_policy = None
    runtime_flags = None
    space_root: Path | None = None
    site_controls = SiteDiscussionControls(defaults={}, pages={})
    requested_count = 0
    evidence_mode = "canonical-only"
    comment_user_filters: list[str] = []
    target_page_refs: list[str] = []
    comments_added = 0
    evidence_snapshot_path: Path | None = None
    semantic_flows: list[str] = []
    semantic_flow_invocation_counts: dict[str, int] = {}
    llm_attempt_count = 0
    adjudication_summary = _empty_adjudication_summary()
    generation_isolation_summary = _empty_generation_isolation_summary()
    comments_by_page_for_quality: dict[str, list[dict[str, object]]] = {}
    comment_quality_manifest_path: Path | None = None

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

        requested_count = validate_comment_count(args.count)
        evidence_mode = normalize_evidence_mode(
            args.comment_evidence_mode,
            comment_web_evidence=bool(args.comment_web_evidence),
        )
        comment_user_filters = _normalize_comment_user_filters(args)
        selected_persona_ids = _resolve_selected_persona_ids(comment_user_filters=comment_user_filters)
        targets = collect_comment_targets(
            space_root=space_root,
            explicit_page_refs=_normalize_comment_page_refs(args),
        )
        site_controls = load_site_discussion_controls(site_path=site_path)
        target_page_refs = [target.page_ref for target in targets]
    except (FileNotFoundError, KeyError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    target_new_comment_uids: dict[str, list[str]] = {}

    try:
        for target in targets:
            page_controls = resolve_page_discussion_controls(
                site_controls=site_controls,
                page_ref=target.page_ref,
                page_payload=target.page_payload,
            )
            page_payload = target.page_payload
            if page_controls.canonical_page_controls_to_write is not None:
                page_payload = apply_canonical_page_discussion_controls(
                    page_payload=page_payload,
                    canonical_page_controls=page_controls.canonical_page_controls_to_write,
                )

            _record_semantic_invocation(
                flow_key="comment_section_generation",
                semantic_flows=semantic_flows,
                semantic_flow_invocation_counts=semantic_flow_invocation_counts,
            )
            spec = build_semantic_spec_from_contract(
                "comment_section_generation",
                repo_root=_REPO_ROOT,
                path_tokens={
                    "space_root": space_root,
                    "site_path": site_path,
                    "run_id": run_id,
                    "page_ref_key": page_ref_key(target.page_ref),
                },
            )
            comment_llm_client = _build_comment_section_client(
                runtime_flags=runtime_flags,
                page_ref=target.page_ref,
                requested_count=requested_count,
                persona_ids=selected_persona_ids,
                page_payload=page_payload,
                original_source_context=_build_original_source_context(
                    space_root=space_root,
                    page_ref=target.page_ref,
                    page_payload=page_payload,
                ),
            )
            semantic_payload, attempt_count = run_semantic_flow(
                spec=spec,
                llm_client=comment_llm_client,
                max_repair_loops=_COMMENT_SECTION_MAX_REPAIR_LOOPS,
            )
            llm_attempt_count += attempt_count
            generation_isolation_summary = _merge_generation_isolation_summary(
                generation_isolation_summary,
                comment_llm_client.generation_isolation_summary,
            )
            if not spec.output_json_path.exists():
                raise RuntimeError(
                    "comment_section_generation semantic output was not persisted to the canonical path."
                )
            transaction.mark_create(spec.output_json_path)

            merge_result = merge_comment_section(
                page_ref=target.page_ref,
                page_payload=page_payload,
                semantic_comments=_extract_semantic_comments(
                    semantic_payload=semantic_payload,
                    expected_page_ref=target.page_ref,
                ),
            )
            comments_added += merge_result.comments_added
            adjudication_summary = _merge_adjudication_summary(
                adjudication_summary,
                _summarize_page_adjudication(
                    page_ref=target.page_ref,
                    comments=merge_result.merged_comments,
                ),
            )
            target_new_comment_uids[target.page_ref] = merge_result.new_comment_uids
            comments_by_page_for_quality[target.page_ref] = list(merge_result.merged_comments)
            updated_page_payload = apply_merged_comments_to_page(
                page_payload=page_payload,
                page_ref=target.page_ref,
                merged_comments=merge_result.merged_comments,
            )
            _write_json_with_transaction(
                target.page_path,
                updated_page_payload,
                transaction=transaction,
            )

        if evidence_mode == EVIDENCE_MODE_WEB_AUGMENTED:
            snapshot_seed = _resolve_snapshot_seed(args.comment_seed, run_id=run_id)
            evidence_snapshot_path = (
                space_root
                / "raw"
                / "snapshots"
                / "comment_sections"
                / f"comment-section-{snapshot_seed}.json"
            )
            _write_json_with_transaction(
                evidence_snapshot_path,
                _build_web_augmented_evidence_snapshot(
                    seed=snapshot_seed,
                    target_new_comment_uids=target_new_comment_uids,
                ),
                transaction=transaction,
            )

        comment_quality_manifest_path, comment_quality_manifest_payload = build_comment_quality_manifest(
            repo_root=_REPO_ROOT,
            space_root=space_root,
            comments_by_page=comments_by_page_for_quality,
            snapshot_path=evidence_snapshot_path,
        )
        _write_json_with_transaction(
            comment_quality_manifest_path,
            comment_quality_manifest_payload,
            transaction=transaction,
        )

        if args.simulate_terminal_failure:
            raise RuntimeError("Simulated terminal comments failure.")
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
        flow_fields = CommentRunFields(
            target_page_refs=target_page_refs,
            comment_user_filters=comment_user_filters,
            requested_count=requested_count,
            comments_added=comments_added,
            adjudication=adjudication_summary,
            generation_isolation=generation_isolation_summary,
            evidence_mode=evidence_mode,
            evidence_snapshot_path=(
                str(evidence_snapshot_path.resolve()) if evidence_snapshot_path is not None else None
            ),
        )
        finalized = finalize_pipeline_run(
            space_root=space_root,
            base=base,
            flow_fields=flow_fields,
            transaction=transaction,
            force_mode=False,
            summary="Comment generation failed; invocation-scoped outputs rolled back.",
            errors=str(exc),
        )
        print(
            "scripts/create_comments.py comments failed "
            f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
            f"status={finalized.status}, adjudication={adjudication_summary}, "
            f"generation_isolation={generation_isolation_summary}, error={exc})",
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
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )
    flow_fields = CommentRunFields(
        target_page_refs=target_page_refs,
        comment_user_filters=comment_user_filters,
        requested_count=requested_count,
        comments_added=comments_added,
        adjudication=adjudication_summary,
        generation_isolation=generation_isolation_summary,
        evidence_mode=evidence_mode,
        evidence_snapshot_path=(
            str(evidence_snapshot_path.resolve()) if evidence_snapshot_path is not None else None
        ),
    )
    finalized = finalize_pipeline_run(
        space_root=space_root,
        base=base,
        flow_fields=flow_fields,
        transaction=transaction,
        force_mode=False,
        summary="Comment generation completed successfully.",
        changes=(
            f"target_pages={len(target_page_refs)}, "
            f"semantic_artifacts={semantic_flow_invocation_counts.get('comment_section_generation', 0)}, "
            f"comments_added={comments_added}"
        ),
        lint_summary="lint_error_count=0 lint_warning_count=0 lint_info_count=0",
        errors="",
    )
    print(
        "scripts/create_comments.py comments created "
        f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
        f"target_page_refs={target_page_refs}, comments_added={comments_added}, "
        f"adjudication={adjudication_summary}, generation_isolation={generation_isolation_summary}, "
        f"evidence_mode={evidence_mode}, evidence_snapshot_path={flow_fields.evidence_snapshot_path}, "
        f"comment_quality_manifest_path={comment_quality_manifest_path}, "
        f"run_record_path={finalized.run_record_path}, "
        f"runtime_flags={runtime_flags_summary_dict(runtime_flags)})"
    )
    return finalized.exit_code


def _normalize_comment_user_filters(args: argparse.Namespace) -> list[str]:
    comment_users = [str(value).strip() for value in args.comment_user if str(value).strip()]
    user_aliases = [str(value).strip() for value in args.user if str(value).strip()]
    if comment_users and user_aliases:
        raise ValueError("Cannot combine --comment-user and alias --user in direct script invocation.")
    raw = comment_users if comment_users else user_aliases
    deduped: list[str] = []
    seen: set[str] = set()
    for persona_id in raw:
        if persona_id in seen:
            continue
        seen.add(persona_id)
        deduped.append(persona_id)
    return deduped


def _normalize_comment_page_refs(args: argparse.Namespace) -> list[str]:
    comment_pages = [str(value).strip() for value in args.comment_page if str(value).strip()]
    page_aliases = [str(value).strip() for value in args.page if str(value).strip()]
    if comment_pages and page_aliases:
        raise ValueError("Cannot combine --comment-page and alias --page in direct script invocation.")
    return comment_pages if comment_pages else page_aliases


def _resolve_selected_persona_ids(*, comment_user_filters: list[str]) -> list[str]:
    persona_catalog = load_seeded_persona_catalog(repo_root=_REPO_ROOT)
    persona_ids = [str(row["persona_id"]) for row in persona_catalog]
    known_persona_ids = set(persona_ids)
    if not persona_ids:
        if comment_user_filters:
            return comment_user_filters
        return ["commenter-1", "commenter-2", "commenter-3", "commenter-4", "commenter-5"]
    if comment_user_filters:
        unknown = sorted({persona_id for persona_id in comment_user_filters if persona_id not in known_persona_ids})
        if unknown:
            raise ValueError(
                "Unknown persona_id values requested via --comment-user: " + ", ".join(unknown)
            )
        return comment_user_filters
    return persona_ids[:5]


def _extract_semantic_comments(
    *,
    semantic_payload: dict[str, object],
    expected_page_ref: str,
) -> list[dict[str, object]]:
    semantic_page_ref = semantic_payload.get("page_ref")
    if semantic_page_ref != expected_page_ref:
        raise ValueError(
            "comment_section_generation semantic payload page_ref mismatch: "
            f"expected {expected_page_ref!r}, got {semantic_page_ref!r}."
        )
    comments = semantic_payload.get("comments")
    if not isinstance(comments, list):
        raise ValueError("comment_section_generation semantic payload must contain `comments` array.")
    normalized: list[dict[str, object]] = []
    for row in comments:
        if not isinstance(row, dict):
            raise ValueError("comment_section_generation comments rows must be JSON objects.")
        score_assessment = row.get("score_assessment")
        if not isinstance(score_assessment, dict):
            raise ValueError(
                "comment_section_generation comments rows must include score_assessment object."
            )
        score = score_assessment.get("score")
        rationale = score_assessment.get("rationale")
        if not isinstance(score, int):
            raise ValueError(
                "comment_section_generation score_assessment.score must be integer."
            )
        if score < -30 or score > 30:
            raise ValueError(
                "comment_section_generation score_assessment.score must be in [-30, 30]."
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError(
                "comment_section_generation score_assessment.rationale must be non-empty string."
            )
        normalized.append(row)
    return normalized


def _build_original_source_context(
    *,
    space_root: Path,
    page_ref: str,
    page_payload: dict[str, object],
) -> dict[str, object]:
    page_type, _, page_id = page_ref.partition(":")
    source_ids: list[str] = []

    if page_type == "source" and page_id:
        source_ids = [page_id]
    elif page_type == "topic":
        raw_source_ids = page_payload.get("source_ids")
        if isinstance(raw_source_ids, list):
            source_ids = [
                str(item).strip()
                for item in raw_source_ids
                if isinstance(item, str) and str(item).strip()
            ]
    elif page_type == "claim":
        claim_record_path = space_root / "claims" / f"{page_id}.json"
        if claim_record_path.is_file():
            claim_payload = json.loads(claim_record_path.read_text())
            source_id = claim_payload.get("source_id")
            if isinstance(source_id, str) and source_id.strip():
                source_ids = [source_id.strip()]

    deduped_source_ids: list[str] = []
    seen_source_ids: set[str] = set()
    source_records: list[dict[str, object]] = []
    for source_id in source_ids:
        if source_id in seen_source_ids:
            continue
        seen_source_ids.add(source_id)
        deduped_source_ids.append(source_id)
        source_path = space_root / "sources" / "records" / f"{source_id}.json"
        if not source_path.is_file():
            continue
        source_payload = json.loads(source_path.read_text())
        if isinstance(source_payload, dict):
            source_records.append(source_payload)

    return {
        "source_ids": deduped_source_ids,
        "source_records": source_records,
    }


def _write_json_with_transaction(
    path: Path,
    payload: dict[str, object],
    *,
    transaction: ArtifactTransaction,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup_path = path.with_name(f".{path.name}.bak.{secrets.token_hex(8)}")
        shutil.copy2(path, backup_path)
        transaction.mark_replace(path, backup_path)
    else:
        transaction.mark_create(path)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _resolve_snapshot_seed(raw_seed: str | None, *, run_id: str) -> str:
    if raw_seed is None or not raw_seed.strip():
        return run_id
    return raw_seed.strip()


def _build_web_augmented_evidence_snapshot(
    *,
    seed: str,
    target_new_comment_uids: dict[str, list[str]],
) -> dict[str, object]:
    accessed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    items: list[dict[str, object]] = []
    for page_ref, comment_refs in sorted(target_new_comment_uids.items()):
        items.append(
            {
                "query": f"discussion background for {page_ref}",
                "source_url": f"https://example.invalid/{page_ref_key(page_ref)}",
                "accessed_at": accessed_at,
                "comment_refs": comment_refs,
            }
        )
    return {
        "schema_version": "comment_section_evidence_snapshot_v1",
        "seed": seed,
        "mode": EVIDENCE_MODE_WEB_AUGMENTED,
        "items": items,
    }


def _record_semantic_invocation(
    *,
    flow_key: str,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
) -> None:
    if flow_key not in semantic_flows:
        semantic_flows.append(flow_key)
    semantic_flow_invocation_counts[flow_key] = semantic_flow_invocation_counts.get(flow_key, 0) + 1


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
    return RunEnvelopeBase(
        run_id=run_id,
        flow_key="comment_section_pipeline",
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        status=status,  # type: ignore[arg-type]
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


def _empty_generation_isolation_summary() -> dict[str, object]:
    return {
        "schema_version": _GENERATION_ISOLATION_SCHEMA_VERSION,
        "prompt_leak_count": 0,
        "context_leak_count": 0,
        "total_leak_count": 0,
        "detected_terms": [],
    }


def _merge_generation_isolation_summary(
    left: dict[str, object],
    right: dict[str, object],
) -> dict[str, object]:
    combined_terms = sorted(
        set(_as_str_list(left.get("detected_terms"))) | set(_as_str_list(right.get("detected_terms")))
    )
    prompt_leak_count = int(left.get("prompt_leak_count", 0)) + int(right.get("prompt_leak_count", 0))
    context_leak_count = int(left.get("context_leak_count", 0)) + int(right.get("context_leak_count", 0))
    total_leak_count = int(left.get("total_leak_count", 0)) + int(right.get("total_leak_count", 0))
    return {
        "schema_version": _GENERATION_ISOLATION_SCHEMA_VERSION,
        "prompt_leak_count": prompt_leak_count,
        "context_leak_count": context_leak_count,
        "total_leak_count": total_leak_count,
        "detected_terms": combined_terms,
    }


def _audit_generation_isolation_request(request: SemanticLlmRequest) -> dict[str, object]:
    prompt_blob = request.spec_text
    context_blob = "\n".join(
        f"{path}={pointer}"
        for path, pointer in sorted(request.context_by_path.items())
    )
    prompt_leak_count, prompt_terms = _count_generation_isolation_leaks(prompt_blob)
    context_leak_count, context_terms = _count_generation_isolation_leaks(context_blob)
    detected_terms = sorted(prompt_terms | context_terms)
    return {
        "schema_version": _GENERATION_ISOLATION_SCHEMA_VERSION,
        "prompt_leak_count": prompt_leak_count,
        "context_leak_count": context_leak_count,
        "total_leak_count": prompt_leak_count + context_leak_count,
        "detected_terms": detected_terms,
    }


def _count_generation_isolation_leaks(text: str) -> tuple[int, set[str]]:
    normalized = text.lower()
    terms: set[str] = set()
    leak_count = 0
    for term in _GENERATION_ISOLATION_LEAK_TERMS:
        count = normalized.count(term)
        if count <= 0:
            continue
        terms.add(term)
        leak_count += count
    return leak_count, terms


def _empty_adjudication_summary() -> dict[str, object]:
    return {
        "rubric_id": _ADJUDICATION_RUBRIC_ID,
        "rows": 0,
        "checks": {
            "claim_citation": 0,
            "anti_repetition": 0,
            "strongest_opposing_point_ack": 0,
        },
        "failures": {
            "claim_citation": 0,
            "anti_repetition": 0,
            "strongest_opposing_point_ack": 0,
            "total": 0,
        },
        "pages_with_failures": [],
    }


def _summarize_page_adjudication(
    *,
    page_ref: str,
    comments: list[dict[str, object]],
) -> dict[str, object]:
    rows = len(comments)
    checks = {
        "claim_citation": 0,
        "anti_repetition": rows,
        "strongest_opposing_point_ack": 0,
    }
    failures = {
        "claim_citation": 0,
        "anti_repetition": 0,
        "strongest_opposing_point_ack": 0,
        "total": 0,
    }
    seen_comment_bodies: set[tuple[str, str]] = set()
    page_failed = False
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        persona_id = str(comment.get("persona_id") or "")
        body = str(comment.get("body") or "")
        body_key = (persona_id.strip(), " ".join(body.split()).strip().lower())
        if body_key in seen_comment_bodies:
            failures["anti_repetition"] += 1
            page_failed = True
        else:
            seen_comment_bodies.add(body_key)

        turn = comment.get("turn")
        if not isinstance(turn, dict):
            continue
        position = str(turn.get("position") or "").strip().lower()
        if position in _ARGUMENTATIVE_POSITIONS:
            checks["claim_citation"] += 1
            evidence_refs = turn.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs:
                failures["claim_citation"] += 1
                page_failed = True
        if position == "rebuttal":
            checks["strongest_opposing_point_ack"] += 1
            ack = turn.get("strongest_opposing_point_ack")
            if not isinstance(ack, str) or not ack.strip():
                failures["strongest_opposing_point_ack"] += 1
                page_failed = True

    failures["total"] = (
        failures["claim_citation"]
        + failures["anti_repetition"]
        + failures["strongest_opposing_point_ack"]
    )
    return {
        "rubric_id": _ADJUDICATION_RUBRIC_ID,
        "rows": rows,
        "checks": checks,
        "failures": failures,
        "pages_with_failures": [page_ref] if page_failed else [],
    }


def _merge_adjudication_summary(
    left: dict[str, object],
    right: dict[str, object],
) -> dict[str, object]:
    left_checks = _as_int_map(left.get("checks"))
    right_checks = _as_int_map(right.get("checks"))
    left_failures = _as_int_map(left.get("failures"))
    right_failures = _as_int_map(right.get("failures"))
    checks = {
        "claim_citation": left_checks.get("claim_citation", 0) + right_checks.get("claim_citation", 0),
        "anti_repetition": left_checks.get("anti_repetition", 0) + right_checks.get("anti_repetition", 0),
        "strongest_opposing_point_ack": left_checks.get("strongest_opposing_point_ack", 0)
        + right_checks.get("strongest_opposing_point_ack", 0),
    }
    failures = {
        "claim_citation": left_failures.get("claim_citation", 0) + right_failures.get("claim_citation", 0),
        "anti_repetition": left_failures.get("anti_repetition", 0) + right_failures.get("anti_repetition", 0),
        "strongest_opposing_point_ack": left_failures.get("strongest_opposing_point_ack", 0)
        + right_failures.get("strongest_opposing_point_ack", 0),
    }
    failures["total"] = (
        failures["claim_citation"]
        + failures["anti_repetition"]
        + failures["strongest_opposing_point_ack"]
    )
    return {
        "rubric_id": _ADJUDICATION_RUBRIC_ID,
        "rows": int(left.get("rows", 0)) + int(right.get("rows", 0)),
        "checks": checks,
        "failures": failures,
        "pages_with_failures": sorted(
            set(_as_str_list(left.get("pages_with_failures")))
            | set(_as_str_list(right.get("pages_with_failures")))
        ),
    }


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
    return result


def _as_int_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            continue
        if isinstance(item, int):
            result[key] = item
    return result


def _build_comment_section_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    page_ref: str,
    requested_count: int,
    persona_ids: list[str],
    page_payload: dict[str, object],
    original_source_context: dict[str, object],
):
    if runtime_flags.mock_llm:
        return _MockCommentSectionClient(
            page_ref=page_ref,
            requested_count=requested_count,
            persona_ids=persona_ids,
            page_payload=page_payload,
            original_source_context=original_source_context,
        )
    return _LiveCommentSectionClient(
        backend_config=SemanticBackendConfig(
            backend=runtime_flags.llm_backend,
            model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            timeout_secs=runtime_flags.llm_timeout_secs,
        ),
        page_ref=page_ref,
        requested_count=requested_count,
        persona_ids=persona_ids,
        page_payload=page_payload,
        original_source_context=original_source_context,
    )


class _MockCommentSectionClient:
    def __init__(
        self,
        *,
        page_ref: str,
        requested_count: int,
        persona_ids: list[str],
        page_payload: dict[str, object],
        original_source_context: dict[str, object],
    ) -> None:
        self._page_ref = page_ref
        self._requested_count = requested_count
        self._persona_ids = persona_ids
        self._page_payload = page_payload
        self._original_source_context = original_source_context
        self._generation_isolation_summary = _empty_generation_isolation_summary()

    @property
    def generation_isolation_summary(self) -> dict[str, object]:
        return dict(self._generation_isolation_summary)

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        generation_isolation_summary = _audit_generation_isolation_request(request)
        self._generation_isolation_summary = generation_isolation_summary
        if int(generation_isolation_summary.get("total_leak_count", 0)) > 0:
            raise ValueError(
                "comment-generation prompts/context exposed adjudication rubric details."
            )
        page_label = _mock_page_label(page_ref=self._page_ref, page_payload=self._page_payload)
        focus_line = _mock_focus_line(
            page_payload=self._page_payload,
            original_source_context=self._original_source_context,
        )
        comments: list[dict[str, object]] = []
        for index in range(self._requested_count):
            persona_id = self._persona_ids[index % len(self._persona_ids)]
            comment_ref = f"draft-{index + 1}"
            parent_ref: str | None = None if index == 0 else ("draft-1" if index % 2 == 1 else f"draft-{index}")
            body = _mock_comment_body(
                index=index,
                requested_count=self._requested_count,
                persona_id=persona_id,
                page_label=page_label,
                focus_line=focus_line,
            )
            comments.append(
                {
                    "comment_ref": comment_ref,
                    "persona_id": persona_id,
                    "body": body,
                    "parent_ref": parent_ref,
                    "score_assessment": {
                        "score": max(-4, 16 - (index * 2)),
                        "rationale": (
                            "Deterministic mock assessor score based on clarity, relevance, "
                            "and thread coherence."
                        ),
                    },
                }
            )
        payload = {
            "page_ref": self._page_ref,
            "requested_count": self._requested_count,
            "comments": comments,
        }
        return json.dumps(payload)


def _mock_page_label(*, page_ref: str, page_payload: dict[str, object]) -> str:
    for key in ("display_title", "title", "short_title", "topic_id", "source_id", "claim_id"):
        value = page_payload.get(key)
        if isinstance(value, str) and value.strip():
            normalized = " ".join(value.split())
            if re.search(r"--[0-9a-f]{12,}$", normalized):
                continue
            if normalized.casefold().startswith("source-"):
                continue
            return normalized
    return page_ref


def _mock_focus_line(
    *,
    page_payload: dict[str, object],
    original_source_context: dict[str, object],
) -> str:
    candidates: list[str] = []
    for key in ("summary", "text", "description"):
        value = page_payload.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append(value.strip())
    source_summary = original_source_context.get("source_summary")
    if isinstance(source_summary, str) and source_summary.strip():
        candidates.append(source_summary.strip())
    evidence_excerpts = page_payload.get("evidence_excerpts")
    if isinstance(evidence_excerpts, list):
        for row in evidence_excerpts:
            if isinstance(row, str) and row.strip():
                candidates.append(row.strip())
                break
    for candidate in candidates:
        sentence = " ".join(candidate.split())
        if sentence:
            return sentence[:220]
    return "the central argument is clear but benefits from explicit evidence links"


def _persona_display_name(persona_id: str) -> str:
    trimmed = persona_id.strip()
    if trimmed.startswith("persona-"):
        trimmed = trimmed[len("persona-") :]
    words = [part for part in trimmed.split("-") if part]
    if not words:
        return persona_id
    return " ".join(word.capitalize() for word in words)


def _mock_comment_body(
    *,
    index: int,
    requested_count: int,
    persona_id: str,
    page_label: str,
    focus_line: str,
) -> str:
    persona_name = _persona_display_name(persona_id)
    variants = (
        f"{persona_name}: On {page_label}, the clearest claim is that {focus_line}. The page reads stronger when each conclusion stays tied to a specific evidence line.",
        f"{persona_name}: The discussion on {page_label} is solid overall. I would separate direct findings from interpretation, then keep cross-claim transitions shorter for easier verification.",
        f"{persona_name}: My takeaway from {page_label} is that {focus_line}. A short note on scope limits would make the argument easier to trust.",
        f"{persona_name}: {page_label} has good structure and grounded references. The next improvement is to trim repeated phrasing and keep one concrete evidence anchor per paragraph.",
        f"{persona_name}: The central point on {page_label} is coherent and useful. I would clarify which part is source-backed versus synthesis so readers can audit it faster.",
    )
    if requested_count <= 0:
        return variants[0]
    return variants[index % len(variants)]


class _LiveCommentSectionClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        page_ref: str,
        requested_count: int,
        persona_ids: list[str],
        page_payload: dict[str, object],
        original_source_context: dict[str, object],
    ) -> None:
        self._backend_config = backend_config
        self._page_ref = page_ref
        self._requested_count = requested_count
        self._persona_ids = persona_ids
        self._page_payload = page_payload
        self._original_source_context = original_source_context
        self._generation_isolation_summary = _empty_generation_isolation_summary()

    @property
    def generation_isolation_summary(self) -> dict[str, object]:
        return dict(self._generation_isolation_summary)

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        generation_isolation_summary = _audit_generation_isolation_request(request)
        self._generation_isolation_summary = generation_isolation_summary
        if int(generation_isolation_summary.get("total_leak_count", 0)) > 0:
            raise ValueError(
                "comment-generation prompts/context exposed adjudication rubric details."
            )
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "must_use_page_ref": self._page_ref,
                    "requested_count": self._requested_count,
                    "allowed_persona_ids": self._persona_ids,
                    "threading_rule": (
                        "Use parent_ref null for root comments and draft-N references for replies."
                    ),
                    "score_assessment_rule": (
                        "For every generated comment, add score_assessment with score in [-30, 30] "
                        "and concise rationale. Score neutrally from comment quality using thread "
                        "context and original source context."
                    ),
                    "style_constraints": [
                        "Write natural discussion comments, not moderation-template prose.",
                        "Do not use formulaic phrases like 'most defensible sentence is' or 'more persuasive if'.",
                        "Never reference internal IDs or slug labels (for example source-paper-lowres). Use human-readable page titles.",
                        "Vary openings and sentence structure across comments in the same thread.",
                    ],
                },
                "page_payload": self._page_payload,
                "comment_chain_context": (
                    self._page_payload.get("comment_section")
                    if isinstance(self._page_payload.get("comment_section"), dict)
                    else {"comments": []}
                ),
                "original_source_context": self._original_source_context,
            },
        )


if __name__ == "__main__":
    raise SystemExit(main())
