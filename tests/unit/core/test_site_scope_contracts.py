from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sapi.core.site_scope import (
    SPACE_SUBSPACES_SCHEMA_VERSION,
    SITE_SCOPE_SCHEMA_VERSION,
    load_site_scope,
    validate_subspaces_metadata_document,
    write_site_scope,
    write_subspaces_metadata,
)


class SiteScopeContractTests(unittest.TestCase):
    def test_site_scope_contract_is_validated_and_written_at_canonical_site_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            site_path.mkdir(parents=True)

            path = write_site_scope(site_path=site_path, site_name="My Site", site_root=".")
            self.assertEqual(path, site_path / "site.json")
            data = json.loads(path.read_text())
            self.assertEqual(data["schema_version"], SITE_SCOPE_SCHEMA_VERSION)
            self.assertEqual(data["site_name"], "My Site")
            self.assertEqual(data["site_root"], ".")

            loaded = load_site_scope(site_path=site_path)
            self.assertEqual(loaded.schema_version, SITE_SCOPE_SCHEMA_VERSION)
            self.assertEqual(loaded.site_name, "My Site")

    def test_subspace_metadata_contract_validates_duplicates_nesting_and_root_existence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            space_root = Path(tmp) / "spaces" / "alpha"
            (space_root / "sub-a").mkdir(parents=True, exist_ok=True)

            # Valid write path.
            path = write_subspaces_metadata(
                space_root=space_root,
                subspaces=[
                    {
                        "space_name": "sub-a",
                        "space_root": "sub-a",
                        "title": "Sub A",
                    }
                ],
            )
            self.assertEqual(path, space_root / "subspaces.json")
            payload = json.loads(path.read_text())
            self.assertEqual(payload["schema_version"], SPACE_SUBSPACES_SCHEMA_VERSION)

            # Duplicate names fail.
            with self.assertRaises(ValueError):
                validate_subspaces_metadata_document(
                    {
                        "schema_version": SPACE_SUBSPACES_SCHEMA_VERSION,
                        "subspaces": [
                            {"space_name": "sub-a", "space_root": "sub-a"},
                            {"space_name": "sub-a", "space_root": "sub-a"},
                        ],
                    },
                    space_root=space_root,
                )

            # Missing roots fail.
            with self.assertRaises(ValueError):
                validate_subspaces_metadata_document(
                    {
                        "schema_version": SPACE_SUBSPACES_SCHEMA_VERSION,
                        "subspaces": [{"space_name": "sub-b", "space_root": "missing"}],
                    },
                    space_root=space_root,
                )

            # Nested declarations fail.
            with self.assertRaises(ValueError):
                validate_subspaces_metadata_document(
                    {
                        "schema_version": SPACE_SUBSPACES_SCHEMA_VERSION,
                        "subspaces": [
                            {
                                "space_name": "sub-a",
                                "space_root": "sub-a",
                                "subspaces": [],
                            }
                        ],
                    },
                    space_root=space_root,
                )

    def test_compatibility_read_path_is_opt_in_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site_path = Path(tmp) / "site-a"
            space_root = site_path / "spaces" / "alpha"
            space_root.mkdir(parents=True)

            legacy_site_json = space_root / "site.json"
            legacy_site_json.write_text(
                json.dumps(
                    {
                        "schema_version": SITE_SCOPE_SCHEMA_VERSION,
                        "site_name": "Legacy Site",
                        "site_root": ".",
                    }
                )
                + "\n"
            )

            with self.assertRaises(FileNotFoundError):
                load_site_scope(site_path=site_path, space_root=space_root)

            loaded = load_site_scope(
                site_path=site_path,
                space_root=space_root,
                allow_legacy_space_scope_read=True,
            )
            self.assertEqual(loaded.site_name, "Legacy Site")


if __name__ == "__main__":
    unittest.main()
