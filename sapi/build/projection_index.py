"""Projection index writer for deterministic build outputs."""

from __future__ import annotations

import json
from pathlib import Path


def projection_index_path(*, space_root: Path) -> Path:
    return space_root / "outputs" / "projection_index" / "index.json"


def build_projection_index_payload(
    *,
    space_root: Path,
    generated_files: list[Path],
) -> dict[str, object]:
    relpaths = sorted(
        str(path.relative_to(space_root))
        for path in generated_files
        if path.is_file() and _is_within(path=path, root=space_root)
    )
    return {
        "schema_version": "projection_index_v1",
        "space_name": space_root.name,
        "generated_files": relpaths,
    }


def write_projection_index(
    *,
    space_root: Path,
    generated_files: list[Path],
) -> Path:
    target = projection_index_path(space_root=space_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_projection_index_payload(
        space_root=space_root,
        generated_files=generated_files,
    )
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return target


def _is_within(*, path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
