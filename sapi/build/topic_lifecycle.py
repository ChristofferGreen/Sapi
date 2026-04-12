"""Topic lifecycle transition and contradiction-gating helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sapi.lint.lint_engine import LintIssue


_ALLOWED_TOPIC_LIFECYCLE_STATES: frozenset[str] = frozenset({"draft", "stable", "final"})


@dataclass(frozen=True)
class TopicLifecycleResolution:
    """Resolved lifecycle view for one topic projection record."""

    declared_state: str
    effective_state: str
    auto_transition: str | None
    final_disputed_contradiction: bool
    lint_issues: tuple[LintIssue, ...]


def resolve_topic_lifecycle(*, topic: dict[str, Any], topic_id: str) -> TopicLifecycleResolution:
    """Resolve lifecycle transitions and final-page contradiction lint behavior."""
    declared_state = _normalize_declared_state(topic.get("lifecycle_state"), topic_id=topic_id)
    major_conflict = _is_truthy(topic.get("major_conflict")) or _is_truthy(topic.get("structural_churn"))
    final_disputed_contradiction = _is_truthy(topic.get("final_disputed_contradiction"))

    effective_state = declared_state
    auto_transition: str | None = None
    if declared_state == "draft" and not major_conflict:
        effective_state = "stable"
        auto_transition = "draft_to_stable"
    elif declared_state == "stable" and major_conflict:
        effective_state = "draft"
        auto_transition = "stable_to_draft"
    elif declared_state == "final":
        # Final pages are never auto-demoted by projection/lint.
        effective_state = "final"

    lint_issues: list[LintIssue] = []
    if effective_state == "final" and final_disputed_contradiction:
        lint_issues.append(
            LintIssue(
                check_id="final_disputed_contradiction",
                severity="error",
                message=(
                    f"{topic_id}: final page has unresolved disputed contradiction; publication workflow "
                    "is blocked until contradiction is resolved or lifecycle is manually reopened."
                ),
                path=f"topics/{topic_id}.json",
            )
        )

    return TopicLifecycleResolution(
        declared_state=declared_state,
        effective_state=effective_state,
        auto_transition=auto_transition,
        final_disputed_contradiction=final_disputed_contradiction,
        lint_issues=tuple(lint_issues),
    )


def validate_manual_lifecycle_transition(*, current_state: str, target_state: str) -> None:
    """Enforce manual-only lifecycle transition boundaries."""
    if current_state not in _ALLOWED_TOPIC_LIFECYCLE_STATES:
        raise ValueError(f"Unsupported current lifecycle state: {current_state!r}")
    if target_state not in _ALLOWED_TOPIC_LIFECYCLE_STATES:
        raise ValueError(f"Unsupported target lifecycle state: {target_state!r}")
    if target_state == "final" and current_state != "stable":
        raise ValueError(
            "Manual transition to `final` is allowed only from `stable` lifecycle state."
        )
    if target_state == "draft" and current_state == "final":
        raise ValueError(
            "Manual transition `final -> draft` is not allowed; reopen to `stable` first."
        )


def normalize_lifecycle_state_for_write(raw_state: Any) -> str:
    if not isinstance(raw_state, str) or not raw_state.strip():
        raise ValueError("lifecycle state must be a non-empty string.")
    normalized = raw_state.strip().lower()
    if normalized not in _ALLOWED_TOPIC_LIFECYCLE_STATES:
        raise ValueError(f"Unsupported lifecycle state: {raw_state!r}")
    return normalized


def _normalize_declared_state(raw_state: Any, *, topic_id: str) -> str:
    if raw_state is None:
        return "draft"
    if not isinstance(raw_state, str) or not raw_state.strip():
        raise ValueError(f"{topic_id}: lifecycle_state must be a non-empty string when present.")
    normalized = raw_state.strip().lower()
    if normalized not in _ALLOWED_TOPIC_LIFECYCLE_STATES:
        raise ValueError(f"{topic_id}: unsupported lifecycle_state value {raw_state!r}.")
    return normalized


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"1", "true", "yes", "y", "on"}
    return False
