"""Shared runtime/control flag surface for semantic entrypoints."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any


DEFAULT_LLM_BACKEND = "codex"
DEFAULT_LLM_MODEL = "gpt-5.4"
DEFAULT_LLM_REASONING_EFFORT = "high"
DEFAULT_LLM_TIMEOUT_SECS = 900
DEFAULT_WARNING_BUDGET = 200

LLM_REASONING_EFFORT_CHOICES: tuple[str, ...] = ("low", "medium", "high", "xhigh")
RUN_SEARCH_VISIBILITY_CHOICES: tuple[str, ...] = ("auto", "on", "off")
SITE_PRESENTATION_MODE_CHOICES: tuple[str, ...] = ("public", "debug")


@dataclass(frozen=True)
class RuntimeFlagSnapshot:
    llm_backend: str
    llm_model: str
    llm_reasoning_effort: str
    llm_timeout_secs: int
    llm_trace: bool
    llm_trace_dir: str | None
    trace_llm_io: bool
    mock_llm: bool
    warning_budget: int
    run_search_visibility: str
    site_presentation_mode: str
    enable_source_index: bool


def add_runtime_flag_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--llm-backend", default=DEFAULT_LLM_BACKEND)
    parser.add_argument("--llm-model", default=DEFAULT_LLM_MODEL)
    parser.add_argument(
        "--llm-reasoning-effort",
        choices=LLM_REASONING_EFFORT_CHOICES,
        default=DEFAULT_LLM_REASONING_EFFORT,
    )
    parser.add_argument("--llm-timeout-secs", type=int, default=DEFAULT_LLM_TIMEOUT_SECS)
    parser.add_argument("--llm-trace", action="store_true")
    parser.add_argument("--llm-trace-dir")
    parser.add_argument("--trace-llm-io", action="store_true")
    parser.add_argument("--mock-llm", action="store_true")
    parser.add_argument("--warning-budget", type=int, default=DEFAULT_WARNING_BUDGET)
    parser.add_argument(
        "--run-search-visibility",
        choices=RUN_SEARCH_VISIBILITY_CHOICES,
        default="auto",
    )
    parser.add_argument(
        "--site-presentation-mode",
        choices=SITE_PRESENTATION_MODE_CHOICES,
        default="public",
    )
    parser.add_argument("--enable-source-index", action="store_true")


def validate_runtime_flag_arguments(args: argparse.Namespace) -> None:
    if args.llm_timeout_secs <= 0:
        raise ValueError("--llm-timeout-secs must be a positive integer.")
    if args.warning_budget <= 0:
        raise ValueError("--warning-budget must be a positive integer.")
    if args.llm_trace_dir and not (args.llm_trace or args.trace_llm_io or args.verbose):
        raise ValueError(
            "--llm-trace-dir requires trace emission; pass --llm-trace, --trace-llm-io, or --verbose."
        )


def snapshot_runtime_flags(args: argparse.Namespace) -> RuntimeFlagSnapshot:
    return RuntimeFlagSnapshot(
        llm_backend=_require_non_empty_string(args.llm_backend, "--llm-backend"),
        llm_model=_require_non_empty_string(args.llm_model, "--llm-model"),
        llm_reasoning_effort=_require_non_empty_string(
            args.llm_reasoning_effort,
            "--llm-reasoning-effort",
        ),
        llm_timeout_secs=int(args.llm_timeout_secs),
        llm_trace=bool(args.llm_trace),
        llm_trace_dir=args.llm_trace_dir,
        trace_llm_io=bool(args.trace_llm_io),
        mock_llm=bool(args.mock_llm),
        warning_budget=int(args.warning_budget),
        run_search_visibility=_require_non_empty_string(
            args.run_search_visibility,
            "--run-search-visibility",
        ),
        site_presentation_mode=_require_non_empty_string(
            args.site_presentation_mode,
            "--site-presentation-mode",
        ),
        enable_source_index=bool(args.enable_source_index),
    )


def runtime_flags_summary_dict(flags: RuntimeFlagSnapshot) -> dict[str, Any]:
    return {
        "llm_backend": flags.llm_backend,
        "llm_model": flags.llm_model,
        "llm_reasoning_effort": flags.llm_reasoning_effort,
        "llm_timeout_secs": flags.llm_timeout_secs,
        "llm_trace": flags.llm_trace,
        "llm_trace_dir": flags.llm_trace_dir,
        "trace_llm_io": flags.trace_llm_io,
        "mock_llm": flags.mock_llm,
        "warning_budget": flags.warning_budget,
        "run_search_visibility": flags.run_search_visibility,
        "site_presentation_mode": flags.site_presentation_mode,
        "enable_source_index": flags.enable_source_index,
    }


def _require_non_empty_string(raw: Any, flag_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{flag_name} must be a non-empty string.")
    return raw.strip()
