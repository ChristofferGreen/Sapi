from __future__ import annotations

import io
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from sapi.lint.guardrails import GuardrailIssue, run_guardrail_checks
from scripts import lint as lint_script


REPO_ROOT = Path(__file__).resolve().parents[3]


class GuardrailChecksTests(unittest.TestCase):
    def test_repo_passes_guardrail_checks(self) -> None:
        issues = run_guardrail_checks(REPO_ROOT)
        self.assertEqual([], issues)

    def test_guardrail_fails_on_implicit_registry_fallback_literal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "scripts/bad_registry.py",
                """
                DEFAULT_REGISTRY = "~/.sapi/spaces.toml"
                """,
            )
            issues = run_guardrail_checks(root)
            self.assertTrue(any(issue.check_id == "registry_fallback" for issue in issues))

    def test_guardrail_fails_on_env_var_flow_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "scripts/bad_env.py",
                """
                import os
                ENABLED = os.environ.get("SAPI_SEMANTIC_FLOW_MODE")
                """,
            )
            issues = run_guardrail_checks(root)
            self.assertTrue(any(issue.check_id == "env_flow_control" for issue in issues))

    def test_guardrail_fails_on_semantic_contract_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "scripts/bad_contract.py",
                """
                SCHEMA_PATH = "schemas/query_synthesis.v1.schema.json"
                """,
            )
            issues = run_guardrail_checks(root)
            self.assertTrue(any(issue.check_id == "semantic_contract_duplication" for issue in issues))

    def test_guardrail_flags_query_canonical_mutation_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "sapi/query/bad_mutation.py",
                """
                from pathlib import Path

                def mutate(space_root: Path) -> None:
                    target = space_root / "sources/records/new.json"
                    target.write_text("{}")
                """,
            )
            issues = run_guardrail_checks(root)
            self.assertTrue(any(issue.check_id == "query_canonical_mutation" for issue in issues))

    def test_validate_entrypoint_reports_guardrail_failures_with_clear_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_root = Path(tmp)
            (site_root / "spaces" / "alpha").mkdir(parents=True)
            registry_path = site_root / "spaces.toml"
            registry_path.write_text(
                textwrap.dedent(
                    """
                    [[spaces]]
                    space_name = "alpha"
                    space_root = "spaces/alpha"
                    """
                ).strip()
                + "\n"
            )

            fake_issue = GuardrailIssue(
                check_id="registry_fallback",
                path=REPO_ROOT / "scripts" / "query.py",
                line=17,
                message="Implicit registry fallback is prohibited; require explicit --registry-path.",
            )
            stderr_capture = io.StringIO()
            with patch("scripts.lint.run_guardrail_checks", return_value=[fake_issue]):
                with patch("sys.stderr", stderr_capture):
                    exit_code = lint_script.run_main(
                        ["alpha", "--registry-path", str(registry_path)]
                    )

            self.assertEqual(1, exit_code)
            stderr_text = stderr_capture.getvalue()
            self.assertIn("Guardrail checks failed:", stderr_text)
            self.assertIn("[registry_fallback]", stderr_text)
            self.assertIn("scripts/query.py:17", stderr_text)

    def _write(self, root: Path, relpath: str, content: str) -> None:
        target = root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(content).strip() + "\n")


if __name__ == "__main__":
    unittest.main()
