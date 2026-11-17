"""تحويل الصورة النصية إلى سطح pygame، مع تكبير البكسل وتكرار الزخرفة المحفوظة."""

from __future__ import annotations

import pygame

from src.utils.sprites import SPRITE_SIZE, SpriteSpec, shaded_pixels

SPRITE_SCALE = 6


def build_surface(spec: SpriteSpec, scale: int = SPRITE_SCALE) -> pygame.Surface:
    size = SPRITE_SIZE * scale
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pixels = shaded_pixels(spec)
    for y, row in enumerate(pixels):
        for x, color in enumerate(row):
            if color is None:
                continue
            surface.fill((*color, 255), (x * scale, y * scale, scale, scale))
    return surface


def flashed(surface: pygame.Surface) -> pygame.Surface:
    """نسخة أفتح للومضة البيضاء عند الإصابة."""
    copy = surface.copy()
    copy.fill((110, 110, 110, 0), special_flags=pygame.BLEND_RGB_ADD)
    return copy
