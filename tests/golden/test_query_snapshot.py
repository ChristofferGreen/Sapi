from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command


GOLDEN_QUERY_SNAPSHOT = (
    Path(__file__).resolve().parent
    / "query_snapshot"
    / "empty_space_strict_query.normalized.json"
)


class QuerySnapshotGoldenTests(unittest.TestCase):
    def test_empty_space_query_payload_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = bootstrap_site_and_space(tmp_root, "alpha")

            query_result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "query.py"),
                    "alpha",
                    "What is available?",
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "--mock-llm",
                ]
            )
            self.assertEqual(query_result.returncode, 0, msg=query_result.stderr)

            query_paths = sorted((site_path / "spaces" / "alpha" / "outputs" / "query").glob("query-*/query.json"))
            self.assertEqual(len(query_paths), 1)
            payload = json.loads(query_paths[0].read_text())
            normalized_payload = _normalize_query_payload(payload)

            expected = json.loads(GOLDEN_QUERY_SNAPSHOT.read_text())
            self.assertEqual(normalized_payload, expected)


def _normalize_query_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = json.loads(json.dumps(payload))
    normalized["query_id"] = "<query_id>"
    normalized["run_id"] = "<run_id>"
    normalized["query_timestamp_utc"] = "<query_timestamp_utc>"
    return normalized


if __name__ == "__main__":
    unittest.main()
