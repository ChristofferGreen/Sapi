from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DESIGN_DOC_PATH = REPO_ROOT / "docs" / "design.md"
LOW_LEVEL_DOC_PATH = REPO_ROOT / "docs" / "low_level.md"


class CanonicalOnlyDocContractTests(unittest.TestCase):
    def test_generation_spec_contract_is_canonical_only(self) -> None:
        section = _section_text(
            DESIGN_DOC_PATH.read_text(),
            "### 4.1.3 Generation spec discovery and versioning (normative)",
        )
        self.assertIn("Canonical-only naming policy (normative):", section)
        self.assertIn(
            "unknown flow keys, including `persona_comment_generation`, MUST fail fast",
            section,
        )
        self.assertNotIn("Compatibility-reader sunset policy for legacy aliases", section)
        self.assertNotIn("MAY be accepted on read/CLI/config input", section)

    def test_comment_contracts_require_canonical_flags_and_markers(self) -> None:
        section = _section_text(
            DESIGN_DOC_PATH.read_text(),
            "### 7.6 Comment section generation and rendering",
        )
        self.assertIn(
            "removed non-canonical inputs `--user`, `--page`, positional count `<n>`, and `--comment-web-evidence` MUST fail fast",
            section,
        )
        self.assertIn("legacy HTML comment markers are non-canonical and MUST fail fast", section)
        self.assertIn("markdown frontmatter-only controls are non-canonical and MUST fail fast", section)
        self.assertNotIn("compatibility input aliases:", section)
        self.assertNotIn("compatibility schema alias accepted on read/import", section)

    def test_low_level_docs_no_longer_describe_alias_normalization(self) -> None:
        low_level_text = LOW_LEVEL_DOC_PATH.read_text()
        spec_section = _section_text(low_level_text, "### 6.1 Spec resolution and version pinning")
        comments_section = _section_text(low_level_text, "### 8.3 Comment Section Pipeline (`scripts/create_comments.py`)")
        wrapper_section = _section_text(low_level_text, "## 12. Wrapper Interface Notes")

        self.assertIn(
            "unknown flow keys, including `persona_comment_generation`, MUST fail fast before resolution",
            spec_section,
        )
        self.assertIn(
            "reject removed non-canonical comment flags (`--user`, `--page`, positional count `<n>`, `--comment-web-evidence`) with usage error",
            comments_section,
        )
        self.assertIn("fail fast on removed non-canonical aliases instead of normalizing them", wrapper_section)
        self.assertNotIn("normalize compatibility aliases", low_level_text)
        self.assertNotIn("Required alias normalization:", low_level_text)


def _section_text(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    if end == -1:
        end = len(text)
    return text[start:end]


if __name__ == "__main__":
    unittest.main()
