#!/usr/bin/env python3
"""Generate repository-seeded persona profile images using Gemini API + Imagen."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any, Protocol
from io import BytesIO

_REPO_ROOT = Path(__file__).resolve().parents[1]

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from sapi.profiles.persona_catalog import load_seeded_persona_catalog


class _ImageGenerator(Protocol):
    def generate_jpeg(self, *, prompt: str, model: str) -> bytes:
        """Return one JPEG image for the provided prompt."""


class GeminiImagenGenerator:
    """Gemini API + Imagen image generator."""

    def __init__(self, *, api_key: str) -> None:
        try:
            from google import genai
        except ModuleNotFoundError as exc:  # pragma: no cover - exercised in script usage
            raise RuntimeError(
                "Missing dependency `google-genai`. Install it with: python3 -m pip install google-genai"
            ) from exc

        self._client = genai.Client(api_key=api_key)

    def generate_jpeg(self, *, prompt: str, model: str) -> bytes:
        response = self._client.models.generate_images(
            model=model,
            prompt=prompt,
            config={
                "numberOfImages": 1,
                "outputMimeType": "image/jpeg",
                "aspectRatio": "1:1",
                "personGeneration": "allow_adult",
            },
        )
        return _extract_image_bytes(response=response)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--persona-id",
        action="append",
        default=[],
        help="Persona id to generate (repeatable). Defaults to all catalog personas.",
    )
    parser.add_argument(
        "--model",
        default="imagen-4.0-generate-001",
        help="Gemini Imagen model id.",
    )
    parser.add_argument(
        "--profile-size",
        type=int,
        default=512,
        help="Square side length for canonical profile photo output.",
    )
    parser.add_argument(
        "--avatar-size",
        type=int,
        default=128,
        help="Square side length for companion avatar thumbnail output.",
    )
    parser.add_argument(
        "--api-key-env",
        default="GEMINI_API_KEY",
        help="Environment variable containing Gemini API key (fallback: GOOGLE_API_KEY).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned generation targets without API calls.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.profile_size < 128:
        print("--profile-size must be at least 128.", file=sys.stderr)
        return 2
    if args.avatar_size < 32:
        print("--avatar-size must be at least 32.", file=sys.stderr)
        return 2
    if args.avatar_size > args.profile_size:
        print("--avatar-size must be <= --profile-size.", file=sys.stderr)
        return 2

    catalog_rows = load_seeded_persona_catalog(repo_root=_REPO_ROOT, require_image_files=False)
    selected_rows = _select_persona_rows(
        catalog_rows=catalog_rows,
        requested_persona_ids=args.persona_id,
    )
    targets = [
        (
            str(row["persona_id"]),
            _REPO_ROOT / str(row["profile_image_path"]),
            _REPO_ROOT / str(row["profile_image_thumb_path"]),
            str(row["profile_image_prompt"]),
        )
        for row in selected_rows
    ]

    if args.dry_run:
        for persona_id, target_path, thumb_path, _prompt in targets:
            print(f"[dry-run] {persona_id} -> {target_path} (thumb: {thumb_path})")
        return 0

    try:
        api_key = _resolve_api_key(args.api_key_env)
        generator = GeminiImagenGenerator(api_key=api_key)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    generated = 0
    for persona_id, target_path, thumb_path, prompt in targets:
        if args.verbose:
            print(
                f"Generating {persona_id} with model {args.model} -> {target_path} (thumb: {thumb_path})",
                flush=True,
            )
        try:
            image_bytes = generator.generate_jpeg(prompt=prompt, model=args.model)
        except Exception as exc:  # pragma: no cover - exercised in live runs
            print(
                f"Image generation failed for persona {persona_id}: {exc}",
                file=sys.stderr,
            )
            return 1
        try:
            profile_jpeg = _resize_jpeg(image_bytes=image_bytes, side_px=args.profile_size, quality=88)
            avatar_jpeg = _resize_jpeg(image_bytes=image_bytes, side_px=args.avatar_size, quality=84)
        except Exception as exc:  # pragma: no cover - exercised in live runs
            print(
                f"Image resizing failed for persona {persona_id}: {exc}",
                file=sys.stderr,
            )
            return 1
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(profile_jpeg)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        thumb_path.write_bytes(avatar_jpeg)
        generated += 1

    print(
        f"Generated {generated} profile images with model {args.model} "
        f"(profile_size={args.profile_size}, avatar_size={args.avatar_size})."
    )
    return 0


def _resolve_api_key(primary_env_var: str) -> str:
    primary = os.environ.get(primary_env_var, "").strip()
    if primary:
        return primary
    fallback = os.environ.get("GOOGLE_API_KEY", "").strip()
    if fallback:
        return fallback
    raise RuntimeError(
        f"Missing API key. Set `{primary_env_var}` or `GOOGLE_API_KEY`."
    )


def _select_persona_rows(
    *,
    catalog_rows: list[dict[str, Any]],
    requested_persona_ids: list[str],
) -> list[dict[str, Any]]:
    if not requested_persona_ids:
        return list(catalog_rows)

    deduped_ids = _dedupe_preserving_order(requested_persona_ids)
    rows_by_id = {str(row["persona_id"]): row for row in catalog_rows}
    unknown = [persona_id for persona_id in deduped_ids if persona_id not in rows_by_id]
    if unknown:
        raise ValueError(
            "Unknown persona_id values requested via --persona-id: " + ", ".join(unknown)
        )
    return [rows_by_id[persona_id] for persona_id in deduped_ids]


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _extract_image_bytes(*, response: Any) -> bytes:
    generated_images = getattr(response, "generated_images", None)
    if not generated_images:
        generated_images = getattr(response, "images", None)
    if not generated_images:
        raise RuntimeError("Imagen response did not include generated images.")

    for generated in generated_images:
        image = getattr(generated, "image", None)
        if image is None:
            continue
        image_bytes = getattr(image, "image_bytes", None)
        if isinstance(image_bytes, (bytes, bytearray)) and image_bytes:
            return bytes(image_bytes)

    raise RuntimeError("Imagen response did not include image bytes.")


def _resize_jpeg(*, image_bytes: bytes, side_px: int, quality: int) -> bytes:
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised in script usage
        raise RuntimeError(
            "Missing dependency `Pillow`. Install it with: python3 -m pip install Pillow"
        ) from exc
    with Image.open(BytesIO(image_bytes)) as image:
        prepared = image.convert("RGB")
        resized = ImageOps.fit(prepared, (side_px, side_px), method=Image.Resampling.LANCZOS)
        output = BytesIO()
        resized.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()


if __name__ == "__main__":
    raise SystemExit(main())
