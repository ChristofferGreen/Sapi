"""Prepared-question lint checks shared by validation and refresh workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sapi.lint.lint_engine import LintIssue
from sapi.questions.prepared_questions import PreparedQuestion, load_prepared_questions
from sapi.questions.synthesis import build_question_synthesis_context


def collect_question_lint_issues(
    space_root: Path,
    *,
    include_site_output: bool = True,
) -> list[LintIssue]:
    """Collect lint diagnostics for canonical prepared-question state."""
    try:
        questions = load_prepared_questions(space_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [
            LintIssue(
                check_id="prepared_question_invalid",
                severity="error",
                message=str(exc),
                path=str(space_root / "questions"),
            )
        ]

    issues: list[LintIssue] = []
    for question in questions:
        issues.extend(_collect_synthesis_freshness_issues(space_root=space_root, question=question))
        issues.extend(_collect_measurement_issues(space_root=space_root, question=question))
    if include_site_output:
        issues.extend(_collect_site_output_issues(space_root=space_root, questions=questions))
    return sorted(
        issues,
        key=lambda issue: (
            issue.severity or "",
            issue.check_id,
            issue.path or "",
            issue.message,
        ),
    )


def _collect_synthesis_freshness_issues(
    *,
    space_root: Path,
    question: PreparedQuestion,
) -> list[LintIssue]:
    has_linked_context = bool(
        question.linked_source_ids
        or question.claim_ids
        or question.evidence_ids
        or question.measurement_ids
    )
    if not has_linked_context and not question.synthesis:
        return []

    freshness = question.freshness.get("question_synthesis")
    if not isinstance(freshness, dict):
        observed_signature = None
    else:
        observed = freshness.get("input_signature")
        observed_signature = observed if isinstance(observed, str) and observed else None
    expected_signature = build_question_synthesis_context(
        space_root=space_root,
        question=question,
    ).input_signature
    if observed_signature == expected_signature:
        return []

    return [
        LintIssue(
            check_id="stale_question_synthesis",
            severity="warning",
            message=(
                f"Prepared question {question.question_id} has stale or missing synthesis freshness metadata."
            ),
            path=str(question.path),
        )
    ]


def _collect_measurement_issues(
    *,
    space_root: Path,
    question: PreparedQuestion,
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for measurement_id in question.measurement_ids:
        measurement_path = space_root / "measurements" / f"{measurement_id}.json"
        if not measurement_path.is_file():
            issues.append(
                LintIssue(
                    check_id="invalid_question_measurement",
                    severity="error",
                    message=(
                        f"Prepared question {question.question_id} references missing measurement {measurement_id}."
                    ),
                    path=str(question.path),
                )
            )
            continue
        try:
            payload = _read_json_object(measurement_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(
                LintIssue(
                    check_id="invalid_question_measurement",
                    severity="error",
                    message=f"Measurement {measurement_id} is not a valid JSON object: {exc}",
                    path=str(measurement_path),
                )
            )
            continue
        issues.extend(
            _validate_measurement_payload(
                question=question,
                measurement_id=measurement_id,
                measurement_path=measurement_path,
                payload=payload,
            )
        )
    return issues


def _validate_measurement_payload(
    *,
    question: PreparedQuestion,
    measurement_id: str,
    measurement_path: Path,
    payload: dict[str, Any],
) -> list[LintIssue]:
    issues: list[LintIssue] = []
    if payload.get("measurement_id") != measurement_id:
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=(
                    f"Measurement file for {measurement_id} contains measurement_id "
                    f"{payload.get('measurement_id')!r}."
                ),
            )
        )
    question_id = payload.get("question_id")
    if question_id is not None and question_id != question.question_id:
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=(
                    f"Measurement {measurement_id} belongs to question_id {question_id!r}, "
                    f"not {question.question_id!r}."
                ),
            )
        )
    value = payload.get("value")
    if not isinstance(value, int | float) or isinstance(value, bool):
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=f"Measurement {measurement_id} must contain numeric value.",
            )
        )
    value_max = payload.get("value_max")
    if value_max is not None and (
        not isinstance(value_max, int | float) or isinstance(value_max, bool)
    ):
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=f"Measurement {measurement_id} value_max must be numeric or null.",
            )
        )
    if isinstance(value, int | float) and isinstance(value_max, int | float) and value_max < value:
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=f"Measurement {measurement_id} value_max must be greater than or equal to value.",
            )
        )
    for field in ("measure_name", "outcome"):
        text = payload.get(field)
        if not isinstance(text, str) or not text.strip():
            issues.append(
                _measurement_issue(
                    measurement_path=measurement_path,
                    message=f"Measurement {measurement_id} must contain a non-empty {field}.",
                )
            )
    unit = payload.get("unit")
    if not isinstance(unit, str) or not unit.strip():
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=f"Measurement {measurement_id} must contain a non-empty unit.",
            )
        )
    source_id = payload.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=f"Measurement {measurement_id} must reference a linked source_id.",
            )
        )
    elif source_id not in set(question.linked_source_ids):
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=(
                    f"Measurement {measurement_id} references unlinked source_id {source_id!r}."
                ),
            )
        )
    claim_id = payload.get("claim_id")
    evidence_id = payload.get("evidence_id")
    if claim_id is not None and claim_id not in set(question.claim_ids):
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=f"Measurement {measurement_id} references unlinked claim_id {claim_id!r}.",
            )
        )
    if evidence_id is not None and evidence_id not in set(question.evidence_ids):
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=(
                    f"Measurement {measurement_id} references unlinked evidence_id {evidence_id!r}."
                ),
            )
        )
    if claim_id is None and evidence_id is None:
        issues.append(
            _measurement_issue(
                measurement_path=measurement_path,
                message=f"Measurement {measurement_id} must reference a linked claim or evidence item.",
            )
        )
    return issues


def _measurement_issue(*, measurement_path: Path, message: str) -> LintIssue:
    return LintIssue(
        check_id="invalid_question_measurement",
        severity="error",
        message=message,
        path=str(measurement_path),
    )


def _collect_site_output_issues(
    *,
    space_root: Path,
    questions: list[PreparedQuestion],
) -> list[LintIssue]:
    active_questions = [question for question in questions if question.status == "active"]
    if not active_questions:
        return []
    site_root = space_root / "site"
    if not site_root.exists():
        return []

    issues: list[LintIssue] = []
    home_path = site_root / "index.html"
    question_index_path = site_root / "questions" / "index.html"
    home_text = home_path.read_text() if home_path.is_file() else ""
    question_index_text = question_index_path.read_text() if question_index_path.is_file() else ""

    if 'data-front-page="questions"' not in home_text:
        issues.append(
            LintIssue(
                check_id="missing_question_front_page",
                severity="error",
                message="Built space home is missing the prepared-question front-page marker.",
                path=str(home_path),
            )
        )
    if not question_index_path.is_file():
        issues.append(
            LintIssue(
                check_id="missing_question_front_page",
                severity="error",
                message="Built question index is missing.",
                path=str(question_index_path),
            )
        )

    for question in active_questions:
        detail_href = f"questions/{question.question_id}.html"
        if detail_href not in home_text:
            issues.append(
                LintIssue(
                    check_id="missing_question_front_page",
                    severity="error",
                    message=(
                        f"Built space home is missing active question link {question.question_id}."
                    ),
                    path=str(home_path),
                )
            )
        if question.question_id not in question_index_text:
            issues.append(
                LintIssue(
                    check_id="missing_question_front_page",
                    severity="error",
                    message=(
                        f"Built question index is missing active question {question.question_id}."
                    ),
                    path=str(question_index_path),
                )
            )
    return issues


def _read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object.")
    return payload
