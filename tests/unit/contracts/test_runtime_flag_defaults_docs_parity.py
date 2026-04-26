from __future__ import annotations

import re
import unittest
from pathlib import Path

from sapi.core import runtime_config
from sapi.core import runtime_flags


REPO_ROOT = Path(__file__).resolve().parents[3]


class RuntimeFlagDefaultsDocsParityTests(unittest.TestCase):
    def test_readme_default_values_match_runtime_defaults(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text()
        self.assertEqual(
            _extract_flag_value(readme_text, "--llm-backend"),
            runtime_flags.DEFAULT_LLM_BACKEND,
        )
        self.assertIn(
            "- `--llm-model` from `config/llm.json` (`default_live_model`)",
            readme_text,
        )
        self.assertEqual(runtime_flags.DEFAULT_LLM_MODEL, runtime_config.DEFAULT_LIVE_LLM_MODEL)
        self.assertEqual(
            _extract_flag_value(readme_text, "--llm-reasoning-effort"),
            runtime_flags.DEFAULT_LLM_REASONING_EFFORT,
        )
        self.assertEqual(
            _extract_optional_timeout_value(readme_text, "--llm-timeout-secs"),
            runtime_flags.DEFAULT_LLM_TIMEOUT_SECS,
        )
        self.assertEqual(
            int(_extract_flag_value(readme_text, "--warning-budget")),
            runtime_flags.DEFAULT_WARNING_BUDGET,
        )


def _extract_flag_value(readme_text: str, flag_name: str) -> str:
    pattern = re.compile(rf"-\s+`{re.escape(flag_name)}\s+([^`]+)`")
    match = pattern.search(readme_text)
    if match is None:
        raise AssertionError(f"README defaults section missing {flag_name} entry.")
    return match.group(1).strip()


def _extract_optional_timeout_value(readme_text: str, flag_name: str) -> int | None:
    raw_value = _extract_flag_value(readme_text, flag_name).lower()
    if raw_value == "none":
        return None
    return int(raw_value)


if __name__ == "__main__":
    unittest.main()
