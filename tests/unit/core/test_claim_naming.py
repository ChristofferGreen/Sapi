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

    def test_resolve_claim_short_title_keeps_existing_verb_statement(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="",
            claim_text="Splay operations stay logarithmic",
        )
        self.assertEqual(title, "Splay operations stay logarithmic")

    def test_resolve_claim_short_title_rewrites_quantified_of_phrase(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="",
            claim_text="The introduction identifies two layers of underdetermination between rival responses.",
        )
        self.assertEqual(title, "Underdetermination has two layers")

    def test_resolve_claim_short_title_collapses_redundant_is_after_verb(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="Quarter probability saves is space",
            claim_text="Quarter probability saves space",
        )
        self.assertEqual(title, "Quarter probability saves space")

    def test_resolve_claim_short_title_prefers_verb_relation_before_late_copula(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="Embodiment grounds quantum is facts",
            claim_text="Embodiment grounds quantum facts",
        )
        self.assertEqual(title, "Embodiment grounds quantum facts")

    def test_resolve_claim_short_title_removes_subject_repetition_from_predicate(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="CompCert preserves safety is CompCert preserves source",
            claim_text="CompCert preserves source-level safety",
        )
        self.assertNotIn(" is ", f" {title.lower()} ")
        self.assertNotIn("CompCert preserves safety CompCert", title)

    def test_resolve_claim_short_title_handles_late_copula_with_additional_verbs(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="Four outcomes exclude is overlap",
            claim_text="Four outcomes exclude overlap",
        )
        self.assertEqual(title, "Four outcomes exclude overlap")

    def test_resolve_claim_short_title_discards_malformed_raw_title(self) -> None:
        title = resolve_claim_short_title(
            raw_short_title="Skip lists replace is balanced trees",
            claim_text="Skip lists replace balanced trees",
        )
        self.assertEqual(title, "Skip lists replace balanced trees")


if __name__ == "__main__":
    unittest.main()
