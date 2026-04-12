#!/usr/bin/env python3
"""Ingest source acquisition entrypoint (TODO-0210 scope)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import json

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.core.locks import IngestLockHeldError, ingest_lock
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.contracts.ids import make_run_id
from sapi.ingest.records_writer import (
    ingest_source_artifacts_and_record,
    run_ingest_extraction_and_persist_canonical,
)
from sapi.llm.client import SemanticLlmRequest


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
    parser.add_argument("--article-kind")
    parser.add_argument("--citation-count", type=float)
    parser.add_argument("--citation-count-as-of")
    parser.add_argument("--citation-count-provider")
    parser.add_argument("--citation-count-confidence")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=args.mock_llm,
            env=os.environ,
        )
        registry_path = resolve_registry_path(args.registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        with ingest_lock(space_root):
            result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=args.source_path_or_url,
                source_title_override=args.source_title,
                source_media_type_override=args.source_media_type,
                source_type_override=args.source_type,
                source_family_id=args.source_family_id,
                canonical_identifier=args.canonical_identifier,
                source_date=args.source_date,
                article_kind=args.article_kind,
                citation_count=args.citation_count,
                citation_count_as_of=args.citation_count_as_of,
                citation_count_provider=args.citation_count_provider,
                citation_count_confidence=args.citation_count_confidence,
            )
            extraction_result = None
            if not args.source_only:
                source_record = json.loads(result.record_path.read_text())
                source_title = source_record.get("title")
                run_id = make_run_id()
                extraction_result = run_ingest_extraction_and_persist_canonical(
                    space_root=space_root,
                    source_id=result.source_id,
                    run_id=run_id,
                    llm_client=_BootstrapIngestExtractionClient(
                        source_id=result.source_id,
                        source_title=source_title if isinstance(source_title, str) else None,
                        source_date=args.source_date,
                    ),
                )
    except IngestLockHeldError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - exercised by CLI contract tests.
        print(str(exc), file=sys.stderr)
        return 1

    summary = (
        "scripts/ingest_source.py source ingested "
        f"(execution_mode={runtime_policy.execution_mode}, "
        f"source_id={result.source_id}, "
        f"record_path={result.record_path}"
    )
    if extraction_result is not None:
        summary += (
            f", run_id={extraction_result.run_id}, "
            f"claims_written={len(extraction_result.claim_paths)}, "
            f"relations_written={len(extraction_result.relation_paths)}"
        )
    summary += ")"
    print(summary)
    return 0


class _BootstrapIngestExtractionClient:
    """Repository-local deterministic semantic client used for reconstruction bootstrap."""

    def __init__(
        self,
        *,
        source_id: str,
        source_title: str | None,
        source_date: str | None,
    ) -> None:
        self._source_id = source_id
        self._source_title = source_title or source_id
        self._source_date = source_date

    def generate_semantic_json(self, _request: SemanticLlmRequest) -> str:
        payload = {
            "source_date_inference": {
                "date": self._source_date,
                "origin": "explicit" if self._source_date else "unknown",
                "confidence": "high" if self._source_date else "unknown",
                "rationale": None,
            },
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
            "warnings": (
                []
                if self._source_date
                else [
                    {
                        "code": "missing_publication_date",
                        "message": "Publication date could not be resolved; continuing with date=null.",
                    }
                ]
            ),
        }
        return json.dumps(payload)


if __name__ == "__main__":
    raise SystemExit(main())
