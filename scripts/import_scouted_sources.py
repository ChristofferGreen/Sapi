#!/usr/bin/env python3
"""Import selected source-scouting candidates through the canonical ingest wrapper."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc
from sapi.core.registry import resolve_registry_path, resolve_site_path_from_registry, resolve_space_root
from sapi.scouting.store import candidate_queue, load_candidates, select_importable_candidates, update_candidate_status


_SOURCE_ID_RE = re.compile(r"source_id=([a-z0-9][a-z0-9-]*)")
_RUN_ID_RE = re.compile(r"run_id=([^,\s)]+)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--question-id")
    parser.add_argument("--selected-only", action="store_true")
    parser.add_argument("--allow-restricted-source", action="store_true")
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.count <= 0:
            raise ValueError("--count must be positive.")
        registry_path = resolve_registry_path(args.registry_path)
        site_path = resolve_site_path_from_registry(registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        question_id = args.question_id or _resolve_single_question_id(site_path=site_path, space_name=args.space_name)
        queue = candidate_queue(site_path=site_path, space_name=args.space_name, question_id=question_id)
        candidates = select_importable_candidates(
            queue=queue,
            count=args.count,
            include_selected_only=args.selected_only,
        )
        imported: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []
        for candidate in candidates:
            candidate_id = str(candidate["candidate_id"])
            duplicate_source_id = _find_duplicate_source(space_root=space_root, candidate=candidate)
            if duplicate_source_id:
                update_candidate_status(
                    queue=queue,
                    candidate_id=candidate_id,
                    import_status="duplicate",
                    import_link={
                        "source_id": duplicate_source_id,
                        "run_id": None,
                        "imported_at": format_timestamp_rfc3339_utc(datetime.now(UTC)),
                    },
                    skip_reason="source already ingested",
                )
                skipped.append(candidate_id)
                continue
            pdf_locator = str(candidate.get("pdf_url") or "").strip()
            public_access = candidate.get("public_access") if isinstance(candidate.get("public_access"), dict) else {}
            if not pdf_locator:
                update_candidate_status(
                    queue=queue,
                    candidate_id=candidate_id,
                    import_status="skipped",
                    skip_reason="candidate has no PDF locator to import",
                )
                skipped.append(candidate_id)
                continue
            if public_access.get("has_public_pdf") is not True:
                if not args.allow_restricted_source:
                    update_candidate_status(
                        queue=queue,
                        candidate_id=candidate_id,
                        import_status="skipped",
                        skip_reason="candidate has no public PDF; rerun with --allow-restricted-source to import restricted local files",
                    )
                    skipped.append(candidate_id)
                    continue
            update_candidate_status(queue=queue, candidate_id=candidate_id, import_status="importing")
            result = _run_ingest(
                site_path=site_path,
                space_name=args.space_name,
                candidate=candidate,
                pdf_locator=pdf_locator,
                mock_llm=args.mock_llm,
                restricted_source=bool(public_access.get("has_public_pdf") is not True),
                verbose=args.verbose,
            )
            if result.returncode != 0:
                update_candidate_status(
                    queue=queue,
                    candidate_id=candidate_id,
                    import_status="failed",
                    failure_reason=result.stderr.strip() or result.stdout.strip() or f"ingest exited {result.returncode}",
                )
                failed.append(candidate_id)
                continue
            source_id = _parse_required(_SOURCE_ID_RE, result.stdout, "source_id")
            run_id = _parse_required(_RUN_ID_RE, result.stdout, "run_id")
            update_candidate_status(
                queue=queue,
                candidate_id=candidate_id,
                import_status="imported",
                import_link={
                    "source_id": source_id,
                    "run_id": run_id,
                    "imported_at": format_timestamp_rfc3339_utc(datetime.now(UTC)),
                },
            )
            imported.append(candidate_id)
        print(
            "scripts/import_scouted_sources.py import completed "
            f"(space_name={args.space_name}, question_id={question_id}, requested_count={args.count}, "
            f"imported={imported}, skipped={skipped}, failed={failed})"
        )
        return 1 if failed else 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _resolve_single_question_id(*, site_path: Path, space_name: str) -> str:
    questions_root = site_path / "scouting" / "spaces" / space_name / "questions"
    if not questions_root.is_dir():
        raise ValueError("--question-id is required because no scouting queue exists for this space.")
    question_ids = sorted(path.name for path in questions_root.iterdir() if path.is_dir())
    if len(question_ids) != 1:
        raise ValueError("--question-id is required when a space has zero or multiple scouting queues.")
    return question_ids[0]


def _run_ingest(
    *,
    site_path: Path,
    space_name: str,
    candidate: dict[str, Any],
    pdf_locator: str,
    mock_llm: bool,
    restricted_source: bool,
    verbose: bool,
) -> subprocess.CompletedProcess[str]:
    command = [
        "bash",
        str(_REPO_ROOT / "ingest.sh"),
        str(site_path),
        space_name,
        pdf_locator,
        "--source-title",
        str(candidate.get("title") or candidate["candidate_id"]),
    ]
    doi = candidate.get("doi")
    if isinstance(doi, str) and doi.strip():
        command.extend(["--canonical-identifier", doi.strip()])
    citation_signal = candidate.get("citation_signal")
    if isinstance(citation_signal, dict):
        count = citation_signal.get("count")
        if isinstance(count, int):
            command.extend(["--citation-count", str(count)])
        for flag, key in (
            ("--citation-count-as-of", "as_of"),
            ("--citation-count-provider", "provider"),
            ("--citation-count-confidence", "confidence"),
        ):
            value = citation_signal.get(key)
            if isinstance(value, str) and value.strip():
                command.extend([flag, value.strip()])
    if mock_llm:
        command.append("--mock-llm")
    if restricted_source:
        restricted_args = [
            "--restricted-source",
            "--source-access-reason",
            "scouted candidate does not have a public PDF",
            "--operator-responsibility",
            "operator confirmed rights to process this source locally",
        ]
        landing_url = candidate.get("landing_url")
        if isinstance(landing_url, str) and landing_url.strip():
            restricted_args.extend(["--source-landing-url", landing_url.strip()])
        command.extend(
            restricted_args
        )
    if verbose:
        command.append("--verbose")
    return subprocess.run(command, cwd=str(_REPO_ROOT), text=True, capture_output=True)


def _find_duplicate_source(*, space_root: Path, candidate: dict[str, Any]) -> str | None:
    records_root = space_root / "sources" / "records"
    if not records_root.is_dir():
        return None
    candidate_keys = _candidate_keys(candidate)
    for path in sorted(records_root.glob("source-*.json")):
        payload = json.loads(path.read_text())
        if not isinstance(payload, dict):
            continue
        source_keys = _source_keys(payload)
        if candidate_keys.intersection(source_keys):
            return str(payload.get("source_id") or path.stem)
    return None


def _candidate_keys(candidate: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    doi = candidate.get("doi")
    if isinstance(doi, str) and doi.strip():
        keys.add("doi:" + doi.strip().casefold())
    for field in ("landing_url", "pdf_url"):
        value = candidate.get(field)
        if isinstance(value, str) and value.strip():
            keys.add(field + ":" + value.strip().casefold())
    return keys


def _source_keys(source: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for field in ("canonical_identifier", "source_locator"):
        value = source.get(field)
        if isinstance(value, str) and value.strip():
            keys.add(("doi:" if value.casefold().startswith("10.") else f"{field}:") + value.strip().casefold())
    source_semantic = source.get("source_semantic")
    if isinstance(source_semantic, dict):
        doi = source_semantic.get("doi")
        if isinstance(doi, str) and doi.strip():
            keys.add("doi:" + doi.strip().casefold())
    return keys


def _parse_required(pattern: re.Pattern[str], text: str, label: str) -> str:
    match = pattern.search(text)
    if not match:
        raise ValueError(f"ingest output did not include {label}.")
    return match.group(1)


if __name__ == "__main__":
    raise SystemExit(main())
