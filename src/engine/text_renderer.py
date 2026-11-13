"""رسم النص العربي واللاتيني (ADR-001).

- المقاطع العربية تُرسم بالمحرك المدمج في pygame-ce باتجاه RTL.
- المقاطع اللاتينية والأرقام تُرسم بخط عادي من اليسار إلى اليمين.
- الأسطر المرسومة تُخزَّن في LRU Cache، فلا يُعاد التشكيل في كل إطار (NFR-02).
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import pygame

from src.core.text_layout import AR, split_runs

Color = tuple[int, int, int]


class TextRenderer:
    def __init__(self, font_path: Path, cache_size: int) -> None:
        self._font_path = font_path
        self._cache_size = cache_size
        self._fonts: dict[int, tuple[pygame.font.Font, pygame.font.Font]] = {}
        self._cache: OrderedDict[tuple[str, int, Color], pygame.Surface] = OrderedDict()

    def _fonts_for(self, size: int) -> tuple[pygame.font.Font, pygame.font.Font]:
        """(خط عربي RTL، خط لاتيني عادي) لحجم معيّن."""
        if size not in self._fonts:
            arabic = pygame.font.Font(str(self._font_path), size)
            latin = pygame.font.Font(str(self._font_path), size)
            try:
                arabic.set_direction(pygame.DIRECTION_RTL)
                arabic.set_script("Arab")
            except (AttributeError, pygame.error) as exc:
                raise RuntimeError(
                    "المحرك المدمج لا يدعم RTL في هذه النسخة من pygame-ce"
                ) from exc
            self._fonts[size] = (arabic, latin)
        return self._fonts[size]

    def width(self, text: str, size: int) -> int:
        arabic, latin = self._fonts_for(size)
        return sum(
            (arabic if run.kind == AR else latin).size(run.text)[0] for run in split_runs(text)
        )

    def render_line(self, text: str, size: int, color: Color) -> pygame.Surface:
        key = (text, size, color)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        surface = self._build_line(text, size, color)
        self._cache[key] = surface
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return surface

    def _build_line(self, text: str, size: int, color: Color) -> pygame.Surface:
        arabic, latin = self._fonts_for(size)
        pieces: list[pygame.Surface] = []
        for run in split_runs(text):
            font = arabic if run.kind == AR else latin
            pieces.append(font.render(run.text, True, color))
        height = max(arabic.get_height(), latin.get_height())
        total = sum(piece.get_width() for piece in pieces)
        surface = pygame.Surface((max(total, 1), height), pygame.SRCALPHA)
        # الترتيب المنطقي من اليسار، والعرض RTL: أول مقطع يقع في أقصى اليمين.
        x = total
        for piece in pieces:
            x -= piece.get_width()
            surface.blit(piece, (x, 0))
        return surface
