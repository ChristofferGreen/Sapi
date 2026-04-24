"""ID and temporal-format helpers for Section 5.4 contracts."""

from __future__ import annotations

from datetime import UTC, date, datetime
import hashlib
import re
import secrets


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DETERMINISTIC_SUFFIX_RE = re.compile(r"^[0-9a-f]{12,}$")
EXECUTION_SUFFIX_RE = re.compile(r"^[a-z0-9]{10,}$")
RFC3339_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
COMPACT_UTC_TIMESTAMP_RE = re.compile(r"^\d{8}T\d{6}Z$")

_CONTENT_PREFIXES = {"source", "claim", "concept", "topic", "family"}


def slugify(value: str) -> str:
    """Convert arbitrary text to lowercase kebab-case slug."""
    lowered = value.lower().strip()
    collapsed = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    if not collapsed:
        raise ValueError("Slug source produced an empty slug.")
    if not SLUG_RE.fullmatch(collapsed):
        raise ValueError(f"Invalid slug after normalization: {collapsed}")
    return collapsed


def format_timestamp_rfc3339_utc(moment: datetime | None = None) -> str:
    """Format UTC timestamp fields as RFC 3339 with trailing Z."""
    dt = _as_utc(moment)
    value = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    if not RFC3339_UTC_RE.fullmatch(value):
        raise ValueError(f"Invalid RFC3339 UTC timestamp: {value}")
    return value


def format_date_iso(value: date) -> str:
    """Format date-only fields as ISO-8601 YYYY-MM-DD."""
    rendered = value.isoformat()
    if not ISO_DATE_RE.fullmatch(rendered):
        raise ValueError(f"Invalid ISO date: {rendered}")
    return rendered


def format_compact_utc_timestamp(moment: datetime | None = None) -> str:
    """Format compact UTC timestamps used inside IDs."""
    dt = _as_utc(moment)
    value = dt.strftime("%Y%m%dT%H%M%SZ")
    if not COMPACT_UTC_TIMESTAMP_RE.fullmatch(value):
        raise ValueError(f"Invalid compact UTC timestamp: {value}")
    return value


def make_deterministic_content_id(
    prefix: str,
    *,
    slug: str,
    canonical_payload: str | bytes,
    suffix_length: int = 12,
) -> str:
    """Build deterministic `<prefix>-<slug>--<suffix>` IDs."""
    if prefix not in _CONTENT_PREFIXES:
        raise ValueError(f"Unsupported deterministic content ID prefix: {prefix}")
    _validate_slug(slug)
    if suffix_length < 12:
        raise ValueError("Deterministic suffix length must be at least 12.")

    payload_bytes = canonical_payload.encode("utf-8") if isinstance(canonical_payload, str) else canonical_payload
    suffix = hashlib.sha256(payload_bytes).hexdigest()[:suffix_length]
    if not DETERMINISTIC_SUFFIX_RE.fullmatch(suffix):
        raise ValueError(f"Invalid deterministic suffix: {suffix}")
    return f"{prefix}-{slug}--{suffix}"


def make_source_id(*, slug: str, canonical_payload: str | bytes, suffix_length: int = 12) -> str:
    return make_deterministic_content_id(
        "source",
        slug=slug,
        canonical_payload=canonical_payload,
        suffix_length=suffix_length,
    )


def make_claim_id(*, slug: str, canonical_payload: str | bytes, suffix_length: int = 12) -> str:
    return make_deterministic_content_id(
        "claim",
        slug=slug,
        canonical_payload=canonical_payload,
        suffix_length=suffix_length,
    )


def make_concept_id(*, slug: str, canonical_payload: str | bytes, suffix_length: int = 12) -> str:
    return make_deterministic_content_id(
        "concept",
        slug=slug,
        canonical_payload=canonical_payload,
        suffix_length=suffix_length,
    )


def make_topic_id(*, slug: str, canonical_payload: str | bytes, suffix_length: int = 12) -> str:
    return make_deterministic_content_id(
        "topic",
        slug=slug,
        canonical_payload=canonical_payload,
        suffix_length=suffix_length,
    )


def make_family_id(*, slug: str, canonical_payload: str | bytes, suffix_length: int = 12) -> str:
    return make_deterministic_content_id(
        "family",
        slug=slug,
        canonical_payload=canonical_payload,
        suffix_length=suffix_length,
    )


def make_run_id(*, moment: datetime | None = None, suffix: str | None = None, suffix_length: int = 10) -> str:
    """Build execution-scoped run ID: `run-<utc_timestamp>--<suffix>`."""
    timestamp = format_compact_utc_timestamp(moment)
    execution_suffix = suffix or generate_execution_suffix(suffix_length)
    _validate_execution_suffix(execution_suffix)
    return f"run-{timestamp}--{execution_suffix}"


def make_query_id(
    *,
    slug: str,
    moment: datetime | None = None,
    suffix: str | None = None,
    suffix_length: int = 10,
) -> str:
    """Build execution-scoped query ID: `query-<utc_timestamp>-<slug>--<suffix>`."""
    _validate_slug(slug)
    timestamp = format_compact_utc_timestamp(moment)
    execution_suffix = suffix or generate_execution_suffix(suffix_length)
    _validate_execution_suffix(execution_suffix)
    return f"query-{timestamp}-{slug}--{execution_suffix}"


def make_comment_uid(*, slug: str, suffix: str | None = None, suffix_length: int = 10) -> str:
    """Build stable comment UID: `comment-<slug>--<suffix>`."""
    _validate_slug(slug)
    execution_suffix = suffix or generate_execution_suffix(suffix_length)
    _validate_execution_suffix(execution_suffix)
    return f"comment-{slug}--{execution_suffix}"


def make_overview_id(*, scope_kind: str, scope_name: str) -> str:
    """Build canonical overview IDs: `space--<slug>` or `subspace--<slug>`."""
    if scope_kind not in {"space", "subspace"}:
        raise ValueError(f"Unsupported overview scope_kind: {scope_kind}")
    scope_slug = slugify(scope_name)
    return f"{scope_kind}--{scope_slug}"


def format_comment_no(value: int) -> str:
    """Render comment ordinal as display-only `pc-###` token."""
    if value <= 0:
        raise ValueError("comment_no must be positive.")
    return f"pc-{value:03d}"


def generate_execution_suffix(length: int = 10) -> str:
    """Generate lowercase URL-safe execution suffix."""
    if length < 10:
        raise ValueError("Execution suffix length must be at least 10.")
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _as_utc(moment: datetime | None) -> datetime:
    if moment is None:
        return datetime.now(UTC)
    if moment.tzinfo is None:
        # Interpret naive values as UTC to preserve explicit UTC contract.
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _validate_slug(slug: str) -> None:
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"Invalid kebab-case slug: {slug}")


def _validate_execution_suffix(suffix: str) -> None:
    if not EXECUTION_SUFFIX_RE.fullmatch(suffix):
        raise ValueError(f"Invalid execution/comment suffix: {suffix}")
