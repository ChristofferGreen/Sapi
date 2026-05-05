"""Sidecar store for source-scouting candidate queues."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import secrets
from typing import Any
from urllib.parse import urlparse

from sapi.contracts.ids import format_timestamp_rfc3339_utc, slugify
from sapi.contracts.schemas import load_json_schema, require_valid_json_instance


_QUESTION_ID_RE = re.compile(r"^question-[a-z0-9]+(?:-[a-z0-9]+)*$")
_CANDIDATE_ID_RE = re.compile(r"^candidate-[a-z0-9]+(?:-[a-z0-9]+)*--[0-9a-f]{12}$")
_DOI_RE = re.compile(r"^10\.\S+$", re.IGNORECASE)
_ALLOWED_OPERATOR_STATUS = {"candidate", "selected", "hidden", "rejected"}
_ALLOWED_IMPORT_STATUS = {"not_imported", "importing", "imported", "skipped", "failed", "duplicate"}


@dataclass(frozen=True)
class CandidateQueue:
    site_path: Path
    space_name: str
    question_id: str

    @property
    def root(self) -> Path:
        return self.site_path / "scouting" / "spaces" / self.space_name / "questions" / self.question_id

    @property
    def candidates_root(self) -> Path:
        return self.root / "candidates"

    @property
    def runs_root(self) -> Path:
        return self.root / "runs"


def candidate_queue(*, site_path: Path, space_name: str, question_id: str) -> CandidateQueue:
    normalized_space = _require_slug(space_name, "space_name")
    normalized_question = _require_question_id(question_id)
    return CandidateQueue(
        site_path=site_path.resolve(),
        space_name=normalized_space,
        question_id=normalized_question,
    )


def load_candidates(queue: CandidateQueue) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if not queue.candidates_root.is_dir():
        return []
    for path in sorted(queue.candidates_root.glob("candidate-*.json")):
        payload = json.loads(path.read_text())
        validate_candidate_record(payload, queue=queue, path=path)
        candidates.append(payload)
    _validate_queue_duplicates(candidates)
    return sorted(candidates, key=_candidate_sort_key)


def write_candidate(queue: CandidateQueue, candidate: dict[str, Any]) -> Path:
    validate_candidate_record(candidate, queue=queue)
    path = queue.candidates_root / f"{candidate['candidate_id']}.json"
    _atomic_write_json(path, candidate)
    return path


def append_scouted_candidates(
    *,
    queue: CandidateQueue,
    semantic_payload: dict[str, Any],
    run_id: str,
    semantic_output_path: Path,
    scouted_at: str | None = None,
) -> list[dict[str, Any]]:
    if semantic_payload.get("space_name") != queue.space_name:
        raise ValueError("source_scouting output space_name does not match target queue.")
    if semantic_payload.get("question_id") != queue.question_id:
        raise ValueError("source_scouting output question_id does not match target queue.")
    question_text = _require_non_empty(str(semantic_payload.get("question_text") or ""), "question_text")
    timestamp = scouted_at or format_timestamp_rfc3339_utc(datetime.now(UTC))
    existing_by_key = {
        key: candidate
        for candidate in load_candidates(queue)
        for key in _candidate_duplicate_keys(candidate)
    }

    records: list[dict[str, Any]] = []
    seen_output_keys: set[str] = set()
    raw_candidates = semantic_payload.get("candidates")
    if not isinstance(raw_candidates, list):
        raise ValueError("source_scouting output requires candidates array.")
    for raw_candidate in raw_candidates:
        if not isinstance(raw_candidate, dict):
            raise ValueError("source_scouting candidates must be objects.")
        record = normalize_candidate_record(
            raw_candidate=raw_candidate,
            queue=queue,
            question_text=question_text,
            run_id=run_id,
            semantic_output_path=semantic_output_path,
            scouted_at=timestamp,
        )
        duplicate_keys = _candidate_duplicate_keys(record)
        if seen_output_keys.intersection(duplicate_keys):
            continue
        seen_output_keys.update(duplicate_keys)
        existing = next((existing_by_key[key] for key in duplicate_keys if key in existing_by_key), None)
        if existing is not None:
            record["candidate_id"] = existing["candidate_id"]
            if existing.get("import_status") == "imported":
                record["import_status"] = "imported"
                record["import_link"] = existing.get("import_link")
        write_candidate(queue, record)
        records.append(record)
    _write_queue_manifest(queue)
    return sorted(records, key=_candidate_sort_key)


def normalize_candidate_record(
    *,
    raw_candidate: dict[str, Any],
    queue: CandidateQueue,
    question_text: str,
    run_id: str,
    semantic_output_path: Path,
    scouted_at: str,
) -> dict[str, Any]:
    title = _require_non_empty(str(raw_candidate.get("title") or ""), "title")
    candidate_id = raw_candidate.get("candidate_id")
    if isinstance(candidate_id, str) and candidate_id.strip():
        normalized_candidate_id = candidate_id.strip()
        if not _CANDIDATE_ID_RE.fullmatch(normalized_candidate_id):
            raise ValueError(f"Invalid candidate_id: {normalized_candidate_id}")
    else:
        normalized_candidate_id = make_candidate_id(raw_candidate)

    record = {
        "schema_version": "source_scouting_candidate_v1",
        "candidate_id": normalized_candidate_id,
        "space_name": queue.space_name,
        "question_id": queue.question_id,
        "question_text": question_text,
        "title": title,
        "authors": _normalize_string_list(raw_candidate.get("authors")),
        "venue": _require_dict(raw_candidate.get("venue"), "venue"),
        "publication_year": raw_candidate.get("publication_year"),
        "doi": _normalize_optional_doi(raw_candidate.get("doi")),
        "landing_url": _normalize_locator(raw_candidate.get("landing_url"), "landing_url"),
        "pdf_url": _normalize_optional_locator(raw_candidate.get("pdf_url"), "pdf_url"),
        "public_access": _require_public_access(raw_candidate.get("public_access")),
        "citation_signal": _require_dict(raw_candidate.get("citation_signal"), "citation_signal"),
        "ranking": _require_ranking(raw_candidate.get("ranking")),
        "operator_status": "candidate",
        "import_status": "not_imported",
        "import_link": None,
        "skip_reason": None,
        "failure_reason": None,
        "provenance": {
            "scouted_at": scouted_at,
            "scouting_run_id": run_id,
            "semantic_output_path": str(semantic_output_path),
        },
    }
    validate_candidate_record(record, queue=queue)
    return record


def make_candidate_id(raw_candidate: dict[str, Any]) -> str:
    title = str(raw_candidate.get("title") or "candidate")
    slug = slugify(title)[:64].rstrip("-") or "candidate"
    key_payload = json.dumps(
        {
            "title": title,
            "doi": raw_candidate.get("doi"),
            "landing_url": raw_candidate.get("landing_url"),
            "pdf_url": raw_candidate.get("pdf_url"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(key_payload.encode("utf-8")).hexdigest()[:12]
    return f"candidate-{slug}--{digest}"


def validate_candidate_record(
    candidate: dict[str, Any],
    *,
    queue: CandidateQueue,
    path: Path | None = None,
) -> None:
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "source_scouting_candidate.v1.schema.json"
    require_valid_json_instance(candidate, load_json_schema(schema_path))
    if candidate.get("space_name") != queue.space_name:
        raise ValueError(f"Candidate space_name does not match queue: {path or candidate.get('candidate_id')}")
    if candidate.get("question_id") != queue.question_id:
        raise ValueError(f"Candidate question_id does not match queue: {path or candidate.get('candidate_id')}")
    if candidate.get("operator_status") not in _ALLOWED_OPERATOR_STATUS:
        raise ValueError("Invalid candidate operator_status.")
    if candidate.get("import_status") not in _ALLOWED_IMPORT_STATUS:
        raise ValueError("Invalid candidate import_status.")
    if not _candidate_duplicate_keys(candidate):
        raise ValueError("Candidate requires DOI, landing_url, or pdf_url provenance.")
    _require_ranking(candidate.get("ranking"))
    _require_public_access(candidate.get("public_access"))


def select_importable_candidates(
    *,
    queue: CandidateQueue,
    count: int,
    include_selected_only: bool = False,
) -> list[dict[str, Any]]:
    if count <= 0:
        raise ValueError("count must be positive.")
    candidates = load_candidates(queue)
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if include_selected_only and candidate.get("operator_status") != "selected":
            continue
        if candidate.get("operator_status") in {"hidden", "rejected"}:
            continue
        if candidate.get("import_status") in {"imported", "duplicate", "skipped"}:
            continue
        public_access = candidate.get("public_access")
        has_public_pdf = isinstance(public_access, dict) and public_access.get("has_public_pdf") is True
        if not has_public_pdf or not candidate.get("pdf_url"):
            continue
        selected.append(candidate)
        if len(selected) >= count:
            break
    return selected


def update_candidate_status(
    *,
    queue: CandidateQueue,
    candidate_id: str,
    import_status: str | None = None,
    operator_status: str | None = None,
    import_link: dict[str, Any] | None = None,
    skip_reason: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    candidates = {candidate["candidate_id"]: candidate for candidate in load_candidates(queue)}
    if candidate_id not in candidates:
        raise FileNotFoundError(f"Scouting candidate not found: {candidate_id}")
    candidate = dict(candidates[candidate_id])
    if import_status is not None:
        if import_status not in _ALLOWED_IMPORT_STATUS:
            raise ValueError(f"Invalid import_status: {import_status}")
        candidate["import_status"] = import_status
    if operator_status is not None:
        if operator_status not in _ALLOWED_OPERATOR_STATUS:
            raise ValueError(f"Invalid operator_status: {operator_status}")
        candidate["operator_status"] = operator_status
    if import_link is not None:
        candidate["import_link"] = import_link
    if skip_reason is not None:
        candidate["skip_reason"] = skip_reason
    if failure_reason is not None:
        candidate["failure_reason"] = failure_reason
    write_candidate(queue, candidate)
    _write_queue_manifest(queue)
    return candidate


def _candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, str]:
    ranking = candidate.get("ranking") if isinstance(candidate.get("ranking"), dict) else {}
    rank = ranking.get("rank")
    overall = ranking.get("overall_score")
    return (
        int(rank) if isinstance(rank, int) else 1_000_000,
        -(int(overall) if isinstance(overall, int) else 0),
        str(candidate.get("candidate_id") or ""),
    )


def _write_queue_manifest(queue: CandidateQueue) -> Path:
    candidates = load_candidates(queue)
    manifest = {
        "schema_version": "source_scouting_queue_v1",
        "space_name": queue.space_name,
        "question_id": queue.question_id,
        "candidate_count": len(candidates),
        "candidate_ids": [candidate["candidate_id"] for candidate in candidates],
        "updated_at": format_timestamp_rfc3339_utc(datetime.now(UTC)),
    }
    path = queue.root / "queue.json"
    _atomic_write_json(path, manifest)
    return path


def _validate_queue_duplicates(candidates: list[dict[str, Any]]) -> None:
    seen: dict[str, str] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        for key in _candidate_duplicate_keys(candidate):
            if key in seen and seen[key] != candidate_id:
                raise ValueError(f"Duplicate scouting candidate provenance key `{key}`.")
            seen[key] = candidate_id


def _candidate_duplicate_keys(candidate: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    doi = candidate.get("doi")
    if isinstance(doi, str) and doi.strip():
        keys.add("doi:" + doi.strip().casefold())
    for field in ("landing_url", "pdf_url"):
        raw = candidate.get(field)
        if isinstance(raw, str) and raw.strip():
            keys.add(field + ":" + _normalize_url_key(raw))
    return keys


def _require_slug(raw: str, field_name: str) -> str:
    value = _require_non_empty(raw, field_name)
    if slugify(value) != value:
        raise ValueError(f"{field_name} must be a slug.")
    return value


def _require_question_id(raw: str) -> str:
    value = _require_non_empty(raw, "question_id")
    if not _QUESTION_ID_RE.fullmatch(value):
        raise ValueError(f"Invalid question_id: {value}")
    return value


def _require_non_empty(raw: str, field_name: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty.")
    return value


def _require_dict(raw: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"{field_name} must be an object.")
    return dict(raw)


def _normalize_string_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [" ".join(str(item).split()) for item in raw if str(item).strip()]


def _normalize_optional_doi(raw: Any) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    if not _DOI_RE.fullmatch(value):
        raise ValueError(f"Invalid DOI: {value}")
    return value


def _normalize_locator(raw: Any, field_name: str) -> str:
    value = _require_non_empty(str(raw or ""), field_name)
    _validate_locator(value, field_name)
    return value


def _normalize_optional_locator(raw: Any, field_name: str) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    _validate_locator(value, field_name)
    return value


def _validate_locator(value: str, field_name: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return
    path = Path(value).expanduser()
    if path.is_absolute() or value.startswith("."):
        return
    if field_name == "landing_url":
        raise ValueError(f"{field_name} must be an absolute http(s) URL or local test fixture path.")


def _normalize_url_key(raw: str) -> str:
    parsed = urlparse(raw.strip())
    if parsed.scheme and parsed.netloc:
        return parsed._replace(fragment="").geturl().rstrip("/").casefold()
    return str(Path(raw).expanduser())


def _require_public_access(raw: Any) -> dict[str, Any]:
    payload = _require_dict(raw, "public_access")
    if not isinstance(payload.get("has_public_pdf"), bool):
        raise ValueError("public_access.has_public_pdf must be boolean.")
    if str(payload.get("access_status") or "") not in {
        "public_pdf",
        "landing_page_only",
        "restricted",
        "unknown",
    }:
        raise ValueError("Invalid public_access.access_status.")
    if not str(payload.get("evidence") or "").strip():
        raise ValueError("public_access.evidence must be non-empty.")
    return payload


def _require_ranking(raw: Any) -> dict[str, Any]:
    payload = _require_dict(raw, "ranking")
    required_rationales = ("answer_fit_rationale", "interestingness_rationale", "overall_rationale")
    for key in required_rationales:
        if not str(payload.get(key) or "").strip():
            raise ValueError(f"ranking.{key} must be non-empty.")
    for key in ("rank", "answer_fit_score", "venue_reputation_score", "citation_score", "interestingness_score", "overall_score"):
        if not isinstance(payload.get(key), int):
            raise ValueError(f"ranking.{key} must be an integer.")
    return payload


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp.{secrets.token_hex(8)}")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp_path.replace(path)
