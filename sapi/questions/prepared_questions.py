"""Canonical prepared-question records and seed authoring helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable

from sapi.contracts.schemas import (
    SchemaValidationError,
    load_json_schema,
    require_valid_json_instance,
)


QUESTION_SCHEMA_VERSION = "prepared_question_v1"
QUESTION_ID_RE = re.compile(r"^question-[a-z0-9]+(?:-[a-z0-9]+)*(?:--[0-9a-f]{12,})?$")
QUESTION_STATUS_VALUES = {"active", "inactive", "draft"}
_PREPARED_QUESTION_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "schemas" / "prepared_question.v1.schema.json"
)


@dataclass(frozen=True)
class PreparedQuestionSeed:
    """Operator-authored seed row for one prepared question."""

    space_name: str
    question_id: str
    display_order: int
    question: str
    status: str = "active"


@dataclass(frozen=True)
class PreparedQuestion:
    """Validated canonical prepared-question record."""

    question_id: str
    question: str
    status: str
    display_order: int
    scope_space_name: str
    linked_source_ids: tuple[str, ...]
    claim_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    measurement_ids: tuple[str, ...]
    synthesis: dict[str, Any]
    freshness: dict[str, Any]
    warnings: tuple[str, ...]
    path: Path


def parse_prepared_question_seed_tsv(tsv_path: Path) -> list[PreparedQuestionSeed]:
    """Parse operator-authored prepared-question TSV seed data."""
    rows: list[PreparedQuestionSeed] = []
    seen_ids: set[tuple[str, str]] = set()
    seen_orders: set[tuple[str, int]] = set()
    for line_number, raw_line in enumerate(tsv_path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw_line.split("\t")
        if len(parts) == 4:
            space_name, question_id, display_order_raw, question = (part.strip() for part in parts)
            status = "active"
        elif len(parts) == 5:
            space_name, question_id, display_order_raw, status, question = (part.strip() for part in parts)
        else:
            raise ValueError(
                f"{tsv_path}:{line_number}: expected 4 or 5 tab-separated fields: "
                "space_name, question_id, display_order, [status], question."
            )
        if not space_name:
            raise ValueError(f"{tsv_path}:{line_number}: space_name must be non-empty.")
        _validate_question_id(question_id, path=tsv_path, field="question_id")
        if status not in QUESTION_STATUS_VALUES:
            raise ValueError(
                f"{tsv_path}:{line_number}: status must be one of "
                f"{', '.join(sorted(QUESTION_STATUS_VALUES))}."
            )
        if not question:
            raise ValueError(f"{tsv_path}:{line_number}: question must be non-empty.")
        try:
            display_order = int(display_order_raw)
        except ValueError as exc:
            raise ValueError(f"{tsv_path}:{line_number}: display_order must be an integer.") from exc
        if display_order < 1:
            raise ValueError(f"{tsv_path}:{line_number}: display_order must be >= 1.")
        id_key = (space_name, question_id)
        if id_key in seen_ids:
            raise ValueError(f"{tsv_path}:{line_number}: duplicate question_id in {space_name}: {question_id}.")
        order_key = (space_name, display_order)
        if order_key in seen_orders:
            raise ValueError(
                f"{tsv_path}:{line_number}: duplicate display_order in {space_name}: {display_order}."
            )
        seen_ids.add(id_key)
        seen_orders.add(order_key)
        rows.append(
            PreparedQuestionSeed(
                space_name=space_name,
                question_id=question_id,
                display_order=display_order,
                question=question,
                status=status,
            )
        )
    return rows


def load_prepared_questions(space_root: Path, *, space_name: str | None = None) -> list[PreparedQuestion]:
    """Load canonical prepared-question records for one space."""
    questions_root = space_root / "questions"
    if not questions_root.is_dir():
        return []
    questions: list[PreparedQuestion] = []
    seen_ids: dict[str, Path] = {}
    seen_orders: dict[int, Path] = {}
    expected_space_name = space_name or space_root.name
    for path in sorted(questions_root.glob("question-*.json")):
        payload = _read_json_object(path)
        question = _prepared_question_from_payload(
            payload=payload,
            path=path,
            space_root=space_root,
            expected_space_name=expected_space_name,
        )
        if path.stem != question.question_id:
            raise ValueError(
                f"{path}: filename must match question_id {question.question_id!r}."
            )
        if question.question_id in seen_ids:
            raise ValueError(
                f"{path}: duplicate question_id {question.question_id!r}; "
                f"first seen in {seen_ids[question.question_id]}."
            )
        if question.display_order in seen_orders:
            raise ValueError(
                f"{path}: duplicate display_order {question.display_order}; "
                f"first seen in {seen_orders[question.display_order]}."
            )
        seen_ids[question.question_id] = path
        seen_orders[question.display_order] = path
        questions.append(question)
    return sorted(questions, key=lambda item: (item.display_order, item.question_id))


def active_prepared_questions(space_root: Path, *, space_name: str | None = None) -> list[PreparedQuestion]:
    """Load active canonical prepared questions for default rendering and mapping."""
    return [
        question
        for question in load_prepared_questions(space_root, space_name=space_name)
        if question.status == "active"
    ]


def upsert_prepared_question_seeds(
    *,
    space_root: Path,
    space_name: str,
    seeds: Iterable[PreparedQuestionSeed],
) -> list[Path]:
    """Create or update canonical prepared-question records from operator-authored seeds."""
    questions_root = space_root / "questions"
    questions_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for seed in sorted(seeds, key=lambda item: (item.display_order, item.question_id)):
        if seed.space_name != space_name:
            raise ValueError(
                f"Cannot write question seed for {seed.space_name!r} into space {space_name!r}."
            )
        path = questions_root / f"{seed.question_id}.json"
        existing = _read_json_object(path) if path.is_file() else {}
        payload = {
            "schema_version": QUESTION_SCHEMA_VERSION,
            "question_id": seed.question_id,
            "question": seed.question,
            "status": seed.status,
            "display_order": seed.display_order,
            "scope": {"space_name": space_name},
            "linked_source_ids": _existing_string_list(existing, "linked_source_ids"),
            "claim_ids": _existing_string_list(existing, "claim_ids"),
            "evidence_ids": _existing_string_list(existing, "evidence_ids"),
            "measurement_ids": _existing_string_list(existing, "measurement_ids"),
            "synthesis": _existing_object(existing, "synthesis"),
            "freshness": _existing_object(existing, "freshness"),
            "warnings": _existing_string_list(existing, "warnings"),
        }
        written.append(
            write_prepared_question_record(
                space_root=space_root,
                space_name=space_name,
                payload=payload,
            )
        )
    return written


def write_prepared_question_record(
    *,
    space_root: Path,
    space_name: str,
    payload: dict[str, Any],
) -> Path:
    """Validate and write one canonical prepared-question record."""
    unknown_path = space_root / "questions" / "unknown.json"
    question_id = _required_string(payload, "question_id", path=unknown_path)
    _validate_question_id(question_id, path=unknown_path, field="question_id")
    path = space_root / "questions" / f"{question_id}.json"
    _prepared_question_from_payload(
        payload=payload,
        path=path,
        space_root=space_root,
        expected_space_name=space_name,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def _prepared_question_from_payload(
    *,
    payload: dict[str, Any],
    path: Path,
    space_root: Path | None = None,
    expected_space_name: str | None = None,
) -> PreparedQuestion:
    _require_valid_question_schema(payload=payload, path=path)
    if payload.get("schema_version") != QUESTION_SCHEMA_VERSION:
        raise ValueError(f"{path}: schema_version must be {QUESTION_SCHEMA_VERSION!r}.")
    question_id = _required_string(payload, "question_id", path=path)
    _validate_question_id(question_id, path=path, field="question_id")
    question = _required_string(payload, "question", path=path)
    status = _required_string(payload, "status", path=path)
    if status not in QUESTION_STATUS_VALUES:
        raise ValueError(
            f"{path}: status must be one of {', '.join(sorted(QUESTION_STATUS_VALUES))}."
        )
    display_order = payload.get("display_order")
    if not isinstance(display_order, int) or display_order < 1:
        raise ValueError(f"{path}: display_order must be an integer >= 1.")
    scope = payload.get("scope")
    if not isinstance(scope, dict):
        raise ValueError(f"{path}: scope must be an object.")
    scope_space_name = _required_string(scope, "space_name", path=path)
    if expected_space_name is not None and scope_space_name != expected_space_name:
        raise ValueError(
            f"{path}: scope.space_name must match containing space {expected_space_name!r}."
        )
    linked_source_ids = _required_string_list(payload, "linked_source_ids", path=path)
    claim_ids = _required_string_list(payload, "claim_ids", path=path)
    evidence_ids = _required_string_list(payload, "evidence_ids", path=path)
    measurement_ids = _required_string_list(payload, "measurement_ids", path=path)
    warnings = _required_string_list(payload, "warnings", path=path)
    if space_root is not None:
        _validate_link_targets(
            space_root=space_root,
            path=path,
            linked_source_ids=linked_source_ids,
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
        )
    synthesis = _existing_object(payload, "synthesis")
    freshness = _existing_object(payload, "freshness")
    return PreparedQuestion(
        question_id=question_id,
        question=question,
        status=status,
        display_order=display_order,
        scope_space_name=scope_space_name,
        linked_source_ids=tuple(linked_source_ids),
        claim_ids=tuple(claim_ids),
        evidence_ids=tuple(evidence_ids),
        measurement_ids=tuple(measurement_ids),
        synthesis=synthesis,
        freshness=freshness,
        warnings=tuple(warnings),
        path=path,
    )


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object.")
    return payload


def _required_string(payload: dict[str, Any], field: str, *, path: Path) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {field} must be a non-empty string.")
    return value.strip()


def _validate_question_id(question_id: str, *, path: Path, field: str) -> None:
    if not QUESTION_ID_RE.fullmatch(question_id):
        raise ValueError(
            f"{path}: {field} must match question slug format, e.g. question-protein-intake."
        )


def _existing_object(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    return value if isinstance(value, dict) else {}


def _existing_string_list(payload: dict[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        return []
    strings: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            strings.append(item.strip())
    return strings


def _required_string_list(payload: dict[str, Any], field: str, *, path: Path) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list):
        raise ValueError(f"{path}: {field} must be an array.")
    strings: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{path}: {field}[{index}] must be a non-empty string.")
        normalized = item.strip()
        if normalized in seen:
            raise ValueError(f"{path}: {field} contains duplicate value {normalized!r}.")
        seen.add(normalized)
        strings.append(normalized)
    return strings


def _require_valid_question_schema(*, payload: dict[str, Any], path: Path) -> None:
    try:
        require_valid_json_instance(
            payload,
            load_json_schema(_PREPARED_QUESTION_SCHEMA_PATH),
        )
    except SchemaValidationError as exc:
        details = "; ".join(
            f"{issue.path}: {issue.message}"
            for issue in exc.issues[:5]
        )
        raise ValueError(f"{path}: invalid prepared question record: {details}") from exc


def _validate_link_targets(
    *,
    space_root: Path,
    path: Path,
    linked_source_ids: list[str],
    claim_ids: list[str],
    evidence_ids: list[str],
) -> None:
    for source_id in linked_source_ids:
        _require_link_record(
            space_root=space_root,
            path=path,
            record_path=space_root / "sources" / "records" / f"{source_id}.json",
            field="source_id",
            value=source_id,
        )
    for claim_id in claim_ids:
        _require_link_record(
            space_root=space_root,
            path=path,
            record_path=space_root / "claims" / f"{claim_id}.json",
            field="claim_id",
            value=claim_id,
        )
    for evidence_id in evidence_ids:
        _require_link_record(
            space_root=space_root,
            path=path,
            record_path=space_root / "evidence" / f"{evidence_id}.json",
            field="evidence_id",
            value=evidence_id,
        )


def _require_link_record(
    *,
    space_root: Path,
    path: Path,
    record_path: Path,
    field: str,
    value: str,
) -> None:
    try:
        record_path.relative_to(space_root)
    except ValueError as exc:
        raise ValueError(f"{path}: linked {field} path escapes the space root: {record_path}") from exc
    if not record_path.is_file():
        raise ValueError(f"{path}: linked {field} not found: {value}")
    record = _read_json_object(record_path)
    observed = record.get(field)
    if observed != value:
        raise ValueError(
            f"{path}: linked {field} record {record_path} contains {observed!r}, expected {value!r}."
        )
