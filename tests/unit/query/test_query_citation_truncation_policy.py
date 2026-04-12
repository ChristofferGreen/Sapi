from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


class QueryCitationTruncationPolicyTests(unittest.TestCase):
    def test_citation_coverage_policy_is_mode_specific_and_auditable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"
            _seed_claim(space_root, "claim-a--aaaaaaaaaaaa", retrieval_rank=1)
            _seed_source(space_root, "source-a--bbbbbbbbbbbb", retrieval_rank=1)

            expected_threshold = {
                "strict": 0.9,
                "exploratory": 0.7,
                "comparative": 0.7,
            }
            for mode, threshold in expected_threshold.items():
                with self.subTest(mode=mode):
                    payload = _run_query_and_load_payload(site_path=site_path, mode=mode)
                    coverage = payload["citation_coverage"]
                    self.assertEqual(coverage["mode"], mode)
                    self.assertEqual(coverage["policy_version"], "query_citation_coverage_v1")
                    self.assertEqual(coverage["target_threshold"], threshold)
                    self.assertEqual(coverage["factual_sentence_ratio"], 1.0)
                    self.assertEqual(coverage["meets_target"], True)
                    self.assertEqual(coverage["claims_cited"], 1)
                    self.assertEqual(coverage["sources_cited"], 1)

    def test_truncation_is_rank_desc_then_lexical_tie_break_with_omitted_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = _bootstrap_site_and_space(Path(tmp), "alpha")
            space_root = site_path / "spaces" / "alpha"

            _seed_claim(space_root, "claim-z--aaaaaaaaaaaa", retrieval_rank=1)
            _seed_claim(space_root, "claim-c--aaaaaaaaaaaa", retrieval_rank=5)
            _seed_claim(space_root, "claim-a--aaaaaaaaaaaa", retrieval_rank=5)

            _seed_source(space_root, "source-z--bbbbbbbbbbbb", retrieval_rank=0)
            _seed_source(space_root, "source-c--bbbbbbbbbbbb", retrieval_rank=3)
            _seed_source(space_root, "source-a--bbbbbbbbbbbb", retrieval_rank=3)

            payload = _run_query_and_load_payload(
                site_path=site_path,
                mode="strict",
                extra_args=["--max-claims", "2", "--max-sources", "2"],
            )
            self.assertEqual(
                payload["claims_used"],
                ["claim-a--aaaaaaaaaaaa", "claim-c--aaaaaaaaaaaa"],
            )
            self.assertEqual(
                payload["sources_used"],
                ["source-a--bbbbbbbbbbbb", "source-c--bbbbbbbbbbbb"],
            )
            self.assertEqual(payload["omitted_due_to_budget"], {"claims": 1, "sources": 1})
            self.assertGreater(payload["omitted_due_to_budget"]["claims"], 0)
            self.assertGreater(payload["omitted_due_to_budget"]["sources"], 0)


def _bootstrap_site_and_space(tmp_root: Path, space_name: str) -> Path:
    site_path = tmp_root / "site-a"
    _run(["bash", str(REPO_ROOT / "create_site.sh"), str(site_path), "My Site"], check=True)
    _run(["bash", str(REPO_ROOT / "create_space.sh"), str(site_path), space_name], check=True)
    return site_path


def _seed_claim(space_root: Path, claim_id: str, *, retrieval_rank: int) -> None:
    path = space_root / "claims" / f"{claim_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"claim_id": claim_id, "retrieval_rank": retrieval_rank},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _seed_source(space_root: Path, source_id: str, *, retrieval_rank: int) -> None:
    path = space_root / "sources" / "records" / f"{source_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"source_id": source_id, "retrieval_rank": retrieval_rank},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _run_query_and_load_payload(
    *,
    site_path: Path,
    mode: str,
    extra_args: list[str] | None = None,
) -> dict[str, object]:
    space_root = site_path / "spaces" / "alpha"
    before = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
    cmd = [
        "python3",
        str(REPO_ROOT / "scripts" / "query.py"),
        "alpha",
        "policy check",
        "--registry-path",
        str(site_path / "spaces.toml"),
        "--mode",
        mode,
        "--mock-llm",
    ]
    if extra_args:
        cmd.extend(extra_args)
    result = _run(cmd)
    if result.returncode != 0:
        raise AssertionError(
            f"Query command failed unexpectedly (exit={result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    after = {path.name for path in (space_root / "outputs" / "query").glob("query-*")}
    new = sorted(after - before)
    if len(new) != 1:
        raise AssertionError(f"Expected exactly one new query output directory, got: {new}")
    query_json = space_root / "outputs" / "query" / new[0] / "query.json"
    return json.loads(query_json.read_text())


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
