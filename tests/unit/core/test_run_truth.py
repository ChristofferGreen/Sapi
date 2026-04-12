from __future__ import annotations

import unittest

from sapi.core.run_truth import status_advances_reconciliation


class RunTruthStatusTests(unittest.TestCase):
    def test_only_success_statuses_advance_reconciliation(self) -> None:
        self.assertTrue(status_advances_reconciliation("success"))
        self.assertTrue(status_advances_reconciliation("success_with_warnings"))
        self.assertFalse(status_advances_reconciliation("failed"))
        self.assertFalse(status_advances_reconciliation("aborted"))


if __name__ == "__main__":
    unittest.main()
