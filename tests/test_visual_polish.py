"""اختبارات جودة الصور: التظليل الآلي، ومقاس الصورة الثابت."""

from __future__ import annotations

from src.utils.sprites import SPRITE_SIZE, SpriteSpec, shaded_pixels


def block_sprite() -> SpriteSpec:
    return SpriteSpec({"K": (100, 100, 100)}, tuple("K" * SPRITE_SIZE for _ in range(SPRITE_SIZE)))


def test_top_edge_is_lighter_than_base() -> None:
    pixels = shaded_pixels(block_sprite())
    assert pixels[0][5] is not None and pixels[0][5][0] > 100


def test_bottom_edge_is_darker_than_base() -> None:
    pixels = shaded_pixels(block_sprite())
    assert pixels[SPRITE_SIZE - 1][5] is not None and pixels[SPRITE_SIZE - 1][5][0] < 100


def test_interior_keeps_base_color() -> None:
    pixels = shaded_pixels(block_sprite())
    assert pixels[SPRITE_SIZE // 2][SPRITE_SIZE // 2] == (100, 100, 100)


def test_transparent_stays_transparent() -> None:
    spec = SpriteSpec({"K": (1, 2, 3)}, tuple("." * SPRITE_SIZE for _ in range(SPRITE_SIZE)))
    assert all(pixel is None for row in shaded_pixels(spec) for pixel in row)
