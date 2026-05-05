#!/usr/bin/env python3
"""Source-scouting sidecar entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import make_run_id
from sapi.core.registry import resolve_registry_path, resolve_site_path_from_registry, resolve_space_root
from sapi.core.runtime_flags import add_runtime_flag_arguments, snapshot_runtime_flags, validate_runtime_flag_arguments
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.llm.trace import SiteLlmTraceContext
from sapi.questions.prepared_questions import load_prepared_questions
from sapi.scouting.pipeline import (
    LiveSourceScoutingClient,
    MockSourceScoutingClient,
    backend_config_from_runtime_flags,
    run_source_scouting_and_store,
)
from sapi.scouting.store import candidate_queue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("question_id")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--mock-candidate-plan")
    parser.add_argument("--verbose", action="store_true")
    add_runtime_flag_arguments(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.count <= 0:
            raise ValueError("--count must be positive.")
        validate_runtime_flag_arguments(args)
        runtime_flags = snapshot_runtime_flags(args)
        runtime_policy = evaluate_semantic_runtime_policy(mock_llm=runtime_flags.mock_llm, env=None)
        if args.mock_candidate_plan and not runtime_flags.mock_llm:
            raise ValueError("--mock-candidate-plan may only be used with --mock-llm.")
        registry_path = resolve_registry_path(args.registry_path)
        site_path = resolve_site_path_from_registry(registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        question = _load_question(space_root=space_root, space_name=args.space_name, question_id=args.question_id)
        queue = candidate_queue(site_path=site_path, space_name=args.space_name, question_id=args.question_id)
        run_id = make_run_id()
        trace_ctx = SiteLlmTraceContext(site_path=site_path, verbose=True) if args.verbose else None
        candidate_plan = (
            _load_mock_candidate_plan(
                Path(args.mock_candidate_plan),
                space_name=args.space_name,
                question_id=args.question_id,
            )
            if args.mock_candidate_plan
            else None
        )
        if runtime_flags.mock_llm:
            llm_client = MockSourceScoutingClient(
                space_name=args.space_name,
                question_id=args.question_id,
                question_text=question.question,
                count=args.count,
                candidate_plan=candidate_plan,
            )
        else:
            llm_client = LiveSourceScoutingClient(
                backend_config=backend_config_from_runtime_flags(runtime_flags),
                task_context={
                    "requested_count": args.count,
                    "question_id": args.question_id,
                    "question_text": question.question,
                    "scouting_policy": (
                        "Use web search if available to identify reputable, cited papers with public PDFs. "
                        "Return recommendations only; do not write canonical artifacts."
                    ),
                },
            )
        result = run_source_scouting_and_store(
            repo_root=_REPO_ROOT,
            site_path=site_path,
            space_root=space_root,
            queue=queue,
            question=question,
            run_id=run_id,
            count=args.count,
            runtime_flags=runtime_flags,
            llm_client=llm_client,
            trace_ctx=trace_ctx,
        )
        print(
            "scripts/scout_sources.py scouting completed "
            f"(execution_mode={runtime_policy.execution_mode}, "
            f"run_id={result.run_id}, "
            f"status={result.status}, "
            f"question_id={args.question_id}, "
            f"candidate_count={result.candidate_count}, "
            f"candidate_ids={result.candidate_ids}, "
            f"semantic_output_path={result.semantic_output_path}, "
            f"run_record_path={result.run_record_path})"
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _load_question(*, space_root: Path, space_name: str, question_id: str):
    for question in load_prepared_questions(space_root, space_name=space_name):
        if question.question_id == question_id:
            return question
    raise FileNotFoundError(f"Prepared question not found in {space_name}: {question_id}")


def _load_mock_candidate_plan(path: Path, *, space_name: str, question_id: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Mock candidate plan not found: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw_line.split("\t")
        if len(parts) != 9:
            raise ValueError(
                f"{path}:{line_number}: expected 9 tab-separated fields: "
                "space_name, question_id, rank, title, pdf_path, doi, landing_url, venue, citation_count."
            )
        row_space, row_question, rank_raw, title, pdf_path, doi, landing_url, venue, citation_count_raw = (
            part.strip() for part in parts
        )
        if row_space != space_name or row_question != question_id:
            continue
        rank = int(rank_raw)
        citation_count = int(citation_count_raw)
        resolved_pdf = Path(pdf_path)
        if not resolved_pdf.is_absolute():
            resolved_pdf = (path.parent / resolved_pdf).resolve()
        rows.append(
            {
                "title": title,
                "authors": ["Example Fixture Author"],
                "venue": {
                    "name": venue,
                    "type": "journal",
                    "publisher": "Example Fixture Publisher",
                    "reputation_rationale": "Example fixture plan marks this venue as reputable for test mode.",
                },
                "publication_year": 2024,
                "doi": doi,
                "landing_url": landing_url,
                "pdf_url": str(resolved_pdf),
                "public_access": {
                    "has_public_pdf": True,
                    "access_status": "public_pdf",
                    "evidence": "Local example fixture PDF is explicitly public for mock example-site runs.",
                },
                "citation_signal": {
                    "count": citation_count,
                    "provider": "example_fixture",
                    "as_of": "2026-05-05",
                    "confidence": "medium",
                },
                "ranking": {
                    "rank": rank,
                    "answer_fit_score": 5,
                    "venue_reputation_score": 4,
                    "citation_score": 4,
                    "interestingness_score": 4,
                    "overall_score": 17,
                    "answer_fit_rationale": "Fixture paper is mapped to the prepared question.",
                    "interestingness_rationale": "Fixture paper exercises the source-scouting import path.",
                    "overall_rationale": "High-quality deterministic mock candidate.",
                },
            }
        )
    if not rows:
        raise ValueError(f"No mock candidates found for {space_name}/{question_id} in {path}.")
    return sorted(rows, key=lambda item: int(item["ranking"]["rank"]))


if __name__ == "__main__":
    raise SystemExit(main())
