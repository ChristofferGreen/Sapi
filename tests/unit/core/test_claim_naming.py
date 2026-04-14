from __future__ import annotations

import unittest

from sapi.core.claim_naming import (
    normalize_claim_statement_text,
    resolve_claim_short_title,
    shorten_claim_label,
)


class ClaimNamingTests(unittest.TestCase):
    def test_normalize_claim_statement_rewrites_assumption_meta_phrasing(self) -> None:
        text = (
            "A second core assumption is preparation independence: independently prepared systems "
            "have independent underlying physical states."
        )
        normalized = normalize_claim_statement_text(text)
        self.assertEqual(normalized, "Preparation independence is assumed")

    def test_normalize_claim_statement_rewrites_reporting_leadins(self) -> None:
        text = (
            "The paper also gives a noise-tolerant formal version of the theorem, deriving a lower "
            "bound on the total variation distance between associated state distributions."
        )
        normalized = normalize_claim_statement_text(text)
        self.assertNotIn("paper", normalized.casefold())
        self.assertIn("derives", normalized.casefold())

    def test_resolve_claim_short_title_enforces_proposition_word_budget(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="",
            claim_text=(
                "The paper presents a no-go theorem: treating the quantum state as mere information "
                "about an underlying physical state leads to contradiction with quantum theory."
            ),
        )
        words = title.split()
        self.assertGreaterEqual(len(words), 3)
        self.assertLessEqual(len(words), 7)
        self.assertNotIn("paper", title.casefold())
        self.assertTrue(any(token.casefold() in {"is", "shows", "implies", "has"} for token in words))

    def test_resolve_claim_short_title_uses_lower_bound_shape_when_available(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="",
            claim_text=(
                "The paper also gives a noise-tolerant formal version of the theorem, deriving a lower "
                "bound on the total variation distance between underlying-state distributions."
            ),
        )
        self.assertEqual(title, "Total variation has lower bound")

    def test_resolve_claim_short_title_converts_incomplete_meta_phrase_to_proposition(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="",
            claim_text="The paper also gives a noise-tolerant formal version",
        )
        self.assertEqual(title, "Noise-tolerant formal version exists")

    def test_shorten_claim_label_uses_fallback_claim_text_when_short_title_missing(self) -> None:
        label = shorten_claim_label(
            value="",
            fallback_text="The paper claims that preparation independence constrains epistemic overlaps.",
        )
        self.assertEqual(label, "Preparation independence constrains epistemic overlaps")


if __name__ == "__main__":
    unittest.main()
