"""شاشة الخانات: حفظ أو تحميل. Enter للاختيار، وEsc للرجوع."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.core.scene_stack import SceneStack
from src.engine.text_renderer import TextRenderer
from src.scenes.base_scene import BaseScene

SLOT_LABELS = {
    "slot1": "الخانة 1",
    "slot2": "الخانة 2",
    "slot3": "الخانة 3",
    "autosave": "التلقائي",
}


class SlotScene(BaseScene):
    def __init__(
        self,
        stack: SceneStack,
        renderer: TextRenderer,
        title: str,
        slots: tuple[str, ...],
        describe: Callable[[str], str],
        on_choose: Callable[[str], None],
    ) -> None:
        self._stack = stack
        self._renderer = renderer
        self._title = title
        self._slots = slots
        self._describe = describe
        self._on_choose = on_choose
        self._index = 0

    def handle_action(self, action: str) -> None:
        if action == "up":
            self._index = (self._index - 1) % len(self._slots)
        elif action == "down":
            self._index = (self._index + 1) % len(self._slots)
        elif action == "confirm":
            self._on_choose(self._slots[self._index])
        elif action == "cancel":
            self._stack.pop()

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._renderer.render_line(self._title, 46, ACCENT_COLOR), (60, 60))
        for row, slot in enumerate(self._slots):
            selected = row == self._index
            color = ACCENT_COLOR if selected else TEXT_COLOR
            label = SLOT_LABELS.get(slot, slot) + " — " + self._describe(slot)
            marker = "> " if selected else "  "
            surface.blit(
                self._renderer.render_line(marker + label, 28, color), (80, 170 + row * 62)
            )
