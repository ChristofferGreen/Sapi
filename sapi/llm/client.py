"""LLM client protocol used by the shared semantic executor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class SemanticRepairContext:
    """Repair-loop payload passed to retries after invalid semantic output."""

    previous_invalid_json: str
    validation_errors: list[dict[str, Any]]
    schema: dict[str, Any]
    require_complete_replacement_json: bool = True


@dataclass(frozen=True)
class SemanticLlmRequest:
    """One semantic generation attempt request."""

    flow_key: str
    version: str
    spec_text: str
    schema: dict[str, Any]
    context_by_path: dict[str, str]
    repair_context: SemanticRepairContext | None = None


class LlmClient(Protocol):
    """Boundary for semantic JSON generation backends."""

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        """Return model output text for one strict-JSON semantic generation attempt."""
