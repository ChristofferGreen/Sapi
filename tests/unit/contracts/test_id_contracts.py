from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
import re
import tempfile
import unittest
from pathlib import Path

from sapi.contracts.ids import (
    COMPACT_UTC_TIMESTAMP_RE,
    DETERMINISTIC_SUFFIX_RE,
    EXECUTION_SUFFIX_RE,
    RFC3339_UTC_RE,
    format_comment_no,
    format_compact_utc_timestamp,
    format_date_iso,
    format_timestamp_rfc3339_utc,
    make_claim_id,
    make_comment_uid,
    make_concept_id,
    make_deterministic_content_id,
    make_family_id,
    make_query_id,
    make_run_id,
    make_source_id,
    make_topic_id,
    slugify,
)
from sapi.contracts.paths import (
    resolve_contract_path,
    resolve_space_root_from_registry_value,
)


class IdContractTests(unittest.TestCase):
    def test_slugify_enforces_lowercase_kebab_case(self) -> None:
        self.assertEqual(slugify("  Hello, World 2026! "), "hello-world-2026")
        with self.assertRaises(ValueError):
            slugify("!!!")

    def test_deterministic_content_ids_follow_prefix_slug_suffix_contract(self) -> None:
        slug = "my-source"
        payload = "canonical payload"
        source_id = make_source_id(slug=slug, canonical_payload=payload)
        claim_id = make_claim_id(slug=slug, canonical_payload=payload)
        concept_id = make_concept_id(slug=slug, canonical_payload=payload)
        topic_id = make_topic_id(slug=slug, canonical_payload=payload)
        family_id = make_family_id(slug=slug, canonical_payload=payload)

        for prefix, value in [
            ("source", source_id),
            ("claim", claim_id),
            ("concept", concept_id),
            ("topic", topic_id),
            ("family", family_id),
        ]:
            match = re.fullmatch(rf"{prefix}-([a-z0-9]+(?:-[a-z0-9]+)*)--([0-9a-f]+)", value)
            self.assertIsNotNone(match, value)
            suffix = match.group(2)
            self.assertRegex(suffix, DETERMINISTIC_SUFFIX_RE)

    def test_execution_and_comment_ids_follow_timestamp_and_suffix_contract(self) -> None:
        moment = datetime(2026, 4, 12, 9, 30, 45, tzinfo=UTC)
        run_id = make_run_id(moment=moment, suffix="abcde12345")
        query_id = make_query_id(slug="policy-check", moment=moment, suffix="qwert12345")
        comment_uid = make_comment_uid(slug="thread-root", suffix="uidxx12345")

        run_match = re.fullmatch(r"run-(\d{8}T\d{6}Z)--([a-z0-9]+)", run_id)
        self.assertIsNotNone(run_match, run_id)
        self.assertRegex(run_match.group(1), COMPACT_UTC_TIMESTAMP_RE)
        self.assertRegex(run_match.group(2), EXECUTION_SUFFIX_RE)

        query_match = re.fullmatch(r"query-(\d{8}T\d{6}Z)-([a-z0-9]+(?:-[a-z0-9]+)*)--([a-z0-9]+)", query_id)
        self.assertIsNotNone(query_match, query_id)
        self.assertRegex(query_match.group(1), COMPACT_UTC_TIMESTAMP_RE)
        self.assertRegex(query_match.group(3), EXECUTION_SUFFIX_RE)

        comment_match = re.fullmatch(r"comment-([a-z0-9]+(?:-[a-z0-9]+)*)--([a-z0-9]+)", comment_uid)
        self.assertIsNotNone(comment_match, comment_uid)
        self.assertRegex(comment_match.group(2), EXECUTION_SUFFIX_RE)
        self.assertEqual(format_comment_no(7), "pc-007")

    def test_id_suffix_constraints_are_enforced(self) -> None:
        with self.assertRaises(ValueError):
            make_deterministic_content_id(
                "source",
                slug="policy-check",
                canonical_payload="payload",
                suffix_length=11,
            )
        with self.assertRaises(ValueError):
            make_run_id(suffix_length=9)
        with self.assertRaises(ValueError):
            make_query_id(slug="policy-check", suffix_length=9)
        with self.assertRaises(ValueError):
            make_comment_uid(slug="thread-root", suffix_length=9)
        with self.assertRaises(ValueError):
            make_run_id(suffix="ABCDEF1234")
        with self.assertRaises(ValueError):
            make_query_id(slug="policy-check", suffix="short123")
        with self.assertRaises(ValueError):
            make_comment_uid(slug="thread-root", suffix="short123")

    def test_temporal_format_helpers_match_contract(self) -> None:
        moment = datetime(2026, 4, 12, 9, 30, 45, tzinfo=UTC)
        self.assertEqual(format_timestamp_rfc3339_utc(moment), "2026-04-12T09:30:45Z")
        self.assertRegex(format_timestamp_rfc3339_utc(moment), RFC3339_UTC_RE)
        self.assertEqual(format_compact_utc_timestamp(moment), "20260412T093045Z")
        self.assertRegex(format_compact_utc_timestamp(moment), COMPACT_UTC_TIMESTAMP_RE)
        self.assertEqual(format_date_iso(date(2026, 4, 12)), "2026-04-12")
        naive_moment = datetime(2026, 4, 12, 9, 30, 45)
        self.assertEqual(format_timestamp_rfc3339_utc(naive_moment), "2026-04-12T09:30:45Z")
        offset_moment = datetime(2026, 4, 12, 11, 30, 45, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(format_timestamp_rfc3339_utc(offset_moment), "2026-04-12T09:30:45Z")


class PathContractTests(unittest.TestCase):
    def test_resolve_contract_path_tokens_and_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            site_path = tmp_path / "site"
            space_root = site_path / "spaces" / "alpha"
            repo_root.mkdir(parents=True)
            site_path.mkdir(parents=True)
            space_root.mkdir(parents=True)

            self.assertEqual(
                resolve_contract_path(
                    "<repo_root>/personas/users.json",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                (repo_root / "personas/users.json").resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "<site_path>/spaces/alpha",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                (site_path / "spaces/alpha").resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "<space_root>/topics/topic-a.json",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                (space_root / "topics/topic-a.json").resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "site/index.html",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                (space_root / "site/index.html").resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "outputs/query/q.json",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                (space_root / "outputs/query/q.json").resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "raw/source.pdf",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                (space_root / "raw/source.pdf").resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "personas/social_users.json",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                (repo_root / "personas/social_users.json").resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "<repo_root>",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                repo_root.resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "<site_path>",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                site_path.resolve(),
            )
            self.assertEqual(
                resolve_contract_path(
                    "<space_root>",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                ),
                space_root.resolve(),
            )

    def test_resolve_contract_path_rejects_prohibited_or_undocumented_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            site_path = tmp_path / "site"
            space_root = site_path / "spaces" / "alpha"
            repo_root.mkdir(parents=True)
            site_path.mkdir(parents=True)
            space_root.mkdir(parents=True)

            with self.assertRaises(ValueError):
                resolve_contract_path(
                    "sites/main/spaces/alpha",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                )
            with self.assertRaises(ValueError):
                resolve_contract_path(
                    "claims/claim-foo.html",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                )
            with self.assertRaises(ValueError):
                resolve_contract_path(
                    "  ",
                    repo_root=repo_root,
                    site_path=site_path,
                    space_root=space_root,
                )

    def test_registry_space_root_resolution_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "site" / "spaces.toml"
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text("# registry")

            relative = resolve_space_root_from_registry_value(registry_path, "spaces/alpha")
            self.assertEqual(relative, (registry_path.parent / "spaces/alpha").resolve())

            absolute = resolve_space_root_from_registry_value(registry_path, "/tmp/alpha")
            self.assertEqual(absolute, Path("/tmp/alpha").resolve())


if __name__ == "__main__":
    unittest.main()
