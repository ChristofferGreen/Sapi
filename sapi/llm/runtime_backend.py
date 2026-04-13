"""Live semantic JSON backend adapters for OpenAI and Gemini providers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from sapi.llm.client import SemanticLlmRequest


@dataclass(frozen=True)
class SemanticBackendConfig:
    backend: str
    model: str
    reasoning_effort: str
    timeout_secs: int


def generate_semantic_json_live(
    *,
    request: SemanticLlmRequest,
    backend_config: SemanticBackendConfig,
    task_context: dict[str, Any] | None = None,
) -> str:
    """Generate strict semantic JSON in live mode for one semantic-flow request."""
    prompt = _build_prompt(request=request, task_context=task_context)
    backend = backend_config.backend.strip().lower()
    if backend == "openai":
        return _generate_with_openai(
            prompt=prompt,
            backend_config=backend_config,
        )
    if backend == "gemini":
        return _generate_with_gemini(
            prompt=prompt,
            backend_config=backend_config,
        )
    raise RuntimeError(
        "Unsupported --llm-backend value for live semantic generation: "
        f"{backend_config.backend!r}. Supported values: openai, gemini."
    )


def _build_prompt(*, request: SemanticLlmRequest, task_context: dict[str, Any] | None) -> str:
    payload: dict[str, Any] = {
        "flow_key": request.flow_key,
        "version": request.version,
        "schema_path": request.schema_path,
        "output_json_path": request.output_json_path,
        "context_paths": request.context_paths,
        "context_by_path": request.context_by_path,
        "spec_text": request.spec_text,
        "schema": request.schema,
        "task_context": task_context or {},
    }
    if request.repair_context is not None:
        payload["repair_context"] = {
            "previous_invalid_json": request.repair_context.previous_invalid_json,
            "validation_errors": request.repair_context.validation_errors,
            "require_complete_replacement_json": request.repair_context.require_complete_replacement_json,
        }
    instruction_lines = [
        "You are generating one strict JSON object for a semantic pipeline.",
        "Return JSON only. Do not wrap in markdown or code fences.",
        "Follow the provided schema exactly.",
        "Do not invent IDs that conflict with provided canonical IDs.",
        "Use task_context as primary evidence; context_by_path values are filesystem pointers only.",
    ]
    return (
        "\n".join(instruction_lines)
        + "\n\nSemantic request payload:\n"
        + json.dumps(payload, indent=2, sort_keys=True)
    )


def _generate_with_openai(*, prompt: str, backend_config: SemanticBackendConfig) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Missing OPENAI_API_KEY for --llm-backend openai live semantic generation."
        )
    model = backend_config.model.strip() or "gpt-5"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Return only one strict JSON object.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    endpoint = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        raw = _post_json(
            endpoint=endpoint,
            headers=headers,
            payload=payload,
            timeout_secs=backend_config.timeout_secs,
        )
    except RuntimeError as exc:
        # Some model/endpoints may reject response_format json_object; retry once without it.
        if "response_format" not in str(exc):
            raise
        payload_without_response_format = dict(payload)
        payload_without_response_format.pop("response_format", None)
        raw = _post_json(
            endpoint=endpoint,
            headers=headers,
            payload=payload_without_response_format,
            timeout_secs=backend_config.timeout_secs,
        )
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("OpenAI response missing `choices` array.")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("OpenAI response choice must be an object.")
    message = first.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("OpenAI response missing `message` object.")
    content = message.get("content")
    rendered = _normalize_openai_content(content)
    if not rendered:
        raise RuntimeError("OpenAI response did not include text content.")
    return rendered


def _normalize_openai_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                chunks.append(text)
        return "\n".join(chunks).strip()
    return ""


def _generate_with_gemini(*, prompt: str, backend_config: SemanticBackendConfig) -> str:
    api_key = _resolve_gemini_api_key()
    requested_model = backend_config.model.strip()
    model = "gemini-2.5-pro" if requested_model in {"", "gpt-5"} else requested_model
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{quote_plus(model)}:generateContent?key={quote_plus(api_key)}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2,
        },
    }
    raw = _post_json(
        endpoint=endpoint,
        headers={"Content-Type": "application/json"},
        payload=payload,
        timeout_secs=backend_config.timeout_secs,
    )
    candidates = raw.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise RuntimeError("Gemini response missing `candidates` array.")
    first = candidates[0]
    if not isinstance(first, dict):
        raise RuntimeError("Gemini candidate must be an object.")
    content = first.get("content")
    if not isinstance(content, dict):
        raise RuntimeError("Gemini candidate missing `content` object.")
    parts = content.get("parts")
    if not isinstance(parts, list):
        raise RuntimeError("Gemini content missing `parts` array.")
    chunks: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        text = part.get("text")
        if isinstance(text, str):
            chunks.append(text)
    rendered = "\n".join(chunks).strip()
    if not rendered:
        raise RuntimeError("Gemini response did not include text content.")
    return rendered


def _resolve_gemini_api_key() -> str:
    primary = os.environ.get("GEMINI_API_KEY", "").strip()
    if primary:
        return primary
    fallback = os.environ.get("GOOGLE_API_KEY", "").strip()
    if fallback:
        return fallback
    raise RuntimeError(
        "Missing GEMINI_API_KEY/GOOGLE_API_KEY for --llm-backend gemini live semantic generation."
    )


def _post_json(
    *,
    endpoint: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_secs: int,
) -> dict[str, Any]:
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_secs) as response:
            raw_body = response.read().decode("utf-8")
    except HTTPError as exc:  # pragma: no cover - network/provider dependent
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"LLM backend HTTP {exc.code}: {body}"
        ) from exc
    except URLError as exc:  # pragma: no cover - network/provider dependent
        raise RuntimeError(f"LLM backend request failed: {exc.reason}") from exc

    try:
        decoded = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM backend returned non-JSON response: {exc}") from exc
    if not isinstance(decoded, dict):
        raise RuntimeError("LLM backend response must decode to a JSON object.")
    return decoded
