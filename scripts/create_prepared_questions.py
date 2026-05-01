#!/usr/bin/env python3
"""Create or update canonical prepared-question records from TSV seed data."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.questions.prepared_questions import (
    PreparedQuestionSeed,
    parse_prepared_question_seed_tsv,
    upsert_prepared_question_seeds,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--questions-tsv", required=True)
    parser.add_argument("--space-name")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        registry_path = resolve_registry_path(args.registry_path)
        questions_tsv = Path(args.questions_tsv).expanduser()
        if not questions_tsv.is_absolute():
            questions_tsv = (Path.cwd() / questions_tsv).resolve()
        else:
            questions_tsv = questions_tsv.resolve()
        if not questions_tsv.is_file():
            raise FileNotFoundError(f"Questions TSV not found: {questions_tsv}")
        seed_rows = parse_prepared_question_seed_tsv(questions_tsv)
        if args.space_name:
            seed_rows = [row for row in seed_rows if row.space_name == args.space_name]
        rows_by_space: dict[str, list[PreparedQuestionSeed]] = defaultdict(list)
        for row in seed_rows:
            rows_by_space[row.space_name].append(row)
        written = []
        for space_name in sorted(rows_by_space):
            space_root = resolve_space_root(registry_path, space_name)
            written.extend(
                upsert_prepared_question_seeds(
                    space_root=space_root,
                    space_name=space_name,
                    seeds=rows_by_space[space_name],
                )
            )
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Prepared question creation failed: {exc}", file=sys.stderr)
        return 1

    print(
        "scripts/create_prepared_questions.py complete "
        f"(spaces={len(rows_by_space)} questions={len(written)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

