"""Runtime guardrails for semantic LLM execution policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


# Environment variables must not control semantic/pipeline flow behavior.
DISALLOWED_FLOW_ENV_VARS: tuple[str, ...] = (
    "SAPI_MOCK_LLM",
    "SAPI_SEMANTIC_FLOW_MODE",
    "SAPI_ENABLE_DETERMINISTIC_SEMANTICS",
    "SAPI_DISABLE_SEMANTIC_LLM",
)


@dataclass(frozen=True)
class SemanticRuntimePolicy:
    """Resolved runtime execution mode for one semantic command invocation."""

    mock_llm: bool
    execution_mode: str


def evaluate_semantic_runtime_policy(
    *,
    mock_llm: bool,
    deterministic_fallback_requested: bool = False,
    env: Mapping[str, str] | None = None,
) -> SemanticRuntimePolicy:
    """Apply non-negotiable runtime guardrails for semantic flow execution."""
    _reject_env_based_flow_controls(env or {})

    if deterministic_fallback_requested:
        raise ValueError(
            "Deterministic semantic fallback is prohibited in operator/production flow execution."
        )

    execution_mode = "mock_llm_test" if mock_llm else "live_llm"
    return SemanticRuntimePolicy(mock_llm=mock_llm, execution_mode=execution_mode)


def _reject_env_based_flow_controls(env: Mapping[str, str]) -> None:
    for key in DISALLOWED_FLOW_ENV_VARS:
        if key in env:
            raise ValueError(
                f"Flow behavior env var `{key}` is prohibited; use explicit CLI flags only."
            )
