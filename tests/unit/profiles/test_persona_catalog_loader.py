from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from sapi.profiles.persona_catalog import load_seeded_persona_catalog


class PersonaCatalogLoaderTests(unittest.TestCase):
    def test_loader_reads_canonical_catalog_and_ignores_site_local_copies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "alice.jpg")
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        persona_id="persona-alice",
                        profile_image_path="personas/profile_images/alice.jpg",
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

    def test_loader_requires_canonical_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            with self.assertRaises(FileNotFoundError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_rejects_legacy_id_field_and_requires_explicit_persona_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "alias.jpg")
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        id="persona-alias",
                        persona_id=None,
                        profile_image_path="personas/profile_images/alias.jpg",
                    )
                ],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(persona_id="persona-a", id="persona-a")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    {
                        key: value
                        for key, value in self._persona_row(
                            persona_id="persona-alias",
                            profile_image_path="personas/profile_images/alias.jpg",
                        ).items()
                        if key != "persona_id"
                    }
                ],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_rejects_duplicate_or_invalid_persona_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "dup.jpg")
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        persona_id="persona-dup",
                        profile_image_path="personas/profile_images/dup.jpg",
                    ),
                    self._persona_row(
                        persona_id="persona-dup",
                        profile_image_path="personas/profile_images/dup.jpg",
                    ),
                ],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_enforces_name_slug_mapping_for_ids_and_profile_image_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "alice-example.jpg")
            self._write_image(repo_root, "alice-mismatch.jpg")

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        full_name="Alice Example",
                        persona_id="persona-alice-example",
                        profile_image_path="personas/profile_images/alice-example.jpg",
                    )
                ],
            )
            rows = load_seeded_persona_catalog(repo_root=repo_root)
            self.assertEqual(rows[0]["persona_id"], "persona-alice-example")

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        full_name="Alice Example",
                        persona_id="persona-alice-mismatch",
                        profile_image_path="personas/profile_images/alice-example.jpg",
                    )
                ],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [
                    self._persona_row(
                        full_name="Alice Example",
                        persona_id="persona-alice-example",
                        profile_image_path="personas/profile_images/alice-mismatch.jpg",
                    )
                ],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(persona_id="Persona Upper")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_requires_profile_image_under_repo_seeded_profile_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "ok.jpg")

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_path="personas/profile_images/missing.jpg")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_path="personas/not-profile-images/ok.jpg")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_path="personas/profile_images/ok.jpg")],
            )
            rows = load_seeded_persona_catalog(repo_root=repo_root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["profile_image_thumb_path"], "personas/profile_images/ok-thumb.jpg")

            self._write_image(repo_root, "ok.svg")
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_path="personas/profile_images/ok.svg")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_enforces_biography_voice_length_and_topic_richness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "ok.jpg")

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(biography="This biography is third person and too short.")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(biography="I am brief.")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            long_bio = "I " + "word " * 260
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(biography=long_bio)],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(interests=[])],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(biography_profile="Short profile blurb.")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            third_person_profile = (
                "Default Persona is a pragmatic reviewer who helps teams balance evidence, uncertainty, and "
                "delivery pressure with clear tradeoffs. They keep discussions focused and improve decisions "
                "with concrete implementation checks and explicit risk ownership."
            )
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(biography_profile=third_person_profile)],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            same_text = (
                "I evaluate ideas by tracing assumptions, evidence quality, and real-world tradeoffs before "
                "I endorse a claim. I prefer transparent methods over charisma, and I routinely ask what "
                "data is missing, who bears risk, and what would falsify the argument. I prioritize "
                "durable outcomes, clear accountability, and practical implementation details that survive "
                "pressure. I become skeptical when confidence outruns proof, when caveats are hidden, or "
                "when policy choices ignore operational constraints. I communicate directly, cite sources "
                "precisely, and revise my position when stronger evidence appears. I also document "
                "uncertainty explicitly so collaborators can challenge assumptions early."
            )
            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(biography=same_text, biography_profile=same_text)],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(short_cv=[])],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

    def test_loader_enforces_profile_image_prompt_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            self._write_image(repo_root, "ok.jpg")

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_prompt="draw an icon")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

            self._write_catalog(
                repo_root / "personas" / "social_users.json",
                [self._persona_row(profile_image_prompt="Photorealistic landscape with mountains and no visible person in frame.")],
            )
            with self.assertRaises(ValueError):
                load_seeded_persona_catalog(repo_root=repo_root)

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
        persona_id: str | None = None,
        id: str | None = None,
        full_name: str | None = None,
        display_name: str | None = None,
        profile_image_path: str | None = None,
        profile_image_prompt: str | None = None,
        biography: str | None = None,
        biography_profile: str | None = None,
        short_cv: list[str] | None = None,
        interests: list[str] | None = None,
        hot_topics: list[str] | None = None,
        anger_topics: list[str] | None = None,
    ) -> dict[str, object]:
        slug = self._default_slug(
            persona_id=persona_id,
            legacy_id=id,
            full_name=full_name,
            profile_image_path=profile_image_path,
        )
        if full_name is None:
            full_name = " ".join(part.capitalize() for part in slug.split("-"))
        if display_name is None:
            display_name = full_name
        if profile_image_path is None:
            profile_image_path = f"personas/profile_images/{slug}.jpg"
        if persona_id is None and id is None:
            persona_id = f"persona-{slug}"

        biography_text = (
            "I evaluate ideas by tracing assumptions, evidence quality, and real-world tradeoffs before "
            "I endorse a claim. I prefer transparent methods over charisma, and I routinely ask what "
            "data is missing, who bears risk, and what would falsify the argument. I prioritize "
            "durable outcomes, clear accountability, and practical implementation details that survive "
            "pressure. I become skeptical when confidence outruns proof, when caveats are hidden, or "
            "when policy choices ignore operational constraints. I communicate directly, cite sources "
            "precisely, and revise my position when stronger evidence appears. I also document "
            "uncertainty explicitly so collaborators can challenge assumptions early."
            if biography is None
            else biography
        )
        biography_profile_text = (
            "I am known for crisp, evidence-aware judgment and clear communication under pressure. I turn "
            "messy debates into explicit tradeoffs, make uncertainty visible early, and help collaborators "
            "ship decisions that can be defended and improved."
            if biography_profile is None
            else biography_profile
        )
        short_cv_rows = (
            [
                "Senior Analyst, Example Institute (2021-present)",
                "Research Associate, Example Lab (2018-2021)",
                "MSc, Policy Analysis, Example University (2016-2018)",
            ]
            if short_cv is None
            else short_cv
        )
        row: dict[str, object] = {
            "display_name": display_name,
            "full_name": full_name,
            "account_status": "active",
            "stance_profile": "neutral",
            "personality": "measured",
            "biography": biography_text,
            "biography_profile": biography_profile_text,
            "short_cv": short_cv_rows,
            "interests": ["policy"] if interests is None else interests,
            "hot_topics": ["planning"] if hot_topics is None else hot_topics,
            "anger_topics": ["misinformation"] if anger_topics is None else anger_topics,
            "prompt_fields": {
                "core_belief": "Evidence over rhetoric",
                "argument_style": "structured",
                "tone": "formal",
                "evidence_preference": "citations",
            },
            "profile_image_path": profile_image_path,
            "profile_image_prompt": (
                "Photorealistic portrait photo of this person at home office, matching their evidence-first "
                "persona and communication style, natural lighting, candid expression."
                if profile_image_prompt is None
                else profile_image_prompt
            ),
        }
        if persona_id is not None:
            row["persona_id"] = persona_id
        if id is not None:
            row["id"] = id
        return row

    @staticmethod
    def _default_slug(
        *,
        persona_id: str | None,
        legacy_id: str | None,
        full_name: str | None,
        profile_image_path: str | None,
    ) -> str:
        if full_name:
            tokens = re.findall(r"[a-z0-9]+", full_name.lower())
            if tokens:
                return "-".join(tokens)
        if isinstance(persona_id, str) and persona_id.startswith("persona-"):
            return persona_id.removeprefix("persona-")
        if isinstance(legacy_id, str) and legacy_id.startswith("persona-"):
            return legacy_id.removeprefix("persona-")
        if profile_image_path:
            stem = Path(profile_image_path).stem
            if stem.endswith("-thumb"):
                stem = stem.removesuffix("-thumb")
            return stem
        return "ok"


if __name__ == "__main__":
    unittest.main()
