from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.conftest import REPO_ROOT, bootstrap_site_and_space, run_command
from sapi.questions.prepared_questions import write_prepared_question_record


GOLDEN_SITE_SNAPSHOT = (
    Path(__file__).resolve().parent / "site_snapshot" / "space_home_empty.html"
)
GOLDEN_SITE_ROOT_INDEX_SNAPSHOT = (
    Path(__file__).resolve().parent / "site_snapshot" / "site_root_index_empty.html"
)
GOLDEN_PREPARED_QUESTION_INDEX_CONTENT = (
    Path(__file__).resolve().parent / "site_snapshot" / "prepared_question_index_content.html"
)
GOLDEN_PREPARED_QUESTION_DETAIL_CONTENT = (
    Path(__file__).resolve().parent / "site_snapshot" / "prepared_question_detail_content.html"
)


class SiteSnapshotGoldenTests(unittest.TestCase):
    def test_site_root_index_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            actual = (site_path / "site" / "index.html").read_text()
            expected = GOLDEN_SITE_ROOT_INDEX_SNAPSHOT.read_text()
            self.assertEqual(actual, expected)

    def test_empty_space_home_matches_golden_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            actual = (site_path / "spaces" / "alpha" / "site" / "index.html").read_text()
            expected = GOLDEN_SITE_SNAPSHOT.read_text()
            self.assertEqual(actual, expected)

    def test_prepared_question_index_and_detail_match_golden_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"
            _write_prepared_question_golden_fixture(space_root)
            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            question_index = (space_root / "site" / "questions" / "index.html").read_text()
            question_detail = (
                space_root / "site" / "questions" / "question-protein-intake.html"
            ).read_text()
            self.assertEqual(
                _content_card(question_index),
                GOLDEN_PREPARED_QUESTION_INDEX_CONTENT.read_text(),
            )
            self.assertEqual(
                _content_card(question_detail),
                GOLDEN_PREPARED_QUESTION_DETAIL_CONTENT.read_text(),
            )

    def test_prepared_question_measurements_render_table_without_chart_when_no_group_is_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"
            _write_prepared_question_golden_fixture(space_root, chart_groups=[])
            result = run_command(
                [
                    "python3",
                    str(REPO_ROOT / "scripts" / "build_site.py"),
                    "--registry-path",
                    str(site_path / "spaces.toml"),
                    "alpha",
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            question_detail = (
                space_root / "site" / "questions" / "question-protein-intake.html"
            ).read_text()
            content = _content_card(question_detail)
            self.assertIn("question-measurement-table", content)
            self.assertIn("No compatible measurement group is available for charting.", content)
            self.assertNotIn("question-measurement-chart", content)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _content_card(html: str) -> str:
    start = html.index('<section class="content-card">')
    end = html.index("\n</section>\n\n</main>", start) + len("\n</section>")
    return html[start:end] + "\n"


def _write_prepared_question_golden_fixture(
    space_root: Path,
    *,
    chart_groups: list[dict[str, object]] | None = None,
) -> None:
    source_id = "source-protein--123456789abc"
    claim_id = "claim-protein-intake--123456789abc"
    evidence_id = "evidence-protein-intake--123456789abc"
    measurement_id = "measurement-protein-intake--123456789abc"
    _write_json(
        space_root / "sources" / "records" / f"{source_id}.json",
        {
            "schema_version": "source_record_v1",
            "source_id": source_id,
            "title": "Protein Source",
            "date": "2026-05-01",
            "ingested_at": "2026-05-01T00:00:00Z",
            "summary": "Protein dose-response summary.",
        },
    )
    _write_json(
        space_root / "claims" / f"{claim_id}.json",
        {
            "schema_version": "claim_record_v1",
            "claim_id": claim_id,
            "source_id": source_id,
            "text": "Protein intake supports muscle growth.",
            "short_title": "Protein intake",
        },
    )
    _write_json(
        space_root / "evidence" / f"{evidence_id}.json",
        {
            "schema_version": "evidence_record_v1",
            "evidence_id": evidence_id,
            "source_id": source_id,
            "title": "Protein dose evidence",
            "excerpt": "Protein intake of 1.6 to 2.2 g/kg/day supported hypertrophy.",
            "overview": "Dose evidence overview.",
            "evidence_type": "measurement",
            "claim_ids": [claim_id],
        },
    )
    _write_json(
        space_root / "measurements" / f"{measurement_id}.json",
        {
            "schema_version": "question_measurement_v1",
            "question_id": "question-protein-intake",
            "measurement_id": measurement_id,
            "source_id": source_id,
            "claim_id": claim_id,
            "evidence_id": evidence_id,
            "measure_name": "protein intake",
            "value": 1.6,
            "value_max": 2.2,
            "unit": "g/kg/day",
            "population": "resistance-trained adults",
            "outcome": "muscle hypertrophy",
            "comparator": "lower intake",
            "uncertainty": "range depends on training context",
        },
    )
    if chart_groups is None:
        chart_groups = [
            {
                "chart_group_id": "chart-protein-intake",
                "measure_name": "protein intake",
                "unit": "g/kg/day",
                "population": "resistance-trained adults",
                "outcome": "muscle hypertrophy",
                "measurement_ids": [measurement_id],
            }
        ]
    write_prepared_question_record(
        space_root=space_root,
        space_name="alpha",
        payload={
            "schema_version": "prepared_question_v1",
            "question_id": "question-protein-intake",
            "question": "What protein intake supports muscle growth?",
            "status": "active",
            "display_order": 1,
            "scope": {"space_name": "alpha"},
            "linked_source_ids": [source_id],
            "claim_ids": [claim_id],
            "evidence_ids": [evidence_id],
            "measurement_ids": [measurement_id],
            "synthesis": {
                "schema_version": "question_synthesis_v1",
                "question_id": "question-protein-intake",
                "short_answer": "Current evidence supports a protein intake range.",
                "conclusions": [
                    {
                        "text": "Protein intake is relevant when resistance training is present.",
                        "support": "moderate",
                        "source_ids": [source_id],
                        "claim_ids": [claim_id],
                        "evidence_ids": [evidence_id],
                    }
                ],
                "uncertainty": "Population and training status affect the range.",
                "disagreements": [],
                "citation_anchors": [],
                "warnings": [],
            },
            "freshness": {
                "question_synthesis": {
                    "status": "refreshed",
                    "run_id": "run-20260501T120000Z--abcdefghij",
                    "input_signature": "sha256:synthesis",
                    "semantic_output_path": (
                        "runs/run-20260501T120000Z--abcdefghij/semantic/question_synthesis/"
                        "question-protein-intake.json"
                    ),
                    "refreshed_at": "2026-05-01T12:00:00Z",
                },
                "question_measurement_extraction": {
                    "status": "refreshed",
                    "run_id": "run-20260501T120000Z--abcdefghij",
                    "input_signature": "sha256:measurements",
                    "semantic_output_path": (
                        "runs/run-20260501T120000Z--abcdefghij/semantic/"
                        "question_measurement_extraction/question-protein-intake.json"
                    ),
                    "refreshed_at": "2026-05-01T12:00:00Z",
                    "measurement_ids": [measurement_id],
                    "chart_groups": chart_groups,
                    "warnings": [],
                },
            },
            "warnings": [],
        },
    )


if __name__ == "__main__":
    unittest.main()
