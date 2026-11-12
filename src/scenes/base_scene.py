"""قاعدة مشاهد pygame: خطوط مخزّنة ورسم نص لاتيني مؤقت.

ملاحظة M1: الخط الافتراضي لا يحمل العربية، فتسميات M1 لاتينية.
النص العربي يأتي مع TextRenderer في M3 (انظر ADR-001).
"""

from __future__ import annotations

import pygame

from src.core.scene import Scene

_FONT_CACHE: dict[int, pygame.font.Font] = {}


def get_font(size: int) -> pygame.font.Font:
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = pygame.font.Font(None, size)
    return _FONT_CACHE[size]


class BaseScene(Scene):
    def draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        pos: tuple[int, int],
        color: tuple[int, int, int],
        size: int = 36,
    ) -> None:
        surface.blit(get_font(size).render(text, True, color), pos)
