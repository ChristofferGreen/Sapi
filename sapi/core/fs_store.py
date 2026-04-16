"""Canonical filesystem JSON helpers shared by projection/build paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FsStoreError(ValueError):
    """Raised when canonical JSON artifacts cannot be read safely."""


def list_json_paths(root: Path, *, pattern: str = "*.json") -> list[Path]:
    if not root.exists():
        return []
    if not root.is_dir():
        raise FsStoreError(f"Expected directory path for JSON listing: {root}")
    return sorted(path for path in root.glob(pattern) if path.is_file())


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FsStoreError(f"Expected JSON file path: {path}")
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise FsStoreError(f"{path}: invalid JSON ({exc}).") from exc
    if not isinstance(payload, dict):
        raise FsStoreError(f"{path}: payload must be a JSON object.")
    return payload
