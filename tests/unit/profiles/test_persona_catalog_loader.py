from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.profiles.persona_catalog import load_seeded_persona_catalog


class PersonaCatalogLoaderTests(unittest.TestCase):
    def test_loader_reads_canonical_catalog_and_ignores_site_local_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "alice.png")
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        persona_id="persona-alice",
                        id="persona-alice",
                        profile_image_path="personas/profile_images/alice.png",
                    )
                ],
            )
            # Site/space-local copies are intentionally ignored by contract.
            site_catalog = (
                repo_root
                / "site-a"
                / "spaces"
                / "alpha"
                / "personas"
                / "social_users.json"
            )
            site_catalog.parent.mkdir(parents=True, exist_ok=True)
            site_catalog.write_text(
                json.dumps([self._persona_row(persona_id="persona-site-only")], indent=2) + "\n"
            )

            rows = load_seeded_persona_catalog(repo_root=repo_root)
            self.assertEqual([row["persona_id"] for row in rows], ["persona-alice"])

    def test_loader_supports_compatibility_mirror_when_canonical_catalog_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "mirror.png")
            self._write_catalog(
                repo_root / "personas" / "users.json",
                [
                    self._persona_row(
                        id="persona-mirror",
                        persona_id=None,
                        profile_image_path="personas/profile_images/mirror.png",
                    )
                ],
            )

            rows = load_seeded_persona_catalog(repo_root=repo_root, allow_compatibility_mirror=True)
            self.assertEqual(rows[0]["persona_id"], "persona-mirror")

            with self.assertRaises(FileNotFoundError):
                load_seeded_persona_catalog(
                    repo_root=repo_root,
                    allow_compatibility_mirror=False,
                )

    def test_loader_normalizes_legacy_id_alias_and_rejects_mismatched_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "alias.png")
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        id="persona-alias",
                        persona_id=None,
                        profile_image_path="personas/profile_images/alias.png",
                    )
                ],
            )

            rows = load_seeded_persona_catalog(repo_root=repo_root)
            self.assertEqual(rows[0]["persona_id"], "persona-alias")

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(persona_id="persona-a", id="persona-b")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_rejects_duplicate_or_invalid_persona_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "dup.png")
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        persona_id="persona-dup",
                        id="persona-dup",
                        profile_image_path="personas/profile_images/dup.png",
                    ),
                    self._persona_row(
                        persona_id="persona-dup",
                        id="persona-dup",
                        profile_image_path="personas/profile_images/dup.png",
                    ),
                ],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(persona_id="Persona Upper", id="Persona Upper")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_requires_profile_image_under_repo_seeded_profile_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "ok.png")

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_path="personas/profile_images/missing.png")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_path="personas/not-profile-images/ok.png")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_path="personas/profile_images/ok.png")],
            )
            rows = load_seeded_persona_catalog(repo_root=repo_root)
            self.assertEqual(len(rows), 1)

    def _write_image(self, repo_root: Path, file_name: str) -> None:
        image_path = repo_root / "personas" / "profile_images" / file_name
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_text("image-bytes-placeholder\n")

    def _write_catalog(self, path: Path, users: list[dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "social_users_v1",
            "count": len(users),
            "generated_at": "2026-04-12T00:00:00Z",
            "users": users,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _persona_row(
        self,
        *,
        persona_id: str | None = "persona-default",
        id: str | None = None,
        profile_image_path: str = "personas/profile_images/ok.png",
    ) -> dict[str, object]:
        row: dict[str, object] = {
            "display_name": "Default Persona",
            "full_name": "Default Persona",
            "account_status": "active",
            "stance_profile": "neutral",
            "personality": "measured",
            "biography": "Short biography",
            "interests": ["policy"],
            "hot_topics": ["planning"],
            "anger_topics": ["misinformation"],
            "prompt_fields": {
                "core_belief": "Evidence over rhetoric",
                "argument_style": "structured",
                "tone": "formal",
                "evidence_preference": "citations",
            },
            "profile_image_path": profile_image_path,
        }
        if persona_id is not None:
            row["persona_id"] = persona_id
        if id is not None:
            row["id"] = id
        return row


if __name__ == "__main__":
    unittest.main()
