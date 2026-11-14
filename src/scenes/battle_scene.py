"""شاشة المعركة: اختيار الفعل، وعرض السجل، ونهاية المعركة."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.engine.text_renderer import TextRenderer
from src.logic.battle_engine import (
    ACTION_ATTACK,
    ACTION_FLEE,
    ACTION_SPECIAL,
    OUTCOME_FLED,
    OUTCOME_LOST,
    OUTCOME_WON,
    BattleEngine,
)
from src.logic.battle_text import describe_event
from src.logic.models import AnimalInstance
from src.scenes.base_scene import BaseScene

MENU_ITEMS = (("هجوم", ACTION_ATTACK), ("مهارة", ACTION_SPECIAL), ("انسحاب", ACTION_FLEE))
END_TEXT = {
    OUTCOME_WON: "انتصر الأمين!",
    OUTCOME_LOST: "تراجع الرفيق، وعاد الأمين إلى القرية.",
    OUTCOME_FLED: "انسحب الأمين من المعركة.",
}
PHASE_MENU = "menu"
PHASE_LOG = "log"
PHASE_END = "end"
BG_COLOR = (18, 24, 32)
PANEL_COLOR = (14, 20, 30)
ENEMY_COLOR = (200, 90, 90)
ALLY_COLOR = (100, 200, 130)
BAR_BG_COLOR = (60, 60, 70)
BAR_WIDTH = 300


class BattleScene(BaseScene):
    def __init__(
        self,
        engine: BattleEngine,
        renderer: TextRenderer,
        on_finish: Callable[[str], None],
    ) -> None:
        self._engine = engine
        self._renderer = renderer
        self._on_finish = on_finish
        self._phase = PHASE_MENU
        self._index = 0
        self._lines: list[str] = []

    def handle_action(self, action: str) -> None:
        if self._phase == PHASE_MENU:
            self._handle_menu(action)
        elif self._phase == PHASE_LOG and action == "confirm":
            self._phase = PHASE_END if self._engine.outcome is not None else PHASE_MENU
        elif self._phase == PHASE_END and action == "confirm":
            outcome = self._engine.outcome
            if outcome is not None:
                self._on_finish(outcome)

    def _handle_menu(self, action: str) -> None:
        if action == "up":
            self._index = (self._index - 1) % len(MENU_ITEMS)
        elif action == "down":
            self._index = (self._index + 1) % len(MENU_ITEMS)
        elif action == "confirm":
            events = self._engine.turn(MENU_ITEMS[self._index][1])
            self._lines = [describe_event(event) for event in events]
            self._phase = PHASE_LOG

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BG_COLOR)
        self._draw_fighter(surface, self._engine.enemy, (560, 70), ENEMY_COLOR)
        self._draw_fighter(surface, self._engine.player, (70, 230), ALLY_COLOR)
        panel = pygame.Rect(40, 380, 880, 170)
        pygame.draw.rect(surface, PANEL_COLOR, panel)
        pygame.draw.rect(surface, ACCENT_COLOR, panel, width=2)
        if self._phase == PHASE_MENU:
            self._draw_menu(surface, panel)
        else:
            self._draw_log(surface, panel)

    def _draw_menu(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        for row, (label, _action) in enumerate(MENU_ITEMS):
            color = ACCENT_COLOR if row == self._index else TEXT_COLOR
            rendered = self._renderer.render_line(label, 30, color)
            surface.blit(rendered, (panel.x + 40, panel.y + 20 + row * 42))

    def _draw_log(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        y = panel.y + 20
        for line in self._lines:
            rendered = self._renderer.render_line(line, 24, TEXT_COLOR)
            surface.blit(rendered, (panel.right - 30 - rendered.get_width(), y))
            y += 34
        if self._phase == PHASE_END and self._engine.outcome is not None:
            text = END_TEXT[self._engine.outcome]
            rendered = self._renderer.render_line(text, 28, ACCENT_COLOR)
            surface.blit(rendered, (panel.right - 30 - rendered.get_width(), y + 4))
        self.draw_text(surface, "ENTER", (panel.x + 30, panel.bottom - 34), ACCENT_COLOR, 22)

    def _draw_fighter(
        self,
        surface: pygame.Surface,
        animal: AnimalInstance,
        position: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        x, y = position
        name = self._renderer.render_line(animal.name_ar, 30, TEXT_COLOR)
        surface.blit(name, (x, y))
        pygame.draw.rect(surface, BAR_BG_COLOR, (x, y + 42, BAR_WIDTH, 16))
        ratio = max(0.0, animal.current_hp / animal.max_hp)
        pygame.draw.rect(surface, color, (x, y + 42, int(BAR_WIDTH * ratio), 16))
        self.draw_text(
            surface, f"HP {max(0, animal.current_hp)}/{animal.max_hp}", (x, y + 64), TEXT_COLOR, 22
        )
