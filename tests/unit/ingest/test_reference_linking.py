from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from sapi.ingest.citations import (
    extract_normalized_references_from_text,
    run_reference_extraction_and_link_backfill,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


class ReferenceLinkingTests(unittest.TestCase):
    def test_reference_extraction_normalizes_structured_rows(self) -> None:
        text = (
            "Smith et al. 2020. Example Study. doi:10.1234/example.1\n"
            "Follow-up preprint arXiv:2401.12345 available at https://example.org/paper\n"
        )
        rows = extract_normalized_references_from_text(text)
        self.assertGreaterEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(
                set(row.keys()),
                {"title", "authors", "year", "doi", "arxiv", "url", "linked_source_ids"},
            )

    def test_reference_extraction_captures_multiple_urls_on_one_line(self) -> None:
        text = (
            "Background reading https://en.wikipedia.org/wiki/Formal_system "
            "and discussion https://www.reddit.com/r/logic/comments/example/.\n"
        )
        rows = extract_normalized_references_from_text(text)
        self.assertEqual(
            sorted(row["url"] for row in rows),
            [
                "https://en.wikipedia.org/wiki/Formal_system",
                "https://www.reddit.com/r/logic/comments/example",
            ],
        )

    def test_local_reference_matching_persists_linked_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            source_a = tmp_root / "source-a.txt"
            source_a.write_text("Primary source without references.\n")
            source_a_record = _ingest_and_get_record(
                site_path=site_path,
                source_path=source_a,
                source_title="Primary Source",
                canonical_identifier="doi:10.4242/primary.2026",
            )
            source_a_id = source_a_record["source_id"]

            source_b = tmp_root / "source-b.txt"
            source_b.write_text("Background citation doi:10.4242/primary.2026 in related work.\n")
            source_b_record = _ingest_and_get_record(
                site_path=site_path,
                source_path=source_b,
                source_title="Secondary Source",
            )

            reference = _find_reference(source_b_record["references"], doi="10.4242/primary.2026")
            self.assertEqual(reference["linked_source_ids"], [source_a_id])
            self.assertEqual(source_b_record["linked_source_ids"], [source_a_id])
            self.assertTrue((space_root / "sources" / "records" / f"{source_a_id}.json").is_file())

    def test_reference_extraction_ignores_pdf_metadata_namespace_noise(self) -> None:
        text = (
            "<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>\n"
            "<rdf:Description xmlns:pdf='http://ns.adobe.com/pdf/1.3/'>\n"
            "Legitimate citation DOI:10.4242/real.2026 and context text\n"
        )
        rows = extract_normalized_references_from_text(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["doi"], "10.4242/real.2026")
        self.assertIsNone(rows[0]["url"])

    def test_new_ingest_backfills_links_in_older_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            older_source = tmp_root / "older.txt"
            older_source.write_text("Future citation target doi:10.9898/future.7777 pending ingest.\n")
            older_record = _ingest_and_get_record(
                site_path=site_path,
                source_path=older_source,
                source_title="Older Source",
            )
            older_id = older_record["source_id"]
            older_reference = _find_reference(older_record["references"], doi="10.9898/future.7777")
            self.assertEqual(older_reference["linked_source_ids"], [])
            self.assertEqual(older_record["linked_source_ids"], [])

            future_source = tmp_root / "future.txt"
            future_source.write_text("Future source body.\n")
            future_record = _ingest_and_get_record(
                site_path=site_path,
                source_path=future_source,
                source_title="Future Source",
                canonical_identifier="doi:10.9898/future.7777",
            )
            future_id = future_record["source_id"]

            older_reloaded = json.loads(
                (space_root / "sources" / "records" / f"{older_id}.json").read_text()
            )
            older_backfilled_reference = _find_reference(
                older_reloaded["references"],
                doi="10.9898/future.7777",
            )
            self.assertEqual(older_backfilled_reference["linked_source_ids"], [future_id])
            self.assertEqual(older_reloaded["linked_source_ids"], [future_id])

    def test_reference_extraction_prefers_source_markdown_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")
            space_root = site_path / "spaces" / "alpha"

            source_a = tmp_root / "primary.txt"
            source_a.write_text("Primary source body.\n")
            source_a_record = _ingest_and_get_record(
                site_path=site_path,
                source_path=source_a,
                source_title="Primary Source",
                canonical_identifier="doi:10.3131/primary.2026",
            )
            source_a_id = source_a_record["source_id"]

            source_b = tmp_root / "secondary.txt"
            source_b.write_text("Secondary source body without useful references.\n")
            source_b_record = _ingest_and_get_record(
                site_path=site_path,
                source_path=source_b,
                source_title="Secondary Source",
            )
            source_b_id = str(source_b_record["source_id"])
            source_b_record_path = space_root / "sources" / "records" / f"{source_b_id}.json"
            source_b_artifact_root = space_root / "sources" / "artifacts" / source_b_id
            (source_b_artifact_root / "source.txt").write_bytes(b"\x00\xff\x00")
            (source_b_artifact_root / "source.md").write_text(
                "# Secondary Source\n\nBackground reference doi:10.3131/primary.2026.\n"
            )
            source_b_record["analysis_policy"]["quality_status"] = "usable"
            source_b_record["references"] = []
            source_b_record["linked_source_ids"] = []
            source_b_record_path.write_text(json.dumps(source_b_record, indent=2, sort_keys=True) + "\n")

            result = run_reference_extraction_and_link_backfill(
                space_root=space_root,
                source_id=source_b_id,
            )
            reloaded = json.loads(source_b_record_path.read_text())
            reference = _find_reference(reloaded["references"], doi="10.3131/primary.2026")
            self.assertEqual(reference["linked_source_ids"], [source_a_id])
            self.assertEqual(result.linked_source_ids, [source_a_id])

    def test_reference_enrichment_persists_curated_external_related_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            site_path = _bootstrap_site_and_space(tmp_root, "alpha")

            source = tmp_root / "links.txt"
            source.write_text(
                "Background reading https://en.wikipedia.org/wiki/Formal_system and "
                "discussion https://www.reddit.com/r/logic/comments/example/.\n"
            )
            record = _ingest_and_get_record(
                site_path=site_path,
                source_path=source,
                source_title="Links Source",
                canonical_identifier="doi:10.5151/links.2026",
            )

            links = record["external_related_links"]
            self.assertIsInstance(links, list)
            self.assertGreaterEqual(len(links), 2)
            self.assertEqual(record["related_link_enrichment"]["status"], "enriched")
            self.assertIn("canonical_identifier", record["related_link_enrichment"]["sources"])
            self.assertTrue(
                any(isinstance(link, dict) and link.get("domain") == "en.wikipedia.org" for link in links)
            )
            self.assertTrue(
                any(isinstance(link, dict) and link.get("link_type") == "discussion_forum" for link in links)
            )


def _bootstrap_site_and_space(tmp_root: Path, space_name: str) -> Path:
    site_path = tmp_root / "site-a"
    _run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
    _run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
    return site_path


def _ingest_and_get_record(
    *,
    site_path: Path,
    source_path: Path,
    source_title: str,
    canonical_identifier: str | None = None,
) -> dict[str, object]:
    space_root = site_path / "spaces" / "alpha"
    records_dir = space_root / "sources" / "records"
    before = {path.name for path in records_dir.glob("source-*.json")} if records_dir.is_dir() else set()

    command = [
        "python3",
        str(REPO_ROOT / "scripts" / "ingest_source.py"),
        "alpha",
        str(source_path),
        "--registry-path",
        str(site_path / "spaces.toml"),
        "--source-title",
        source_title,
        "--mock-llm",
    ]
    if canonical_identifier is not None:
        command.extend(["--canonical-identifier", canonical_identifier])
    result = _run(command)
    if result.returncode != 0:
        raise AssertionError(
            f"Ingest failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    record_paths = sorted(records_dir.glob("source-*.json"))
    new_paths = [path for path in record_paths if path.name not in before]
    if len(new_paths) != 1:
        raise AssertionError(f"Expected one new source record, found {len(new_paths)}")
    return json.loads(new_paths[0].read_text())


def _find_reference(references: object, *, doi: str) -> dict[str, object]:
    if not isinstance(references, list):
        raise AssertionError("references must be a list")
    for row in references:
        if isinstance(row, dict) and row.get("doi") == doi:
            return row
    raise AssertionError(f"Reference with doi={doi} not found")


def _run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


if __name__ == "__main__":
    unittest.main()
