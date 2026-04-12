from __future__ import annotations

import os
import unittest

import pytest


@pytest.mark.live_llm
class LiveLlmCanaryTests(unittest.TestCase):
    def test_live_llm_canary_requires_explicit_opt_in(self) -> None:
        if os.environ.get("SAPI_RUN_LIVE_CANARY") != "1":
            self.skipTest("Set SAPI_RUN_LIVE_CANARY=1 to execute live LLM canary checks.")

        # Placeholder assertion for CI wiring: Tier 6 selects only live-llm-marked tests.
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
