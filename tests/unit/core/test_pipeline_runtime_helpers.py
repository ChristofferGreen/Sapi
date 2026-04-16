from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.core.pipeline_runtime import (
    add_llm_attempts,
    record_semantic_invocation,
    write_json_with_transaction,
)
from sapi.core.transactions import ArtifactTransaction


class PipelineRuntimeHelperTests(unittest.TestCase):
    def test_record_semantic_invocation_is_ordered_unique_with_counting(self) -> None:
        semantic_flows: list[str] = []
        counts: dict[str, int] = {}
        record_semantic_invocation(
            flow_key="query_synthesis",
            semantic_flows=semantic_flows,
            semantic_flow_invocation_counts=counts,
        )
        record_semantic_invocation(
            flow_key="query_synthesis",
            semantic_flows=semantic_flows,
            semantic_flow_invocation_counts=counts,
        )
        self.assertEqual(semantic_flows, ["query_synthesis"])
        self.assertEqual(counts, {"query_synthesis": 2})

    def test_add_llm_attempts_requires_positive_attempt_increment(self) -> None:
        self.assertEqual(add_llm_attempts(llm_attempt_count=1, attempt_count=2), 3)
        with self.assertRaises(ValueError):
            add_llm_attempts(llm_attempt_count=1, attempt_count=0)

    def test_write_json_with_transaction_replaces_existing_file_and_tracks_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "record.json"
            target.write_text(json.dumps({"before": True}) + "\n")
            tx = ArtifactTransaction()
            write_json_with_transaction(target, {"after": True}, transaction=tx)
            payload = json.loads(target.read_text())
            self.assertEqual(payload, {"after": True})
            tx.rollback()
            restored = json.loads(target.read_text())
            self.assertEqual(restored, {"before": True})


if __name__ == "__main__":
    unittest.main()
