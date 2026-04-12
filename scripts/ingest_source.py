#!/usr/bin/env python3
"""Ingest source acquisition entrypoint (TODO-0210 scope)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.core.locks import IngestLockHeldError, ingest_lock
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.ingest.records_writer import ingest_source_artifacts_and_record


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
            )
    except IngestLockHeldError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - exercised by CLI contract tests.
        print(str(exc), file=sys.stderr)
        return 1

    print(
        "scripts/ingest_source.py source ingested "
        f"(execution_mode={runtime_policy.execution_mode}, "
        f"source_id={result.source_id}, "
        f"record_path={result.record_path})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
