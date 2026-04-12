"""Site-scope and subspace metadata contracts (Section 5.7)."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


SITE_SCOPE_SCHEMA_VERSION = "site_scope_v1"
SPACE_SUBSPACES_SCHEMA_VERSION = "space_subspaces_v1"
_SPACE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class SiteScope:
    schema_version: str
    site_name: str
    site_root: str
    site_base_url: str | None


@dataclass(frozen=True)
class SubspaceEntry:
    space_name: str
    space_root: str
    title: str | None
    resolved_space_root: Path


@dataclass(frozen=True)
class SubspacesMetadata:
    schema_version: str
    subspaces: list[SubspaceEntry]


def write_site_scope(
    *,
    site_path: Path,
    site_name: str,
    site_root: str = ".",
    site_base_url: str | None = None,
) -> Path:
    """Write canonical site scope metadata to `<site_path>/site.json`."""
    _require_non_empty(site_name, "site_name")
    _require_non_empty(site_root, "site_root")

    payload: dict[str, Any] = {
        "schema_version": SITE_SCOPE_SCHEMA_VERSION,
        "site_name": site_name,
        "site_root": site_root,
    }
    if site_base_url is not None:
        _require_non_empty(site_base_url, "site_base_url")
        payload["site_base_url"] = site_base_url

    # Enforce contract validation at write time, including site_root resolution rules.
    validate_site_scope_document(payload, site_path=site_path)

    site_json_path = site_path / "site.json"
    site_json_path.parent.mkdir(parents=True, exist_ok=True)
    site_json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return site_json_path


def load_site_scope(
    *,
    site_path: Path,
    space_root: Path | None = None,
    allow_legacy_space_scope_read: bool = False,
) -> SiteScope:
    """Load site scope metadata with explicit compatibility-only legacy fallback."""
    canonical_path = site_path / "site.json"
    if canonical_path.is_file():
        return validate_site_scope_document(
            json.loads(canonical_path.read_text()),
            site_path=site_path,
        )

    if allow_legacy_space_scope_read and space_root is not None:
        legacy_path = space_root / "site.json"
        if legacy_path.is_file():
            return validate_site_scope_document(
                json.loads(legacy_path.read_text()),
                site_path=site_path,
            )

    raise FileNotFoundError(f"Missing canonical site scope file: {canonical_path}")


def validate_site_scope_document(document: dict[str, Any], *, site_path: Path) -> SiteScope:
    """Validate site scope contract and `site_root` resolution semantics."""
    if not isinstance(document, dict):
        raise TypeError("site.json document must be a JSON object.")

    schema_version = document.get("schema_version")
    site_name = document.get("site_name")
    site_root = document.get("site_root")
    site_base_url = document.get("site_base_url")

    if schema_version != SITE_SCOPE_SCHEMA_VERSION:
        raise ValueError(f"Unsupported site scope schema_version: {schema_version}")
    _require_non_empty(site_name, "site_name")
    _require_non_empty(site_root, "site_root")
    if site_base_url is not None:
        _require_non_empty(site_base_url, "site_base_url")

    # Validate root resolution contract: relative values resolve from <site_path>.
    site_root_path = Path(site_root).expanduser()
    resolved = (
        site_root_path.resolve()
        if site_root_path.is_absolute()
        else (site_path.resolve() / site_root_path).resolve()
    )
    if not resolved.exists():
        raise ValueError(f"Resolved site_root does not exist: {resolved}")

    return SiteScope(
        schema_version=schema_version,
        site_name=site_name,
        site_root=site_root,
        site_base_url=site_base_url,
    )


def write_subspaces_metadata(*, space_root: Path, subspaces: list[dict[str, Any]]) -> Path:
    """Validate and write canonical subspace metadata to `<space_root>/subspaces.json`."""
    payload = {
        "schema_version": SPACE_SUBSPACES_SCHEMA_VERSION,
        "subspaces": subspaces,
    }
    validate_subspaces_metadata_document(payload, space_root=space_root)
    path = space_root / "subspaces.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def load_subspaces_metadata(*, space_root: Path) -> SubspacesMetadata:
    """Load and validate canonical subspace metadata."""
    path = space_root / "subspaces.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing subspace metadata file: {path}")
    document = json.loads(path.read_text())
    return validate_subspaces_metadata_document(document, space_root=space_root)


def validate_subspaces_metadata_document(
    document: dict[str, Any], *, space_root: Path
) -> SubspacesMetadata:
    """Validate duplicate/nesting/root-existence rules for subspaces metadata."""
    if not isinstance(document, dict):
        raise TypeError("subspaces.json document must be a JSON object.")
    schema_version = document.get("schema_version")
    if schema_version != SPACE_SUBSPACES_SCHEMA_VERSION:
        raise ValueError(f"Unsupported subspaces schema_version: {schema_version}")

    subspaces_raw = document.get("subspaces")
    if not isinstance(subspaces_raw, list):
        raise ValueError("subspaces must be an array.")

    seen_names: set[str] = set()
    entries: list[SubspaceEntry] = []
    for idx, row in enumerate(subspaces_raw):
        if not isinstance(row, dict):
            raise ValueError(f"subspaces[{idx}] must be an object.")

        if "subspaces" in row:
            raise ValueError("Nested subspace declarations are not allowed.")

        space_name = row.get("space_name")
        space_root_value = row.get("space_root")
        title = row.get("title")

        _require_non_empty(space_name, f"subspaces[{idx}].space_name")
        _require_non_empty(space_root_value, f"subspaces[{idx}].space_root")
        if not _SPACE_NAME_RE.fullmatch(space_name):
            raise ValueError(f"Invalid subspace name slug: {space_name}")

        if space_name in seen_names:
            raise ValueError(f"Duplicate subspace space_name: {space_name}")
        seen_names.add(space_name)

        if title is not None and (not isinstance(title, str) or not title.strip()):
            raise ValueError(f"subspaces[{idx}].title must be a non-empty string when provided.")

        candidate = Path(space_root_value).expanduser()
        resolved_root = (
            candidate.resolve()
            if candidate.is_absolute()
            else (space_root.resolve() / candidate).resolve()
        )
        if not resolved_root.exists():
            raise ValueError(f"Subspace root does not exist: {resolved_root}")

        entries.append(
            SubspaceEntry(
                space_name=space_name,
                space_root=space_root_value,
                title=title,
                resolved_space_root=resolved_root,
            )
        )

    return SubspacesMetadata(schema_version=schema_version, subspaces=entries)


def _require_non_empty(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
