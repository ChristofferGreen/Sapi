from __future__ import annotations

import unittest

from sapi.core.display_titles import normalize_display_title_strict
from sapi.core.display_titles import resolve_display_title


class DisplayTitleTests(unittest.TestCase):
    def test_resolve_prefers_strict_quality_candidate_over_slugish_candidate(self) -> None:
        resolved = resolve_display_title(
            candidates=[
                "springer_ejps_2020",
                "Epistemic Limits in Quantum Metaphysics",
            ],
            fallback="source-springer-ejps-2020--3da4c0bbba13",
        )

        self.assertEqual(resolved, "Epistemic Limits in Quantum Metaphysics")

    def test_resolve_accepts_short_legacy_title_via_relaxed_fallback(self) -> None:
        resolved = resolve_display_title(
            candidates=["Source A"],
            fallback="source-source-a--123456789abc",
        )

        self.assertEqual(resolved, "Source A")

    def test_resolve_humanizes_source_id_when_candidates_are_invalid(self) -> None:
        resolved = resolve_display_title(
            candidates=["https://example.com/source.pdf"],
            fallback="source-pusey-barrett-rudolph-2012--e197f59c8424",
        )

        self.assertEqual(resolved, "Pusey Barrett Rudolph 2012")

    def test_strict_normalization_rejects_slugish_year_text(self) -> None:
        self.assertIsNone(normalize_display_title_strict("springer_ejps_2020"))


if __name__ == "__main__":
    unittest.main()
