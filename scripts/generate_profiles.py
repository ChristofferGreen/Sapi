#!/usr/bin/env python3
"""Persona-profile generation pipeline entrypoint (TODO-0224 scope)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.contracts.ids import format_timestamp_rfc3339_utc, make_run_id
from sapi.contracts.run_envelopes import PersonaProfileRunFields, RunEnvelopeBase
from sapi.core.pipeline_policy import finalize_pipeline_run
from sapi.core.pipeline_runtime import (
    add_llm_attempts,
    build_run_envelope_base,
    record_semantic_invocation,
    track_path_for_write,
    write_json_with_transaction,
)
from sapi.core.registry import resolve_registry_path, resolve_space_root
from sapi.core.runtime_flags import (
    RuntimeFlagSnapshot,
    add_runtime_flag_arguments,
    runtime_flags_summary_dict,
    snapshot_runtime_flags,
    validate_runtime_flag_arguments,
)
from sapi.core.runtime_policy import evaluate_semantic_runtime_policy
from sapi.core.transactions import ArtifactTransaction
from sapi.llm.client import SemanticLlmRequest
from sapi.llm.runtime_backend import (
    SemanticBackendConfig,
    generate_semantic_json_live,
)
from sapi.llm.semantic_executor import build_semantic_spec_from_contract, run_semantic_flow
from sapi.profiles.history import (
    apply_persona_history_update,
    compute_persona_history_metrics,
    history_path_for_persona,
    read_history_payload,
)
from sapi.profiles.persona_catalog import load_seeded_persona_catalog
from sapi.profiles.profiles_pipeline import (
    select_personas_for_profile_generation,
    validate_profile_semantic_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("space_name")
    parser.add_argument("--registry-path", required=True)
    parser.add_argument("--persona-id", action="append", default=[])
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--simulate-terminal-failure", action="store_true", help=argparse.SUPPRESS)
    add_runtime_flag_arguments(parser)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    run_id = make_run_id()
    transaction = ArtifactTransaction()
    toolchain_versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    persona_ids: list[str] = []
    semantic_flows: list[str] = []
    semantic_flow_invocation_counts: dict[str, int] = {}
    llm_attempt_count = 0
    profile_generated_count = 0
    profile_updated_count = 0
    profile_reused_count = 0
    pages_changed = 0
    history_generated_count = 0
    history_updated_count = 0
    history_reused_count = 0

    try:
        validate_runtime_flag_arguments(args)
        runtime_flags = snapshot_runtime_flags(args)
        runtime_policy = evaluate_semantic_runtime_policy(
            mock_llm=runtime_flags.mock_llm,
            env=os.environ,
        )
        registry_path = resolve_registry_path(args.registry_path)
        space_root = resolve_space_root(registry_path, args.space_name)
        persona_catalog = load_seeded_persona_catalog(repo_root=_REPO_ROOT)
        selected_personas = select_personas_for_profile_generation(
            persona_catalog=persona_catalog,
            requested_persona_ids=args.persona_id,
        )
        persona_ids = [selected.persona_id for selected in selected_personas]
    except (FileNotFoundError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        for selected in selected_personas:
            persona_id = selected.persona_id
            record_semantic_invocation(
                flow_key="persona_profile_generation",
                semantic_flows=semantic_flows,
                semantic_flow_invocation_counts=semantic_flow_invocation_counts,
            )
            semantic_spec = build_semantic_spec_from_contract(
                "persona_profile_generation",
                repo_root=_REPO_ROOT,
                path_tokens={
                    "space_root": space_root,
                    "persona_id": persona_id,
                },
            )
            previous_profile_payload = _read_json_dict_if_exists(semantic_spec.output_json_path)
            track_path_for_write(semantic_spec.output_json_path, transaction=transaction)
            profile_llm_client = _build_profile_client(
                runtime_flags=runtime_flags,
                persona_row=selected.row,
                space_name=args.space_name,
            )
            semantic_payload, attempt_count = run_semantic_flow(
                spec=semantic_spec,
                llm_client=profile_llm_client,
            )
            llm_attempt_count = add_llm_attempts(
                llm_attempt_count=llm_attempt_count,
                attempt_count=attempt_count,
            )
            validate_profile_semantic_payload(
                payload=semantic_payload,
                expected_persona_id=persona_id,
                expected_space_name=args.space_name,
            )

            if previous_profile_payload is None:
                profile_generated_count += 1
                pages_changed += 1
            elif previous_profile_payload != semantic_payload:
                profile_updated_count += 1
                pages_changed += 1
            else:
                profile_reused_count += 1

            history_path = history_path_for_persona(space_root=space_root, persona_id=persona_id)
            current_history_payload = read_history_payload(history_path)
            metrics = compute_persona_history_metrics(space_root=space_root, persona_id=persona_id)
            history_update = apply_persona_history_update(
                current_payload=current_history_payload,
                space_name=args.space_name,
                persona_id=persona_id,
                metrics=metrics,
                as_of_date=datetime.now(UTC).date().isoformat(),
            )
            if history_update.status == "generated":
                history_generated_count += 1
                write_json_with_transaction(
                    history_path,
                    history_update.payload,
                    transaction=transaction,
                )
            elif history_update.status == "updated":
                history_updated_count += 1
                write_json_with_transaction(
                    history_path,
                    history_update.payload,
                    transaction=transaction,
                )
            else:
                history_reused_count += 1

        if args.simulate_terminal_failure:
            raise RuntimeError("Simulated terminal profile failure.")
    except Exception as exc:
        completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
        base = _make_run_base(
            run_id=run_id,
            status="failed",
            started_at=started_at,
            completed_at=completed_at,
            execution_mode=runtime_policy.execution_mode,
            llm_backend=runtime_flags.llm_backend,
            llm_model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            semantic_flows=semantic_flows,
            semantic_flow_invocation_counts=semantic_flow_invocation_counts,
            llm_attempt_count=llm_attempt_count,
            toolchain_versions=toolchain_versions,
        )
        flow_fields = PersonaProfileRunFields(
            persona_ids=persona_ids,
            history_generated=history_generated_count,
            history_updated=history_updated_count,
            history_reused=history_reused_count,
            pages_changed=pages_changed,
        )
        finalized = finalize_pipeline_run(
            space_root=space_root,
            base=base,
            flow_fields=flow_fields,
            transaction=transaction,
            force_mode=False,
            summary="Persona profile generation failed; invocation-scoped outputs rolled back.",
            errors=str(exc),
        )
        print(
            "scripts/generate_profiles.py profiles failed "
            f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
            f"status={finalized.status}, runtime_flags={runtime_flags_summary_dict(runtime_flags)}, "
            f"error={exc})",
            file=sys.stderr,
        )
        return finalized.exit_code

    projection_stats = {
        "persona_profiles": {
            "generated": profile_generated_count,
            "updated": profile_updated_count,
            "reused": profile_reused_count,
            "pages": pages_changed,
            "topic_ids": [],
        },
        "accountability": {
            "personas": len(persona_ids),
            "history_generated": history_generated_count,
            "history_updated": history_updated_count,
            "history_reused": history_reused_count,
        },
    }

    completed_at = format_timestamp_rfc3339_utc(datetime.now(UTC))
    base = _make_run_base(
        run_id=run_id,
        status="success",
        started_at=started_at,
        completed_at=completed_at,
        execution_mode=runtime_policy.execution_mode,
        llm_backend=runtime_flags.llm_backend,
        llm_model=runtime_flags.llm_model,
        reasoning_effort=runtime_flags.llm_reasoning_effort,
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )
    flow_fields = PersonaProfileRunFields(
        persona_ids=persona_ids,
        history_generated=history_generated_count,
        history_updated=history_updated_count,
        history_reused=history_reused_count,
        pages_changed=pages_changed,
    )
    finalized = finalize_pipeline_run(
        space_root=space_root,
        base=base,
        flow_fields=flow_fields,
        transaction=transaction,
        force_mode=False,
        summary="Persona profile generation completed successfully.",
        changes=(
            f"persona_ids={len(persona_ids)}, pages_changed={pages_changed}, "
            f"history_generated={history_generated_count}, history_updated={history_updated_count}, "
            f"history_reused={history_reused_count}"
        ),
        lint_summary="lint_error_count=0 lint_warning_count=0 lint_info_count=0",
        errors="",
    )
    print(
        "scripts/generate_profiles.py profiles complete "
        f"(execution_mode={runtime_policy.execution_mode}, run_id={run_id}, "
        f"persona_ids={persona_ids}, projection_stats={projection_stats}, "
        f"run_record_path={finalized.run_record_path}, "
        f"runtime_flags={runtime_flags_summary_dict(runtime_flags)})"
    )
    return finalized.exit_code


def _read_json_dict_if_exists(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    parsed = json.loads(path.read_text())
    if not isinstance(parsed, dict):
        return None
    return parsed


def _make_run_base(
    *,
    run_id: str,
    status: str,
    started_at: str,
    completed_at: str,
    execution_mode: str,
    llm_backend: str,
    llm_model: str,
    reasoning_effort: str,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
    llm_attempt_count: int,
    toolchain_versions: dict[str, str],
) -> RunEnvelopeBase:
    return build_run_envelope_base(
        run_id=run_id,
        flow_key="persona_profile_pipeline",
        semantic_flows=semantic_flows,
        semantic_flow_invocation_counts=semantic_flow_invocation_counts,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        execution_mode=execution_mode,
        llm_backend=llm_backend,
        llm_model=llm_model,
        reasoning_effort=reasoning_effort,
        llm_attempt_count=llm_attempt_count,
        toolchain_versions=toolchain_versions,
    )


def _build_profile_client(
    *,
    runtime_flags: RuntimeFlagSnapshot,
    persona_row: dict[str, object],
    space_name: str,
):
    if runtime_flags.mock_llm:
        return _MockPersonaProfileClient(
            persona_row=persona_row,
            space_name=space_name,
        )
    return _LivePersonaProfileClient(
        backend_config=SemanticBackendConfig(
            backend=runtime_flags.llm_backend,
            model=runtime_flags.llm_model,
            reasoning_effort=runtime_flags.llm_reasoning_effort,
            timeout_secs=runtime_flags.llm_timeout_secs,
        ),
        persona_row=persona_row,
        space_name=space_name,
    )


class _MockPersonaProfileClient:
    def __init__(
        self,
        *,
        persona_row: dict[str, object],
        space_name: str,
    ) -> None:
        self._persona_row = persona_row
        self._space_name = space_name

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        persona_id = str(self._persona_row["persona_id"])
        profile_image_path = self._persona_row.get("profile_image_path")
        display_name = str(self._persona_row.get("display_name") or persona_id)
        argument_style = "direct"
        prompt_fields = self._persona_row.get("prompt_fields")
        if isinstance(prompt_fields, dict):
            argument_style = str(prompt_fields.get("argument_style") or argument_style)
        interests = self._persona_row.get("interests")
        if isinstance(interests, list):
            interests_lines = [f"- {str(item)}" for item in interests[:3] if str(item).strip()]
        else:
            interests_lines = []
        biography_profile = str(self._persona_row.get("biography_profile") or "").strip()
        short_cv = self._persona_row.get("short_cv")
        if isinstance(short_cv, list):
            short_cv_lines = [f"- {str(item)}" for item in short_cv if str(item).strip()]
        else:
            short_cv_lines = []
        profile_sections = [
            {
                "title": "Identity",
                "content": f"{display_name} participates in space `{self._space_name}` as `{persona_id}`.",
            },
            {
                "title": "Profile biography",
                "content": biography_profile or "(not provided)",
            },
            {
                "title": "Debate style",
                "content": f"Primary argument style: {argument_style}.",
            },
            {
                "title": "Interests",
                "content": "\n".join(interests_lines) if interests_lines else "- (none listed)",
            },
            {
                "title": "Short CV",
                "content": "\n".join(short_cv_lines) if short_cv_lines else "- (none listed)",
            },
        ]
        payload = {
            "persona_id": persona_id,
            "space_name": self._space_name,
            "profile_sections": profile_sections,
            "profile_image_path": profile_image_path,
            "accountability_summary": (
                "Accountability metrics are maintained in space-local persona profile history."
            ),
        }
        return json.dumps(payload)


class _LivePersonaProfileClient:
    def __init__(
        self,
        *,
        backend_config: SemanticBackendConfig,
        persona_row: dict[str, object],
        space_name: str,
    ) -> None:
        self._backend_config = backend_config
        self._persona_row = persona_row
        self._space_name = space_name

    def generate_semantic_json(self, request: SemanticLlmRequest) -> str:
        return generate_semantic_json_live(
            request=request,
            backend_config=self._backend_config,
            task_context={
                "task_requirements": {
                    "persona_id": str(self._persona_row.get("persona_id")),
                    "space_name": self._space_name,
                    "section_expectations": [
                        "Identity",
                        "Profile biography",
                        "Debate style",
                        "Interests",
                        "Short CV",
                    ],
                    "biography_voice": "first_person",
                },
                "persona_row": self._persona_row,
            },
        )


if __name__ == "__main__":
    raise SystemExit(main())
