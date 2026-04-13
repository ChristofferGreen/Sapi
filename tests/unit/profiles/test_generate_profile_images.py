from __future__ import annotations

import unittest
from types import SimpleNamespace

from scripts.generate_profile_images import (
    _dedupe_preserving_order,
    _extract_image_bytes,
    _resize_jpeg,
    _select_persona_rows,
)


class GenerateProfileImagesTests(unittest.TestCase):
    def test_select_persona_rows_defaults_to_all_rows(self) -> None:
        rows = [
            {"persona_id": "persona-a"},
            {"persona_id": "persona-b"},
        ]
        selected = _select_persona_rows(catalog_rows=rows, requested_persona_ids=[])
        self.assertEqual(selected, rows)

    def test_select_persona_rows_dedupes_and_preserves_request_order(self) -> None:
        rows = [
            {"persona_id": "persona-a"},
            {"persona_id": "persona-b"},
        ]
        selected = _select_persona_rows(
            catalog_rows=rows,
            requested_persona_ids=["persona-b", "persona-a", "persona-b"],
        )
        self.assertEqual([row["persona_id"] for row in selected], ["persona-b", "persona-a"])

    def test_select_persona_rows_rejects_unknown_ids(self) -> None:
        rows = [{"persona_id": "persona-a"}]
        with self.assertRaises(ValueError):
            _select_persona_rows(
                catalog_rows=rows,
                requested_persona_ids=["persona-missing"],
            )

    def test_dedupe_preserving_order_ignores_blanks(self) -> None:
        self.assertEqual(
            _dedupe_preserving_order(["persona-a", " ", "persona-b", "persona-a"]),
            ["persona-a", "persona-b"],
        )

    def test_extract_image_bytes_reads_first_generated_image_bytes(self) -> None:
        response = SimpleNamespace(
            generated_images=[
                SimpleNamespace(image=SimpleNamespace(image_bytes=b"jpeg-bytes")),
            ]
        )
        self.assertEqual(_extract_image_bytes(response=response), b"jpeg-bytes")

    def test_extract_image_bytes_fails_when_response_has_no_bytes(self) -> None:
        response = SimpleNamespace(generated_images=[SimpleNamespace(image=SimpleNamespace(image_bytes=None))])
        with self.assertRaises(RuntimeError):
            _extract_image_bytes(response=response)

    def test_resize_jpeg_produces_target_square_dimensions(self) -> None:
        try:
            from PIL import Image
        except ModuleNotFoundError:  # pragma: no cover
            self.skipTest("Pillow unavailable")
            return
        src = Image.new("RGB", (640, 480), color=(128, 64, 32))
        import io

        raw = io.BytesIO()
        src.save(raw, format="JPEG", quality=90)
        resized_bytes = _resize_jpeg(image_bytes=raw.getvalue(), side_px=128, quality=84)
        out = Image.open(io.BytesIO(resized_bytes))
        self.assertEqual(out.size, (128, 128))


if __name__ == "__main__":
    unittest.main()
