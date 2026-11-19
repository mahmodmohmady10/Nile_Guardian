"""مستشفى المدينة: ترقية الحيوانات التي بلغت 10 نقاط خبرة. Enter للترقية، وEsc للخروج."""

from __future__ import annotations

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.core.game_state import GameState
from src.core.hospital import try_upgrade
from src.core.scene_stack import SceneStack
from src.engine.audio import AudioManager
from src.engine.text_renderer import TextRenderer
from src.logic.models import UPGRADE_PRICE
from src.scenes.base_scene import BaseScene


class HospitalScene(BaseScene):
    def __init__(
        self,
        stack: SceneStack,
        renderer: TextRenderer,
        state: GameState,
        audio: AudioManager | None = None,
    ) -> None:
        self._audio = audio
        self._stack = stack
        self._renderer = renderer
        self._state = state
        self._index = 0
        self._message = ""

    def handle_action(self, action: str) -> None:
        size = len(self._state.party)
        if action == "cancel":
            self._stack.pop()
        elif size == 0:
            return
        elif action == "up":
            self._index = (self._index - 1) % size
        elif action == "down":
            self._index = (self._index + 1) % size
        elif action == "confirm":
            animal = self._state.party[self._index]
            was_upgraded = animal.upgraded
            self._message = try_upgrade(self._state, animal)
            if self._audio is not None and animal.upgraded and not was_upgraded:
                self._audio.play_sfx("upgrade")

    def draw(self, surface: pygame.Surface) -> None:
        title = f"مستشفى المدينة — الترقية {UPGRADE_PRICE} — النقود: {self._state.money}"
        surface.blit(self._renderer.render_line(title, 34, ACCENT_COLOR), (60, 60))
        for row, animal in enumerate(self._state.party):
            selected = row == self._index
            color = ACCENT_COLOR if selected else TEXT_COLOR
            marker = "> " if selected else "  "
            if animal.upgraded:
                status = "مُرقّى"
            elif animal.can_upgrade:
                status = "جاهز للترقية"
            else:
                status = f"خبرة {animal.xp}/10"
            label = f"{marker}{animal.name_ar} — المستوى {animal.level} — {status}"
            surface.blit(self._renderer.render_line(label, 28, color), (80, 170 + row * 52))
        if self._message:
            surface.blit(self._renderer.render_line(self._message, 26, TEXT_COLOR), (80, 480))
        self.draw_text(surface, "ENTER: upgrade     ESC: leave", (80, 520), ACCENT_COLOR, 22)
