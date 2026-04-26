"""Repo-owned runtime configuration readers."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any


LLM_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "llm.json"


@lru_cache(maxsize=1)
def load_llm_runtime_config() -> dict[str, Any]:
    payload = json.loads(LLM_CONFIG_PATH.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"LLM runtime config must be a JSON object: {LLM_CONFIG_PATH}")
    default_live_model = payload.get("default_live_model")
    if not isinstance(default_live_model, str) or not default_live_model.strip():
        raise ValueError(f"LLM runtime config requires non-empty default_live_model: {LLM_CONFIG_PATH}")
    return {"default_live_model": default_live_model.strip()}


DEFAULT_LIVE_LLM_MODEL = str(load_llm_runtime_config()["default_live_model"])
