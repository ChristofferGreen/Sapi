from __future__ import annotations

import unittest

from sapi.ingest.source_content import resolve_publication_date, resolve_source_title


class SourceDateTitlePolicyTests(unittest.TestCase):
    def test_source_title_resolution_follows_five_step_priority_contract(self) -> None:
        # 1) --source-title override
        self.assertEqual(
            resolve_source_title(
                source_title_override="Override Title",
                source_metadata_title="Metadata Title",
                in_source_title_line="In-Source Title",
                source_locator="/tmp/fallback-title.pdf",
            ),
            "Override Title",
        )

        # 2) metadata title
        self.assertEqual(
            resolve_source_title(
                source_title_override=None,
                source_metadata_title="Metadata Title",
                in_source_title_line="In-Source Title",
                source_locator="/tmp/fallback-title.pdf",
            ),
            "Metadata Title",
        )

        # 3) in-source title line
        self.assertEqual(
            resolve_source_title(
                source_title_override=None,
                source_metadata_title=None,
                in_source_title_line="In-Source Title",
                source_locator="/tmp/fallback-title.pdf",
            ),
            "In-Source Title",
        )

        # 4) URL/file-stem fallback
        self.assertEqual(
            resolve_source_title(
                source_title_override=None,
                source_metadata_title=None,
                in_source_title_line=None,
                source_locator="https://example.org/papers/2024/causal-methods.pdf",
            ),
            "causal-methods",
        )

        # 5) Untitled Source
        self.assertEqual(
            resolve_source_title(
                source_title_override=None,
                source_metadata_title=None,
                in_source_title_line=None,
                source_locator=None,
            ),
            "Untitled Source",
        )

    def test_missing_publication_date_emits_warning_and_unknown_source_date_inference(self) -> None:
        resolution = resolve_publication_date(
            explicit_source_date=None,
            inferred_source_date=None,
            require_source_date=False,
        )

        self.assertIsNone(resolution.publication_date)
        self.assertEqual(
            resolution.source_date_inference,
            {
                "date": None,
                "origin": "unknown",
                "confidence": "unknown",
                "rationale": None,
            },
        )
        self.assertEqual(len(resolution.warnings), 1)
        self.assertEqual(resolution.warnings[0]["code"], "missing_publication_date")

    def test_require_source_date_strict_mode_fails_when_date_cannot_be_resolved(self) -> None:
        with self.assertRaises(ValueError):
            resolve_publication_date(
                explicit_source_date=None,
                inferred_source_date=None,
                require_source_date=True,
            )

    def test_explicit_source_date_overrides_inferred_date(self) -> None:
        resolution = resolve_publication_date(
            explicit_source_date="2026-04-01",
            inferred_source_date="2026-03-20",
            require_source_date=True,
        )
        self.assertEqual(resolution.publication_date, "2026-04-01")
        self.assertEqual(resolution.source_date_inference["origin"], "explicit")
        self.assertEqual(resolution.warnings, [])


if __name__ == "__main__":
    unittest.main()
