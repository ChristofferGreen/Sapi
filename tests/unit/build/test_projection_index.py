from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.build.projection_index import (
    projection_index_path,
    write_projection_index,
)


class ProjectionIndexTests(unittest.TestCase):
    def test_write_projection_index_writes_canonical_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "site-a" / "spaces" / "alpha"
            site_dir = space_root / "site"
            site_dir.mkdir(parents=True, exist_ok=True)
            topic_page = site_dir / "topics" / "topic-alpha.html"
            topic_page.parent.mkdir(parents=True, exist_ok=True)
            topic_page.write_text("<html></html>\n")

            index_path = write_projection_index(
                space_root=space_root,
                generated_files=[topic_page],
            )
            self.assertEqual(index_path, projection_index_path(space_root=space_root))
            payload = json.loads(index_path.read_text())
            self.assertEqual(payload["schema_version"], "projection_index_v1")
            self.assertEqual(payload["space_name"], "alpha")
            self.assertEqual(payload["generated_files"], ["site/topics/topic-alpha.html"])


if __name__ == "__main__":
    unittest.main()
