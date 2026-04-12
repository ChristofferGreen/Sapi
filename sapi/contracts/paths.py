"""Canonical path-token and alias resolution helpers for Section 5.0."""

from __future__ import annotations

from pathlib import Path


def resolve_contract_path(
    path_ref: str | Path,
    *,
    repo_root: Path,
    site_path: Path,
    space_root: Path,
) -> Path:
    """Resolve contract path refs to absolute filesystem paths."""
    raw = str(path_ref).strip()
    if not raw:
        raise ValueError("Path reference cannot be empty.")
    if raw.startswith("sites/"):
        raise ValueError("Prohibited root alias: sites/<site_name>/...")

    repo_root_abs = repo_root.resolve()
    site_path_abs = site_path.resolve()
    space_root_abs = space_root.resolve()

    token_map = {
        "<repo_root>": repo_root_abs,
        "<site_path>": site_path_abs,
        "<space_root>": space_root_abs,
    }
    for token, base in token_map.items():
        token_prefix = f"{token}/"
        if raw == token:
            return base
        if raw.startswith(token_prefix):
            return (base / raw[len(token_prefix) :]).resolve()

    if raw.startswith("site/"):
        return (space_root_abs / raw).resolve()
    if raw.startswith("outputs/"):
        return (space_root_abs / raw).resolve()
    if raw.startswith("raw/"):
        return (space_root_abs / raw).resolve()
    if raw.startswith("personas/"):
        return (repo_root_abs / raw).resolve()

    as_path = Path(raw).expanduser()
    if as_path.is_absolute():
        return as_path.resolve()

    raise ValueError(
        "Relative path must use a canonical token or alias (site/, outputs/, raw/, personas/)."
    )


def resolve_space_root_from_registry_value(registry_path: Path, space_root_value: str) -> Path:
    """Resolve registry `space_root` value using Section 5.0 registry rule."""
    candidate = Path(space_root_value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (registry_path.resolve().parent / candidate).resolve()
