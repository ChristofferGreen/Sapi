"""Repository-seeded persona catalog loading and validation contracts."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


_PERSONA_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_CATALOG_DIR = Path("personas")
_CANONICAL_CATALOG_FILE = _CATALOG_DIR / "social_users.json"
_COMPATIBILITY_CATALOG_FILE = _CATALOG_DIR / "users.json"
_PROFILE_IMAGES_DIR = _CATALOG_DIR / "profile_images"
_REQUIRED_USER_FIELDS: tuple[str, ...] = (
    "display_name",
    "full_name",
    "account_status",
    "stance_profile",
    "profile_image_path",
)


def canonical_persona_catalog_path(*, repo_root: Path) -> Path:
    return (repo_root / _CANONICAL_CATALOG_FILE).resolve()


def compatibility_persona_catalog_path(*, repo_root: Path) -> Path:
    return (repo_root / _COMPATIBILITY_CATALOG_FILE).resolve()


def load_seeded_persona_catalog(
    *,
    repo_root: Path | None = None,
    allow_compatibility_mirror: bool = True,
) -> list[dict[str, Any]]:
    resolved_repo_root = _resolve_repo_root(repo_root)
    canonical_path = canonical_persona_catalog_path(repo_root=resolved_repo_root)
    compatibility_path = compatibility_persona_catalog_path(repo_root=resolved_repo_root)

    if canonical_path.is_file():
        rows = _load_catalog_rows(canonical_path)
    elif allow_compatibility_mirror and compatibility_path.is_file():
        rows = _load_catalog_rows(compatibility_path)
    else:
        raise FileNotFoundError(
            "Persona catalog not found at canonical path "
            f"{canonical_path} or compatibility mirror {compatibility_path}."
        )

    return _normalize_and_validate_rows(rows, repo_root=resolved_repo_root)


def _resolve_repo_root(repo_root: Path | None) -> Path:
    if repo_root is None:
        return Path(__file__).resolve().parents[2]
    return repo_root.resolve()


def _load_catalog_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict):
        rows = payload.get("users")
        if not isinstance(rows, list):
            raise TypeError(f"{path} must contain a list under key 'users'.")
        count = payload.get("count")
        if count is not None:
            if not isinstance(count, int):
                raise TypeError(f"{path} field 'count' must be an integer when present.")
            if count != len(rows):
                raise ValueError(
                    f"{path} field 'count' ({count}) must equal users row count ({len(rows)})."
                )
        return rows
    if isinstance(payload, list):
        return payload
    raise TypeError(f"{path} must be either an object or an array.")


def _normalize_and_validate_rows(
    rows: list[dict[str, Any]],
    *,
    repo_root: Path,
) -> list[dict[str, Any]]:
    normalized_rows: list[dict[str, Any]] = []
    seen_persona_ids: set[str] = set()

    for index, raw_row in enumerate(rows):
        row = _normalize_row(raw_row, row_index=index, repo_root=repo_root)
        persona_id = row["persona_id"]
        if persona_id in seen_persona_ids:
            raise ValueError(f"Duplicate persona_id detected: {persona_id}")
        seen_persona_ids.add(persona_id)
        normalized_rows.append(row)

    return normalized_rows


def _normalize_row(
    raw_row: Any,
    *,
    row_index: int,
    repo_root: Path,
) -> dict[str, Any]:
    if not isinstance(raw_row, dict):
        raise TypeError(f"Persona row at index {row_index} must be an object.")

    row = dict(raw_row)
    legacy_id = row.get("id")
    persona_id = row.get("persona_id")
    if persona_id is None and legacy_id is not None:
        persona_id = legacy_id
    if legacy_id is not None and persona_id is not None and legacy_id != persona_id:
        raise ValueError(
            f"Persona row at index {row_index} has mismatched 'id' and 'persona_id' aliases."
        )
    persona_id = _require_non_empty_string(
        persona_id,
        field_name=f"users[{row_index}].persona_id",
    )
    if not _PERSONA_ID_RE.fullmatch(persona_id):
        raise ValueError(
            f"users[{row_index}].persona_id '{persona_id}' does not match slug contract."
        )
    row["persona_id"] = persona_id
    if "id" in row and row["id"] != persona_id:
        raise ValueError(
            f"users[{row_index}].id must be omitted or equal users[{row_index}].persona_id."
        )

    for field_name in _REQUIRED_USER_FIELDS:
        row[field_name] = _require_non_empty_string(
            row.get(field_name),
            field_name=f"users[{row_index}].{field_name}",
        )

    _resolve_profile_image_path(
        profile_image_path=row["profile_image_path"],
        repo_root=repo_root,
        row_index=row_index,
    )
    return row


def _resolve_profile_image_path(
    *,
    profile_image_path: str,
    repo_root: Path,
    row_index: int,
) -> Path:
    relative_path = Path(profile_image_path)
    if relative_path.is_absolute():
        raise ValueError(
            f"users[{row_index}].profile_image_path must be repo-relative under personas/profile_images/."
        )

    required_prefix = _PROFILE_IMAGES_DIR.parts
    if relative_path.parts[: len(required_prefix)] != required_prefix:
        raise ValueError(
            f"users[{row_index}].profile_image_path must be under personas/profile_images/."
        )

    profile_root = (repo_root / _PROFILE_IMAGES_DIR).resolve()
    resolved = (repo_root / relative_path).resolve()
    try:
        resolved.relative_to(profile_root)
    except ValueError as exc:
        raise ValueError(
            f"users[{row_index}].profile_image_path escapes personas/profile_images/."
        ) from exc
    if not resolved.is_file():
        raise ValueError(
            f"users[{row_index}].profile_image_path does not resolve to an existing image file."
        )
    return resolved


def _require_non_empty_string(raw: Any, *, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return raw.strip()

