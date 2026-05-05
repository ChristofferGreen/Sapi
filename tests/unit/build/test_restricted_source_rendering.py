from __future__ import annotations

import unittest

from sapi.build.site_builder import (
    _source_artifact_href,
    _source_file_href,
    _validate_source_access_policy,
)


class RestrictedSourceRenderingTests(unittest.TestCase):
    def test_restricted_source_hides_file_and_markdown_artifact_hrefs(self) -> None:
        source = {
            "source_id": "source-alpha",
            "access_policy": {
                "restricted": True,
                "public_download": False,
                "public_source_view": False,
            },
            "artifacts": {
                "source_file": "sources/artifacts/source-alpha/source.pdf",
                "source_markdown": "sources/artifacts/source-alpha/source.md",
                "source_extraction": "sources/artifacts/source-alpha/source_extraction.json",
            },
        }

        self.assertIsNone(_source_file_href(source=source, space_name="alpha"))
        self.assertIsNone(_source_artifact_href(source=source, artifact_key="source_file"))
        self.assertIsNone(_source_artifact_href(source=source, artifact_key="source_markdown"))
        self.assertIsNone(_source_artifact_href(source=source, artifact_key="source_extraction"))

    def test_malformed_access_policy_rejects_before_rendering(self) -> None:
        with self.assertRaisesRegex(ValueError, "public_download"):
            _validate_source_access_policy(
                {
                    "source_id": "source-alpha",
                    "access_policy": {
                        "restricted": True,
                        "public_download": "no",
                        "public_source_view": False,
                    },
                }
            )


if __name__ == "__main__":
    unittest.main()
