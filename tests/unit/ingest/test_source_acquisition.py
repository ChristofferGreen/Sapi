from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path
from typing import Iterator

from sapi.ingest import records_writer
from sapi.ingest.records_writer import ingest_source_artifacts_and_record


class SourceAcquisitionContractTests(unittest.TestCase):
    def test_source_title_resolution_follows_five_step_priority_contract_in_ingest_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            space_root = tmp_root / "spaces" / "alpha"

            html_source = tmp_root / "metadata-title.html"
            html_source.write_text(
                "<html><head><title>Metadata Title</title></head><body># In Source</body></html>\n"
            )
            markdown_source = tmp_root / "in-source-title.md"
            markdown_source.write_text("# In-Source Title\n\nBody text.\n")
            fallback_source = tmp_root / "fallback-title.pdf"
            fallback_source.write_bytes(b"%PDF-1.7\n%fallback\n")

            override_result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(html_source),
                source_title_override="Override Title",
            )
            override_record = json.loads(override_result.record_path.read_text())
            self.assertEqual(override_record["title"], "Override Title")

            metadata_result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(html_source),
                source_title_override=None,
            )
            metadata_record = json.loads(metadata_result.record_path.read_text())
            self.assertEqual(metadata_record["title"], "Metadata Title")

            in_source_result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(markdown_source),
                source_title_override=None,
            )
            in_source_record = json.loads(in_source_result.record_path.read_text())
            self.assertEqual(in_source_record["title"], "In-Source Title")

            fallback_result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(fallback_source),
                source_title_override=None,
            )
            fallback_record = json.loads(fallback_result.record_path.read_text())
            self.assertEqual(fallback_record["title"], "fallback-title")

            with _served_source_bytes(
                body=b"%PDF-1.7\n%untitled\n",
                content_type="application/pdf",
                route_path="/",
            ) as source_url:
                untitled_result = ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=source_url,
                    source_title_override=None,
                )
            untitled_record = json.loads(untitled_result.record_path.read_text())
            self.assertEqual(untitled_record["title"], "Untitled Source")

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

    def test_pdf_ingest_persists_front_page_image_when_renderer_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            input_file = Path(tmp) / "paper.pdf"
            input_file.write_bytes(b"%PDF-1.4\n%fake\n")

            def _fake_front_page_renderer(*, source_artifact_path: Path) -> Path:
                output_path = source_artifact_path.parent / "front_page.png"
                output_path.write_bytes(b"png-bytes")
                return output_path

            with patch(
                "sapi.ingest.records_writer._render_pdf_front_page_image",
                side_effect=_fake_front_page_renderer,
            ):
                result = ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=str(input_file),
                    source_title_override="PDF Source",
                )

            self.assertIsNotNone(result.front_page_image_path)
            assert result.front_page_image_path is not None
            self.assertTrue(result.front_page_image_path.is_file())
            self.assertEqual(result.front_page_image_path.read_bytes(), b"png-bytes")

            record = json.loads(result.record_path.read_text())
            self.assertEqual(
                record["artifacts"]["front_page_image"],
                f"sources/artifacts/{result.source_id}/front_page.png",
            )

    def test_pdf_ingest_keeps_front_page_image_null_when_renderer_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            input_file = Path(tmp) / "paper.pdf"
            input_file.write_bytes(b"%PDF-1.4\n%fake\n")

            with patch(
                "sapi.ingest.records_writer._render_pdf_front_page_image",
                return_value=None,
            ):
                result = ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=str(input_file),
                    source_title_override="PDF Source",
                )

            self.assertIsNone(result.front_page_image_path)
            record = json.loads(result.record_path.read_text())
            self.assertIsNone(record["artifacts"]["front_page_image"])

    def test_pdf_front_page_renderer_uses_scaled_default_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_pdf = Path(tmp) / "source.pdf"
            source_pdf.write_bytes(b"%PDF-1.4\n%fake\n")
            expected_output = source_pdf.parent / "front_page.png"
            captured_args: list[str] = []

            def _fake_run(args: list[str], **_kwargs: object) -> SimpleNamespace:
                nonlocal captured_args
                captured_args = list(args)
                expected_output.write_bytes(b"png-bytes")
                return SimpleNamespace(returncode=0)

            with patch("sapi.ingest.records_writer.shutil.which", return_value="/usr/bin/pdftoppm"), patch(
                "sapi.ingest.records_writer.subprocess.run",
                side_effect=_fake_run,
            ):
                rendered = records_writer._render_pdf_front_page_image(source_artifact_path=source_pdf)

            self.assertEqual(rendered, expected_output)
            self.assertIn("-scale-to-x", captured_args)
            self.assertIn(str(records_writer._FRONT_PAGE_MAX_WIDTH_PX), captured_args)
            self.assertIn("-scale-to-y", captured_args)
            self.assertIn("-1", captured_args)

    def test_source_record_metadata_extensions_use_unknown_defaults_when_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            input_file = Path(tmp) / "paper.txt"
            input_file.write_text("paper\n")

            result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(input_file),
                source_title_override="Defaulted Paper",
            )
            record = json.loads(result.record_path.read_text())

            self.assertIsNone(record["article_kind"])
            self.assertIsNone(record["citation_count"])
            self.assertIsNone(record["citation_count_as_of"])
            self.assertEqual(record["citation_count_provider"], "unknown")
            self.assertEqual(record["citation_count_confidence"], "unknown")

    def test_source_record_metadata_extensions_persist_valid_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            input_file = Path(tmp) / "paper.txt"
            input_file.write_text("paper\n")

            result = ingest_source_artifacts_and_record(
                space_root=space_root,
                source_path_or_url=str(input_file),
                source_title_override="Empirical Paper",
                article_kind="empirical",
                citation_count=128,
                citation_count_as_of="2026-04-12",
                citation_count_provider="crossref",
                citation_count_confidence="high",
            )
            record = json.loads(result.record_path.read_text())

            self.assertEqual(record["article_kind"], "empirical")
            self.assertEqual(record["citation_count"], 128)
            self.assertEqual(record["citation_count_as_of"], "2026-04-12")
            self.assertEqual(record["citation_count_provider"], "crossref")
            self.assertEqual(record["citation_count_confidence"], "high")

    def test_source_record_metadata_extensions_reject_out_of_contract_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            input_file = Path(tmp) / "paper.txt"
            input_file.write_text("paper\n")

            with self.assertRaises(ValueError):
                ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=str(input_file),
                    source_title_override="Bad Kind",
                    article_kind="blog_post",
                )

            with self.assertRaises(ValueError):
                ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=str(input_file),
                    source_title_override="Bad Confidence",
                    citation_count_confidence="certain",
                )

            with self.assertRaises(ValueError):
                ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=str(input_file),
                    source_title_override="Bad As Of",
                    citation_count_as_of="2026/04/12",
                )

            with self.assertRaises(ValueError):
                ingest_source_artifacts_and_record(
                    space_root=space_root,
                    source_path_or_url=str(input_file),
                    source_title_override="Bad Count",
                    citation_count=-1,
                )


@contextmanager
def _served_source_bytes(
    *,
    body: bytes,
    content_type: str,
    route_path: str = "/source",
) -> Iterator[str]:
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != route_path:
                self.send_response(404)
                self.end_headers()
                return
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
        yield f"http://{host}:{port}{route_path}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    unittest.main()
