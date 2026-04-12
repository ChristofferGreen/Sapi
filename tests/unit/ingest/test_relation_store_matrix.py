from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.ingest.relation_store import (
    canonical_relation_id,
    read_relation,
    relation_file_id_from_relation_id,
    write_relation,
)


class RelationStoreMatrixTests(unittest.TestCase):
    def test_relation_id_generation_follows_canonical_relation_type_matrix(self) -> None:
        self.assertEqual(
            canonical_relation_id(
                relation_type="contradictory",
                src_claim_id="claim-b",
                dst_claim_id="claim-a",
            ),
            "contradictory:claim-a|claim-b",
        )
        self.assertEqual(
            canonical_relation_id(
                relation_type="similar",
                src_claim_id="claim-z",
                dst_claim_id="claim-c",
            ),
            "similar:claim-c|claim-z",
        )
        self.assertEqual(
            canonical_relation_id(
                relation_type="supports",
                src_claim_id="claim-src",
                dst_claim_id="claim-dst",
            ),
            "supports:claim-src->claim-dst",
        )
        self.assertEqual(
            canonical_relation_id(
                relation_type="derived_from",
                src_claim_id="claim-src",
                dst_claim_id="claim-dst",
            ),
            "derived_from:claim-src->claim-dst",
        )
        self.assertEqual(
            canonical_relation_id(
                relation_type="falsifies",
                src_claim_id="claim-src",
                dst_claim_id="claim-dst",
            ),
            "falsifies:claim-src->claim-dst",
        )

    def test_undirected_relations_sort_claim_ids_and_directed_relations_preserve_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space-a"

            undirected_path = write_relation(
                {
                    "relation_type": "contradictory",
                    "src_claim_id": "claim-z",
                    "dst_claim_id": "claim-a",
                },
                space_root,
            )
            undirected = json.loads(undirected_path.read_text())
            self.assertEqual(undirected["src_claim_id"], "claim-a")
            self.assertEqual(undirected["dst_claim_id"], "claim-z")
            self.assertEqual(undirected["relation_id"], "contradictory:claim-a|claim-z")

            directed_path = write_relation(
                {
                    "relation_type": "supports",
                    "src_claim_id": "claim-z",
                    "dst_claim_id": "claim-a",
                },
                space_root,
            )
            directed = json.loads(directed_path.read_text())
            self.assertEqual(directed["src_claim_id"], "claim-z")
            self.assertEqual(directed["dst_claim_id"], "claim-a")
            self.assertEqual(directed["relation_id"], "supports:claim-z->claim-a")

    def test_normalization_and_duplicate_merge_are_deterministic_for_same_relation_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "space-a"

            first = write_relation(
                {
                    "relation_type": "contradictory",
                    "src_claim_id": "claim-z",
                    "dst_claim_id": "claim-a",
                    "status": "closed",
                    "below_040_streak": 1,
                    "last_evaluated_run_id": "run-001",
                },
                space_root,
            )
            second = write_relation(
                {
                    "relation_type": "contradictory",
                    "src_claim_id": "claim-a",
                    "dst_claim_id": "claim-z",
                    "status": "open",
                    "below_040_streak": 3,
                    "last_evaluated_run_id": "run-002",
                    "contradiction_confidence_band": "high",
                },
                space_root,
            )

            self.assertEqual(first, second)
            payload = json.loads(second.read_text())
            self.assertEqual(payload["status"], "resolved")
            self.assertEqual(payload["below_040_streak"], 3)
            self.assertEqual(payload["last_evaluated_run_id"], "run-002")
            self.assertEqual(payload["contradiction_confidence_band"], "high")
            self.assertEqual(payload["relation_id"], "contradictory:claim-a|claim-z")
            self.assertEqual(
                payload["relation_file_id"],
                relation_file_id_from_relation_id("contradictory:claim-a|claim-z"),
            )

    def test_read_relation_fails_when_relation_file_id_does_not_match_relation_id_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "relations" / "rel-invalid.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "relation_id": "supports:claim-a->claim-b",
                        "relation_file_id": "rel-deadbeef",
                    }
                )
                + "\n"
            )
            with self.assertRaises(ValueError):
                read_relation(path)


if __name__ == "__main__":
    unittest.main()
