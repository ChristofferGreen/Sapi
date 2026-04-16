from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.core.fs_store import FsStoreError, list_json_paths, read_json_object


class FsStoreTests(unittest.TestCase):
    def test_list_json_paths_returns_sorted_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.json").write_text("{}\n")
            (root / "a.json").write_text("{}\n")
            (root / "skip.txt").write_text("nope\n")
            paths = list_json_paths(root)
            self.assertEqual([path.name for path in paths], ["a.json", "b.json"])

    def test_read_json_object_requires_object_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "record.json"
            path.write_text(json.dumps({"ok": True}) + "\n")
            self.assertEqual(read_json_object(path), {"ok": True})

            path.write_text(json.dumps(["not-an-object"]) + "\n")
            with self.assertRaises(FsStoreError):
                read_json_object(path)


if __name__ == "__main__":
    unittest.main()
