"""مشهد مؤقت لـ M1، يُستبدل بالقرية في M2."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.scenes.base_scene import BaseScene


class PlaceholderScene(BaseScene):
    def __init__(self, on_back: Callable[[], None]) -> None:
        self._on_back = on_back

    def handle_action(self, action: str) -> None:
        if action == "cancel":
            self._on_back()

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_text(surface, "VILLAGE (M2)", (60, 60), ACCENT_COLOR, 48)
        self.draw_text(surface, "ESC: back to menu", (60, 130), TEXT_COLOR, 30)
