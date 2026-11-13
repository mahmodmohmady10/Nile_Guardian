"""نافذة حوار سفلية فوق الخريطة. Enter يتقدم، وEsc يتخطى."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import (
    ACCENT_COLOR,
    BOX_COLOR,
    DIALOGUE_BOX,
    DIALOGUE_SPEAKER_SIZE,
    DIALOGUE_TEXT_SIZE,
    TEXT_COLOR,
)
from src.core.dialogue import DialogueState
from src.core.text_layout import wrap_words
from src.engine.text_renderer import TextRenderer
from src.scenes.base_scene import BaseScene
from src.utils.data_loader import Dialogue

PADDING = 24
LINE_GAP = 10


class DialogueScene(BaseScene):
    opaque = False  # تُرسم الخريطة تحت الصندوق

    def __init__(
        self,
        dialogue: Dialogue,
        renderer: TextRenderer,
        on_finish: Callable[[], None],
    ) -> None:
        self._state = DialogueState(dialogue.speaker, dialogue.lines)
        self._renderer = renderer
        self._on_finish = on_finish

    def handle_action(self, action: str) -> None:
        if action == "cancel":
            self._on_finish()
        elif action == "confirm" and self._state.advance():
            self._on_finish()

    def draw(self, surface: pygame.Surface) -> None:
        box = pygame.Rect(DIALOGUE_BOX)
        pygame.draw.rect(surface, BOX_COLOR, box)
        pygame.draw.rect(surface, ACCENT_COLOR, box, width=2)

        speaker = self._renderer.render_line(
            self._state.speaker, DIALOGUE_SPEAKER_SIZE, ACCENT_COLOR
        )
        surface.blit(speaker, (box.right - PADDING - speaker.get_width(), box.y + 14))

        max_width = box.width - 2 * PADDING

        def measure(text: str) -> int:
            return self._renderer.width(text, DIALOGUE_TEXT_SIZE)

        y = box.y + 14 + DIALOGUE_SPEAKER_SIZE + LINE_GAP
        for line in wrap_words(self._state.current, measure, max_width):
            rendered = self._renderer.render_line(line, DIALOGUE_TEXT_SIZE, TEXT_COLOR)
            surface.blit(rendered, (box.right - PADDING - rendered.get_width(), y))
            y += DIALOGUE_TEXT_SIZE + LINE_GAP

        hint = f"ENTER: next   {self._state.index + 1}/{self._state.total}   ESC: skip"
        surface.blit(
            self._renderer.render_line(hint, 20, ACCENT_COLOR),
            (box.x + PADDING, box.bottom - 30),
        )
