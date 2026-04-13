from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sapi.core.registry import resolve_space_root
from tests.conftest import create_isolated_site_space_fixture


class HarnessFixtureFactoryTests(unittest.TestCase):
    def test_factory_creates_isolated_site_and_registry_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            fixture_a = create_isolated_site_space_fixture(
                tmp_root,
                fixture_name="fixture-a",
                space_name="alpha",
            )
            fixture_b = create_isolated_site_space_fixture(
                tmp_root,
                fixture_name="fixture-b",
                space_name="beta",
            )

            self.assertNotEqual(fixture_a.fixture_root, fixture_b.fixture_root)
            self.assertNotEqual(fixture_a.site_path, fixture_b.site_path)
            self.assertNotEqual(fixture_a.registry_path, fixture_b.registry_path)
            self.assertTrue(fixture_a.registry_path.is_file())
            self.assertTrue(fixture_b.registry_path.is_file())

            resolved_alpha = resolve_space_root(fixture_a.registry_path, "alpha")
            resolved_beta = resolve_space_root(fixture_b.registry_path, "beta")
            self.assertEqual(resolved_alpha, fixture_a.space_root.resolve())
            self.assertEqual(resolved_beta, fixture_b.space_root.resolve())
            with self.assertRaises(KeyError):
                resolve_space_root(fixture_a.registry_path, "beta")
            with self.assertRaises(KeyError):
                resolve_space_root(fixture_b.registry_path, "alpha")


if __name__ == "__main__":
    unittest.main()
