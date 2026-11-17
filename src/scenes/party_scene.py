"""شاشة الفريق: قائمة الحيوانات، وبطاقة تعريف لكل حيوان مع مهاراته ومستواه."""

from __future__ import annotations

from collections.abc import Mapping

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.core.game_state import GameState
from src.core.scene_stack import SceneStack
from src.engine.text_renderer import TextRenderer
from src.logic.animal_card import build_card
from src.scenes.base_scene import BaseScene


class PartyScene(BaseScene):
    def __init__(
        self,
        stack: SceneStack,
        renderer: TextRenderer,
        state: GameState,
        move_names: Mapping[str, str],
    ) -> None:
        self._stack = stack
        self._renderer = renderer
        self._state = state
        self._move_names = dict(move_names)
        self._index = 0
        self._viewing = False
        self._message = ""

    def handle_action(self, action: str) -> None:
        if self._viewing:
            if action == "cancel":
                self._viewing = False
            elif action == "confirm":
                self._state.set_lead(self._index)
                self._index = 0
                self._message = f"{self._state.party[0].name_ar} هو قائد الفريق الآن."
                self._viewing = False
            return
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
            self._viewing = True

    def draw(self, surface: pygame.Surface) -> None:
        if not self._state.party:
            surface.blit(self._renderer.render_line("الفريق فارغ", 40, ACCENT_COLOR), (60, 60))
            return
        if self._viewing:
            self._draw_card(surface, self._state.party[self._index])
        else:
            self._draw_list(surface)

    def _draw_list(self, surface: pygame.Surface) -> None:
        surface.blit(self._renderer.render_line("الفريق", 46, ACCENT_COLOR), (60, 60))
        for row, animal in enumerate(self._state.party):
            selected = row == self._index
            color = ACCENT_COLOR if selected else TEXT_COLOR
            marker = "> " if selected else "  "
            lead_tag = " (القائد)" if row == 0 else ""
            label = f"{marker}{animal.name_ar} — المستوى {animal.level}{lead_tag}"
            surface.blit(self._renderer.render_line(label, 30, color), (80, 170 + row * 56))
        if self._message:
            surface.blit(self._renderer.render_line(self._message, 26, TEXT_COLOR), (80, 480))
        self.draw_text(surface, "ENTER: card     ESC: back", (80, 520), ACCENT_COLOR, 22)

    def _draw_card(self, surface: pygame.Surface, animal) -> None:  # type: ignore[no-untyped-def]
        card = build_card(animal, self._move_names)
        y = 50
        surface.blit(self._renderer.render_line(card.name_ar, 44, ACCENT_COLOR), (60, y))
        y += 60
        lines = [
            f"المستوى {card.level}   الخبرة {card.xp}"
            + (f" / {card.next_level_xp}" if card.next_level_xp else " (الحد الأقصى)"),
            f"الحيوية {card.current_hp:g} / {card.max_hp:g}",
            f"الهجوم {card.attack:g}   الدفاع {card.defense:g}   السرعة {card.speed}",
            "مُرقّى من المستشفى" if card.upgraded else "لم يُرقَّ بعد",
            "يمكن اصطياده" if card.catchable else "لا يمكن اصطياده",
        ]
        for line in lines:
            surface.blit(self._renderer.render_line(line, 26, TEXT_COLOR), (80, y))
            y += 38
        y += 12
        surface.blit(self._renderer.render_line("المهارات", 30, ACCENT_COLOR), (80, y))
        y += 40
        for skill in card.skills:
            status = "مفتوحة" if skill.unlocked else f"تُفتح عند المستوى {skill.level}"
            color = TEXT_COLOR if skill.unlocked else (120, 120, 130)
            surface.blit(self._renderer.render_line(f"• {skill.name_ar} — {status}", 24, color),
                         (100, y))
            y += 32
        hint = "ENTER: اجعله القائد     ESC: back"
        self.draw_text(surface, hint, (80, 540), ACCENT_COLOR, 22)
