"""تحويل الصورة النصية إلى سطح pygame، مع تكبير البكسل وتكرار الزخرفة المحفوظة."""

from __future__ import annotations

import pygame

from src.utils.paths import resource_path
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


def fit_square(image: pygame.Surface, side: int) -> pygame.Surface:
    """يكبّر الصورة أو يصغّرها مع الحفاظ على نسبتها، ويضعها في مربع شفاف أسفله."""
    width, height = image.get_size()
    scale = side / max(width, height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    canvas = pygame.Surface((side, side), pygame.SRCALPHA)
    canvas.blit(pygame.transform.smoothscale(image, size), ((side - size[0]) // 2, side - size[1]))
    return canvas


def load_animal_surface(animal_id: str, side: int) -> pygame.Surface | None:
    """صورة الحيوان المقطّعة إن وُجدت، وإلا None فيُستخدم الرسم البكسلي."""
    path = resource_path("data", "images", "animals", f"{animal_id}.png")
    if not path.is_file():
        return None
    return fit_square(pygame.image.load(str(path)), side)
