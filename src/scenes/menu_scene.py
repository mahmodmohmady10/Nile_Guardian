"""القائمة الرئيسية. تسميات لاتينية مؤقتة حتى M3."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.core.scene import Scene
from src.core.scene_stack import SceneStack
from src.scenes.base_scene import BaseScene

ITEMS = ("START", "QUIT")


class MenuScene(BaseScene):
    def __init__(self, stack: SceneStack, start_world: Callable[[], Scene]) -> None:
        self._stack = stack
        self._start_world = start_world
        self._index = 0

    @property
    def selected(self) -> str:
        return ITEMS[self._index]

    def handle_action(self, action: str) -> None:
        if action == "up":
            self._index = (self._index - 1) % len(ITEMS)
        elif action == "down":
            self._index = (self._index + 1) % len(ITEMS)
        elif action == "confirm":
            self._activate(self.selected)

    def _activate(self, item: str) -> None:
        if item == "START":
            self._stack.replace(self._start_world())
        elif item == "QUIT":
            self._stack.pop()

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_text(surface, "NILE GUARDIAN (M2)", (60, 60), ACCENT_COLOR, 52)
        for row, item in enumerate(ITEMS):
            marker = ">" if row == self._index else " "
            color = ACCENT_COLOR if row == self._index else TEXT_COLOR
            self.draw_text(surface, f"{marker} {item}", (80, 180 + row * 50), color, 40)
