"""Registry loading and path-resolution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib

from sapi.contracts.paths import resolve_space_root_from_registry_value


@dataclass(frozen=True)
class RegistrySpace:
    """Normalized registry entry for one space."""

    space_name: str
    space_root: str


def resolve_registry_path(arg_registry_path: str | None) -> Path:
    """Resolve and validate the explicit registry path argument."""
    if arg_registry_path is None or not arg_registry_path.strip():
        raise ValueError("Missing required --registry-path for non-bootstrap command.")

    registry_path = Path(arg_registry_path).expanduser()
    if not registry_path.is_absolute():
        registry_path = (Path.cwd() / registry_path).resolve()
    else:
        registry_path = registry_path.resolve()

    if not registry_path.is_file():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")
    return registry_path


def load_registry(registry_path: Path) -> dict[str, Any]:
    """Load registry content and enforce a unique normalized space index."""
    normalized_registry_path = resolve_registry_path(str(registry_path))
    data = tomllib.loads(normalized_registry_path.read_text())
    spaces_raw = data.get("spaces")
    if not isinstance(spaces_raw, list):
        raise ValueError("Registry must contain a [[spaces]] list.")

    spaces: list[RegistrySpace] = []
    seen_names: set[str] = set()
    for idx, entry in enumerate(spaces_raw):
        if not isinstance(entry, dict):
            raise ValueError(f"Registry spaces[{idx}] must be a table.")

        # Accept historical key `name` as compatibility input.
        space_name = entry.get("space_name", entry.get("name"))
        space_root = entry.get("space_root")

        if not isinstance(space_name, str) or not space_name.strip():
            raise ValueError(f"Registry spaces[{idx}] is missing non-empty space_name.")
        if not isinstance(space_root, str) or not space_root.strip():
            raise ValueError(f"Registry spaces[{idx}] is missing non-empty space_root.")
        if space_name in seen_names:
            raise ValueError(f"Duplicate space_name in registry: {space_name}")
        seen_names.add(space_name)
        spaces.append(RegistrySpace(space_name=space_name, space_root=space_root))

    return {
        "registry_path": normalized_registry_path,
        "spaces": spaces,
        "space_index": {space.space_name: space for space in spaces},
    }


def resolve_space_root(registry_path: Path, space_name: str) -> Path:
    """Resolve one space root to an absolute path."""
    registry = load_registry(registry_path)
    if space_name not in registry["space_index"]:
        raise KeyError(f"Unknown space_name in registry: {space_name}")

    entry: RegistrySpace = registry["space_index"][space_name]
    return resolve_space_root_from_registry_value(registry["registry_path"], entry.space_root)


def resolve_site_path_from_registry(registry_path: Path) -> Path:
    """Resolve canonical site path from registry location."""
    normalized_registry_path = resolve_registry_path(str(registry_path))
    return normalized_registry_path.parent.resolve()
