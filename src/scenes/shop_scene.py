"""متجر المدينة: شراء العناصر بالنقود. Enter للشراء، وEsc للخروج."""

from __future__ import annotations

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.core.game_state import GameState
from src.core.scene_stack import SceneStack
from src.engine.text_renderer import TextRenderer
from src.logic.models import Item
from src.scenes.base_scene import BaseScene


class ShopScene(BaseScene):
    def __init__(
        self,
        stack: SceneStack,
        renderer: TextRenderer,
        state: GameState,
        items: list[Item],
    ) -> None:
        self._stack = stack
        self._renderer = renderer
        self._state = state
        self._items = items
        self._index = 0
        self._message = ""

    def handle_action(self, action: str) -> None:
        if action == "up":
            self._index = (self._index - 1) % len(self._items)
        elif action == "down":
            self._index = (self._index + 1) % len(self._items)
        elif action == "confirm":
            self._buy(self._items[self._index])
        elif action == "cancel":
            self._stack.pop()

    def _buy(self, item: Item) -> None:
        if self._state.spend(item.price):
            self._state.add_item(item.id)
            self._message = f"تم شراء {item.name_ar}."
        else:
            self._message = "النقود غير كافية."

    def draw(self, surface: pygame.Surface) -> None:
        title = f"متجر المدينة — النقود: {self._state.money}"
        surface.blit(self._renderer.render_line(title, 40, ACCENT_COLOR), (60, 60))
        for row, item in enumerate(self._items):
            selected = row == self._index
            color = ACCENT_COLOR if selected else TEXT_COLOR
            marker = "> " if selected else "  "
            label = f"{marker}{item.name_ar} — {item.price}"
            surface.blit(self._renderer.render_line(label, 32, color), (80, 170 + row * 56))
        if self._message:
            surface.blit(
                self._renderer.render_line(self._message, 26, TEXT_COLOR),
                (80, 170 + len(self._items) * 56 + 20),
            )
        self.draw_text(surface, "ENTER: buy     ESC: leave", (80, 520), ACCENT_COLOR, 22)
