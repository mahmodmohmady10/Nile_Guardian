"""القائمة الرئيسية: عناصر تتغير حسب حالة اللعبة."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.core.scene_stack import SceneStack
from src.engine.text_renderer import TextRenderer
from src.scenes.base_scene import BaseScene

MenuItems = list[tuple[str, Callable[[], None]]]


class MenuScene(BaseScene):
    def __init__(
        self, stack: SceneStack, renderer: TextRenderer, items: Callable[[], MenuItems]
    ) -> None:
        self._stack = stack
        self._renderer = renderer
        self._items = items
        self._index = 0

    def handle_action(self, action: str) -> None:
        entries = self._items()
        if not entries:
            return
        self._index %= len(entries)
        if action == "up":
            self._index = (self._index - 1) % len(entries)
        elif action == "down":
            self._index = (self._index + 1) % len(entries)
        elif action == "confirm":
            entries[self._index][1]()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._renderer.render_line("حارس النيل", 52, ACCENT_COLOR), (60, 60))
        for row, (label, _action) in enumerate(self._items()):
            selected = row == self._index
            color = ACCENT_COLOR if selected else TEXT_COLOR
            marker = "> " if selected else "  "
            surface.blit(
                self._renderer.render_line(marker + label, 36, color), (80, 170 + row * 52)
            )
