"""شاشة المعركة: الأفعال، والتبديل، والاصطياد، والعناصر، والاستبدال، ونهاية المعركة."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.engine.text_renderer import TextRenderer
from src.logic.battle_engine import (
    ACTION_ATTACK,
    ACTION_CAPTURE,
    ACTION_ITEM,
    ACTION_SKILL,
    ACTION_SPECIAL,
    ACTION_SWITCH,
    OUTCOME_CAPTURED,
    OUTCOME_LOST,
    OUTCOME_WON,
    BattleEngine,
)
from src.logic.battle_text import describe_event
from src.logic.models import AnimalInstance
from src.scenes.base_scene import BaseScene

LABELS = {
    ACTION_ATTACK: "هجوم",
    ACTION_SPECIAL: "مهارة",
    ACTION_SWITCH: "تبديل",
    ACTION_CAPTURE: "اصطياد",
    ACTION_ITEM: "عنصر",
}
END_TEXT = {
    OUTCOME_WON: "انتصر الأمين!",
    OUTCOME_LOST: "سقط الفريق، وعاد الأمين إلى القرية.",
    OUTCOME_CAPTURED: "انضم الحيوان إلى فريقك!",
}
USABLE_ITEMS = ("heal", "power", "defense")
RESULT_FRAMES = 30
RESULT_STYLE = {
    OUTCOME_WON: ("انتصر الأمين!", (255, 215, 0)),
    OUTCOME_LOST: ("سقط الفريق", (230, 70, 70)),
    OUTCOME_CAPTURED: ("اصطدت الحيوان!", (190, 120, 255)),
}
PHASE_MENU = "menu"
PHASE_SWITCH = "switch"
PHASE_ITEM = "item"
PHASE_SKILL = "skill"
PHASE_LOG = "log"
PHASE_REPLACE = "replace"
PHASE_END = "end"
BG_COLOR = (18, 24, 32)
PANEL_COLOR = (14, 20, 30)
ENEMY_COLOR = (200, 90, 90)
ALLY_COLOR = (100, 200, 130)
BAR_BG_COLOR = (60, 60, 70)
BAR_WIDTH = 300


def _display(value: int) -> str:
    return f"{value / 10:g}"


class BattleScene(BaseScene):
    def __init__(
        self,
        engine: BattleEngine,
        renderer: TextRenderer,
        on_finish: Callable[[str], None],
        bag: dict[str, int],
        item_names: dict[str, str],
        move_names: dict[str, str],
    ) -> None:
        self._engine = engine
        self._move_names = move_names
        self._renderer = renderer
        self._on_finish = on_finish
        self._bag = bag
        self._item_names = item_names
        self._phase = PHASE_MENU
        self._index = 0
        self._candidates: list[int] = []
        self._items: list[str] = []
        self._skills: list[str] = []
        self._lines: list[str] = []
        self._note = ""
        self._frames = 0

    def _entries(self) -> list[str]:
        entries = [ACTION_ATTACK, ACTION_SPECIAL]
        if self._engine.can_switch():
            entries.append(ACTION_SWITCH)
        entries.append(ACTION_CAPTURE)
        if self._usable_items():
            entries.append(ACTION_ITEM)
        return entries

    def _usable_items(self) -> list[str]:
        return [
            item_id
            for item_id in USABLE_ITEMS
            if self._bag.get(item_id, 0) > 0 and self._engine.can_use_item(item_id)
        ]

    def handle_action(self, action: str) -> None:
        if self._phase == PHASE_MENU:
            self._handle_menu(action)
        elif self._phase == PHASE_SWITCH:
            self._handle_switch(action)
        elif self._phase == PHASE_ITEM:
            self._handle_item(action)
        elif self._phase == PHASE_SKILL:
            self._handle_skill(action)
        elif self._phase == PHASE_LOG and action == "confirm":
            self._after_log()
        elif self._phase == PHASE_REPLACE:
            self._handle_replace(action)
        elif self._phase == PHASE_END and action == "confirm":
            outcome = self._engine.outcome
            if outcome is not None:
                self._on_finish(outcome)

    def _enter_end(self) -> None:
        self._phase = PHASE_END
        self._frames = 0

    def _handle_menu(self, action: str) -> None:
        entries = self._entries()
        self._index %= len(entries)
        if action in ("up", "down"):
            self._note = ""
        if action == "up":
            self._index = (self._index - 1) % len(entries)
        elif action == "down":
            self._index = (self._index + 1) % len(entries)
        elif action == "confirm":
            chosen = entries[self._index]
            if chosen == ACTION_SWITCH:
                self._candidates = self._engine.switch_candidates()
                self._index = 0
                self._phase = PHASE_SWITCH
            elif chosen == ACTION_ITEM:
                self._items = self._usable_items()
                self._index = 0
                self._phase = PHASE_ITEM
            elif chosen == ACTION_CAPTURE and self._engine.capture_block_reason():
                self._note = self._engine.capture_block_reason() or ""
            elif chosen == ACTION_SPECIAL:
                self._skills = list(self._engine.player.available_skill_moves())
                self._index = 0
                self._phase = PHASE_SKILL
            else:
                self._play(chosen)

    def _handle_switch(self, action: str) -> None:
        if action == "up" and self._candidates:
            self._index = (self._index - 1) % len(self._candidates)
        elif action == "down" and self._candidates:
            self._index = (self._index + 1) % len(self._candidates)
        elif action == "confirm" and self._candidates:
            self._play(ACTION_SWITCH, self._candidates[self._index])
        elif action == "cancel":
            self._index = 0
            self._phase = PHASE_MENU

    def _handle_item(self, action: str) -> None:
        if action == "up" and self._items:
            self._index = (self._index - 1) % len(self._items)
        elif action == "down" and self._items:
            self._index = (self._index + 1) % len(self._items)
        elif action == "confirm" and self._items:
            item_id = self._items[self._index]
            self._consume(item_id)
            self._play(ACTION_ITEM, item_id)
        elif action == "cancel":
            self._index = 0
            self._phase = PHASE_MENU

    def _handle_skill(self, action: str) -> None:
        if action == "up" and self._skills:
            self._index = (self._index - 1) % len(self._skills)
        elif action == "down" and self._skills:
            self._index = (self._index + 1) % len(self._skills)
        elif action == "confirm" and self._skills:
            chosen = self._skills[self._index]
            if chosen == self._engine.player.template.special_move:
                self._play(ACTION_SPECIAL)
            else:
                self._play(ACTION_SKILL, chosen)
        elif action == "cancel":
            self._index = 0
            self._phase = PHASE_MENU

    def _consume(self, item_id: str) -> None:
        self._bag[item_id] -= 1
        if self._bag[item_id] <= 0:
            del self._bag[item_id]

    def _handle_replace(self, action: str) -> None:
        size = len(self._engine.party)
        if action == "up":
            self._index = (self._index - 1) % size
        elif action == "down":
            self._index = (self._index + 1) % size
        elif action == "confirm":
            self._engine.replace_member(self._index)
            self._enter_end()

    def _play(self, action: str, target: int | str | None = None) -> None:
        events = self._engine.turn(action, target)
        self._lines = [describe_event(event) for event in events]
        self._index = 0
        self._phase = PHASE_LOG

    def _after_log(self) -> None:
        if self._engine.outcome is None:
            self._index = 0
            self._phase = PHASE_MENU
        elif self._engine.needs_replacement():
            self._index = 0
            self._phase = PHASE_REPLACE
        else:
            self._enter_end()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BG_COLOR)
        self._draw_fighter(surface, self._engine.enemy, (560, 70), ENEMY_COLOR)
        self._draw_fighter(surface, self._engine.player, (70, 230), ALLY_COLOR)
        panel = pygame.Rect(40, 380, 880, 170)
        pygame.draw.rect(surface, PANEL_COLOR, panel)
        pygame.draw.rect(surface, ACCENT_COLOR, panel, width=2)
        if self._phase == PHASE_MENU:
            self._draw_options(surface, panel, [LABELS[a] for a in self._entries()])
            if self._note:
                note = self._renderer.render_line(self._note, 22, ACCENT_COLOR)
                surface.blit(note, (panel.x + 40, panel.bottom - 34))
        elif self._phase == PHASE_SWITCH:
            self._draw_options(surface, panel, [self._member_label(i) for i in self._candidates])
        elif self._phase == PHASE_ITEM:
            rows = [f"{self._item_names.get(i, i)} ×{self._bag.get(i, 0)}" for i in self._items]
            self._draw_options(surface, panel, rows)
        elif self._phase == PHASE_SKILL:
            rows = [self._move_names.get(move, move) for move in self._skills]
            self._draw_options(surface, panel, rows)
        elif self._phase == PHASE_REPLACE:
            rows = ["استبدل " + self._member_label(i) for i in range(len(self._engine.party))]
            self._draw_options(surface, panel, rows)
        else:
            self._draw_log(surface, panel)
        if self._phase == PHASE_END and self._engine.outcome in RESULT_STYLE:
            self._draw_result(surface, self._engine.outcome)

    def _draw_result(self, surface: pygame.Surface, outcome: str) -> None:
        self._frames = min(self._frames + 1, RESULT_FRAMES)
        progress = self._frames / RESULT_FRAMES
        veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        veil.fill((0, 0, 0, int(170 * progress)))
        surface.blit(veil, (0, 0))
        text, color = RESULT_STYLE[outcome]
        rendered = self._renderer.render_line(text, 72, color)
        rendered.set_alpha(int(255 * progress))
        x = surface.get_width() // 2 - rendered.get_width() // 2
        slide = int((1 - progress) * 40)
        y = surface.get_height() // 2 - rendered.get_height() // 2 - slide
        surface.blit(rendered, (x, y))
        if self._frames >= RESULT_FRAMES:
            hint = self._renderer.render_line("ENTER", 26, TEXT_COLOR)
            surface.blit(hint, (surface.get_width() // 2 - hint.get_width() // 2, y + 110))

    def _member_label(self, index: int) -> str:
        animal = self._engine.party[index]
        return f"{animal.name_ar} — {_display(max(0, animal.current_hp))}/{_display(animal.max_hp)}"

    def _draw_options(self, surface: pygame.Surface, panel: pygame.Rect, rows: list[str]) -> None:
        for row, label in enumerate(rows):
            color = ACCENT_COLOR if row == self._index else TEXT_COLOR
            marker = "> " if row == self._index else "  "
            surface.blit(
                self._renderer.render_line(marker + label, 26, color),
                (panel.x + 40, panel.y + 16 + row * 36),
            )

    def _draw_log(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        y = panel.y + 20
        for line in self._lines:
            rendered = self._renderer.render_line(line, 24, TEXT_COLOR)
            surface.blit(rendered, (panel.right - 30 - rendered.get_width(), y))
            y += 34
        outcome = self._engine.outcome
        if self._phase == PHASE_END and outcome is not None:
            text = END_TEXT[outcome]
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
        percent = max(0, round(animal.current_hp * 100 / animal.max_hp))
        self.draw_text(
            surface,
            f"HP {_display(max(0, animal.current_hp))}/{_display(animal.max_hp)} ({percent}%)",
            (x, y + 64),
            TEXT_COLOR,
            22,
        )
