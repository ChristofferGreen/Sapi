from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.core.slice_a_gates import (
    deferred_build_backlog_run_ids,
    parse_run_frontmatter,
    validate_ingest_run_frontmatter,
    validate_query_run_frontmatter,
)


class SliceAGatesTests(unittest.TestCase):
    def test_parse_run_frontmatter_decodes_json_values(self) -> None:
        markdown = (
            "---\n"
            'run_id: "run-20260412T120000Z--abc"\n'
            'semantic_flows: ["query_synthesis"]\n'
            "---\n"
            "body\n"
        )
        frontmatter = parse_run_frontmatter(markdown)
        self.assertEqual(frontmatter["run_id"], "run-20260412T120000Z--abc")
        self.assertEqual(frontmatter["semantic_flows"], ["query_synthesis"])

    def test_validate_ingest_run_frontmatter_accepts_contract_shape(self) -> None:
        frontmatter = _base_frontmatter(
            flow_key="ingest_pipeline",
            semantic_flows=["ingest_extraction", "topic_generation"],
            semantic_flow_invocation_counts={"ingest_extraction": 1, "topic_generation": 1},
        )
        frontmatter.update(
            {
                "ingest_scope": "space",
                "source_ids": ["source-a"],
                "claims_changed": 1,
                "relations_changed": 1,
                "topic_pages_changed": 1,
                "build_deferred": False,
                "deferred_build_reason": None,
                "force_mode": False,
                "rollback_skipped": False,
                "restricted_source_mode": False,
                "source_access_policy": _public_source_access_policy(),
            }
        )
        self.assertEqual(validate_ingest_run_frontmatter(frontmatter), [])

    def test_validate_ingest_run_frontmatter_accepts_revision_detection_prefix(self) -> None:
        frontmatter = _base_frontmatter(
            flow_key="ingest_pipeline",
            semantic_flows=["source_revision_detection", "ingest_extraction", "topic_generation"],
            semantic_flow_invocation_counts={
                "source_revision_detection": 1,
                "ingest_extraction": 1,
                "topic_generation": 1,
            },
        )
        frontmatter.update(
            {
                "ingest_scope": "space",
                "source_ids": ["source-a"],
                "claims_changed": 1,
                "relations_changed": 1,
                "topic_pages_changed": 1,
                "build_deferred": False,
                "deferred_build_reason": None,
                "force_mode": False,
                "rollback_skipped": False,
                "restricted_source_mode": False,
                "source_access_policy": _public_source_access_policy(),
            }
        )
        self.assertEqual(validate_ingest_run_frontmatter(frontmatter), [])

    def test_validate_query_run_frontmatter_reports_missing_required_fields(self) -> None:
        frontmatter = _base_frontmatter(
            flow_key="query_pipeline",
            semantic_flows=["query_synthesis"],
            semantic_flow_invocation_counts={"query_synthesis": 1},
        )
        frontmatter["query_id"] = "query-20260412T120000Z-what--abcdefghij"
        errors = validate_query_run_frontmatter(frontmatter)
        self.assertTrue(any("Missing required frontmatter field: mode" in item for item in errors))

    def test_deferred_build_backlog_detects_only_deferred_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            _write_run_markdown(
                space_root=space_root,
                run_id="run-20260412T120000Z--aaaa",
                frontmatter={
                    **_base_frontmatter(
                        flow_key="ingest_pipeline",
                        semantic_flows=["ingest_extraction", "topic_generation"],
                        semantic_flow_invocation_counts={"ingest_extraction": 1, "topic_generation": 1},
                    ),
                    "ingest_scope": "space",
                    "source_ids": ["source-a"],
                    "claims_changed": 1,
                    "relations_changed": 1,
                    "topic_pages_changed": 1,
                    "build_deferred": True,
                    "deferred_build_reason": "operator_requested_build_deferred",
                    "force_mode": False,
                    "rollback_skipped": False,
                    "restricted_source_mode": False,
                    "source_access_policy": _public_source_access_policy(),
                },
            )
            _write_run_markdown(
                space_root=space_root,
                run_id="run-20260412T120100Z--bbbb",
                frontmatter={
                    **_base_frontmatter(
                        flow_key="query_pipeline",
                        semantic_flows=["query_synthesis"],
                        semantic_flow_invocation_counts={"query_synthesis": 1},
                    ),
                    "query_id": "query-20260412T120100Z-what--bbbbbbbbbb",
                    "mode": "strict",
                    "scope": "default",
                    "claims_used": 1,
                    "sources_used": 1,
                    "contradictions_considered": 0,
                    "manifest_path": None,
                    "build_deferred": False,
                },
            )
            self.assertEqual(
                deferred_build_backlog_run_ids(space_root=space_root),
                ["run-20260412T120000Z--aaaa"],
            )


def _base_frontmatter(
    *,
    flow_key: str,
    semantic_flows: list[str],
    semantic_flow_invocation_counts: dict[str, int],
) -> dict[str, object]:
    return {
        "run_id": "run-20260412T120000Z--sample",
        "flow_key": flow_key,
        "semantic_flows": semantic_flows,
        "semantic_flow_invocation_counts": semantic_flow_invocation_counts,
        "status": "success",
        "started_at": "2026-04-12T12:00:00Z",
        "completed_at": "2026-04-12T12:00:05Z",
        "model_fingerprint": "mock_semantic_fixture",
        "provider_fingerprint": "mock",
        "reasoning_effort": "high",
        "execution_mode": "mock_llm_test",
        "llm_attempt_count": 1,
        "toolchain_versions": {"python": "3.12.0"},
        "lint_error_count": 0,
        "lint_warning_count": 0,
        "lint_info_count": 0,
    }


def _public_source_access_policy() -> dict[str, object]:
    return {
        "restricted": False,
        "public_download": True,
        "public_source_view": True,
        "reason": None,
        "landing_url": None,
        "operator_responsibility": None,
    }


def _write_run_markdown(*, space_root: Path, run_id: str, frontmatter: dict[str, object]) -> None:
    run_md_path = space_root / "runs" / run_id / "run.md"
    run_md_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {json.dumps(value, sort_keys=True)}")
    lines.extend(
        [
            "---",
            "",
            "## Summary",
            "(none)",
        ]
    )
    run_md_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    unittest.main()
