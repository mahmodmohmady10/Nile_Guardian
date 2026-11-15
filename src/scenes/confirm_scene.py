"""نافذة تأكيد: Enter للموافقة، وEsc للإلغاء."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import ACCENT_COLOR, BOX_COLOR, TEXT_COLOR
from src.core.scene_stack import SceneStack
from src.engine.text_renderer import TextRenderer
from src.scenes.base_scene import BaseScene

PANEL = pygame.Rect(180, 200, 600, 170)


class ConfirmScene(BaseScene):
    def __init__(
        self,
        stack: SceneStack,
        renderer: TextRenderer,
        message: str,
        on_yes: Callable[[], None],
    ) -> None:
        self._stack = stack
        self._renderer = renderer
        self._message = message
        self._on_yes = on_yes

    def handle_action(self, action: str) -> None:
        if action == "confirm":
            self._stack.pop()
            self._on_yes()
        elif action == "cancel":
            self._stack.pop()

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, BOX_COLOR, PANEL)
        pygame.draw.rect(surface, ACCENT_COLOR, PANEL, width=2)
        text = self._renderer.render_line(self._message, 30, TEXT_COLOR)
        surface.blit(text, (PANEL.centerx - text.get_width() // 2, PANEL.y + 40))
        self.draw_text(surface, "ENTER: yes     ESC: no", (PANEL.x + 40, PANEL.bottom - 50),
                       ACCENT_COLOR, 24)
