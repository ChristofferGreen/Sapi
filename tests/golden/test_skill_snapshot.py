from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_SKILLS_DIR = Path(__file__).resolve().parent / "skills"


class SkillSnapshotGoldenTests(unittest.TestCase):
    def test_skill_prompt_files_match_golden_snapshots(self) -> None:
        skill_paths = sorted((REPO_ROOT / ".skills").glob("*.skill"))
        self.assertGreaterEqual(len(skill_paths), 1)
        for skill_path in skill_paths:
            with self.subTest(skill=skill_path.name):
                golden_path = GOLDEN_SKILLS_DIR / skill_path.name
                self.assertTrue(golden_path.is_file(), f"Missing golden snapshot: {golden_path}")
                self.assertEqual(skill_path.read_text(), golden_path.read_text())


if __name__ == "__main__":
    unittest.main()
