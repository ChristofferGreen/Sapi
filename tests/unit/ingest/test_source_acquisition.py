from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Iterator

from sapi.ingest.records_writer import ingest_source_artifacts_and_record


class SourceAcquisitionContractTests(unittest.TestCase):
    def test_file_ingest_persists_artifacts_under_source_id_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            input_file = Path(tmp) / "paper.txt"
            input_file.write_text("hello from a local source\n")

            result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(input_file),
                source_title_override="Local Paper",
            )

            expected_artifact_root = space_root / "sources" / "artifacts" / result.source_id
            self.assertEqual(result.artifact_root, expected_artifact_root)
            self.assertTrue(result.source_artifact_path.is_file())
            self.assertTrue(result.overview_markdown_path.is_file())
            self.assertTrue(str(result.source_artifact_path).startswith(str(expected_artifact_root)))

    def test_source_record_persists_canonical_metadata_and_relative_artifact_pointers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            input_file = Path(tmp) / "report.md"
            input_file.write_text("# Heading\n\nBody.\n")

            result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(input_file),
                source_title_override="Contract Report",
                source_family_id="family-paper",
                canonical_identifier="doi:10.1000/example",
            )
            record = json.loads(result.record_path.read_text())

            self.assertEqual(record["source_id"], result.source_id)
            self.assertEqual(record["title"], "Contract Report")
            self.assertEqual(record["artifact_root"], f"sources/artifacts/{result.source_id}")
            self.assertEqual(
                record["artifacts"]["source_file"],
                f"sources/artifacts/{result.source_id}/{result.source_artifact_path.name}",
            )
            self.assertEqual(
                record["artifacts"]["overview_markdown"],
                f"sources/artifacts/{result.source_id}/overview.md",
            )
            self.assertIsNone(record["artifacts"]["front_page_image"])
            self.assertEqual(record["source_family_id"], "family-paper")
            self.assertEqual(record["canonical_identifier"], "doi:10.1000/example")
            self.assertFalse(Path(record["artifact_root"]).is_absolute())
            self.assertFalse(Path(record["artifacts"]["source_file"]).is_absolute())

    def test_url_ingest_is_supported_and_persists_artifacts_and_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            with _served_source_bytes(body=b"%PDF-test-content%", content_type="application/pdf") as source_url:
                result = ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=source_url,
                    source_title_override="Remote Source",
                )

            record = json.loads(result.record_path.read_text())
            self.assertEqual(record["source_kind"], "url")
            self.assertEqual(record["source_type"], "url")
            self.assertEqual(record["source_media_type"], "application/pdf")
            self.assertEqual(result.source_artifact_path.name, "source.pdf")
            self.assertTrue(result.source_artifact_path.is_file())


@contextmanager
def _served_source_bytes(*, body: bytes, content_type: str) -> Iterator[str]:
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}/source"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    unittest.main()
