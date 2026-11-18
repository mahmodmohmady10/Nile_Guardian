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
from src.utils.paths import resource_path

PADDING = 24
PORTRAIT_MAX = 120
PORTRAIT_GAP = 16
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
        self._portrait = self._load_portrait(dialogue.portrait)
        self._renderer = renderer
        self._on_finish = on_finish

    @staticmethod
    def _load_portrait(relative: str | None) -> pygame.Surface | None:
        if relative is None:
            return None
        path = resource_path("data", "images", *relative.split("/"))
        return pygame.image.load(str(path)) if path.is_file() else None

    def handle_action(self, action: str) -> None:
        if action == "cancel":
            self._on_finish()
        elif action == "confirm" and self._state.advance():
            self._on_finish()

    def draw(self, surface: pygame.Surface) -> None:
        box = pygame.Rect(DIALOGUE_BOX)
        pygame.draw.rect(surface, BOX_COLOR, box)
        pygame.draw.rect(surface, ACCENT_COLOR, box, width=2)

        text_right = box.right - PADDING
        if self._portrait is not None:
            side = min(PORTRAIT_MAX, box.height - 2 * PADDING)
            portrait = pygame.transform.smoothscale(self._portrait, (side, side))
            portrait_x = box.right - PADDING - side
            surface.blit(portrait, (portrait_x, box.y + PADDING))
            text_right = portrait_x - PORTRAIT_GAP
        left_limit = box.x + PADDING
        max_width = text_right - left_limit

        speaker = self._renderer.render_line(
            self._state.speaker, DIALOGUE_SPEAKER_SIZE, ACCENT_COLOR
        )
        surface.blit(speaker, (text_right - speaker.get_width(), box.y + 14))

        def measure(text: str) -> int:
            return self._renderer.width(text, DIALOGUE_TEXT_SIZE)

        y = box.y + 14 + DIALOGUE_SPEAKER_SIZE + LINE_GAP
        for line in wrap_words(self._state.current, measure, max_width):
            rendered = self._renderer.render_line(line, DIALOGUE_TEXT_SIZE, TEXT_COLOR)
            surface.blit(rendered, (text_right - rendered.get_width(), y))
            y += DIALOGUE_TEXT_SIZE + LINE_GAP

        hint = f"ENTER: next   {self._state.index + 1}/{self._state.total}   ESC: skip"
        surface.blit(
            self._renderer.render_line(hint, 20, ACCENT_COLOR),
            (box.x + PADDING, box.bottom - 30),
        )
