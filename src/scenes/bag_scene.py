"""الحقيبة خارج المعركة: عرض العناصر، واستخدام الشفاء على أي حيوان في الفريق."""

from __future__ import annotations

import pygame

from src.config import ACCENT_COLOR, TEXT_COLOR
from src.core.game_state import GameState
from src.core.scene_stack import SceneStack
from src.engine.text_renderer import TextRenderer
from src.logic.battle_engine import HEAL_ITEM_PERCENT
from src.logic.models import AnimalInstance, Item
from src.scenes.base_scene import BaseScene

ITEM_PHASE = "items"
MEMBER_PHASE = "members"


class BagScene(BaseScene):
    def __init__(
        self,
        stack: SceneStack,
        renderer: TextRenderer,
        state: GameState,
        items: dict[str, Item],
    ) -> None:
        self._stack = stack
        self._renderer = renderer
        self._state = state
        self._items = list(items.values())
        self._phase = ITEM_PHASE
        self._index = 0
        self._message = ""

    def handle_action(self, action: str) -> None:
        if self._phase == ITEM_PHASE:
            self._handle_items(action)
        else:
            self._handle_members(action)

    def _handle_items(self, action: str) -> None:
        if action == "up":
            self._index = (self._index - 1) % len(self._items)
        elif action == "down":
            self._index = (self._index + 1) % len(self._items)
        elif action == "confirm":
            item = self._items[self._index]
            if self._state.bag.get(item.id, 0) == 0:
                self._message = "لا تملك هذا العنصر."
            elif item.id != "heal":
                self._message = "يُستخدم هذا العنصر داخل المعركة فقط."
            elif not self._state.party:
                self._message = "لا يوجد حيوان في الفريق."
            else:
                self._phase = MEMBER_PHASE
                self._index = 0
                self._message = ""
        elif action == "cancel":
            self._stack.pop()

    def _handle_members(self, action: str) -> None:
        size = len(self._state.party)
        if action == "up":
            self._index = (self._index - 1) % size
        elif action == "down":
            self._index = (self._index + 1) % size
        elif action == "confirm":
            self._heal(self._state.party[self._index])
            self._phase = ITEM_PHASE
            self._index = 0
        elif action == "cancel":
            self._phase = ITEM_PHASE
            self._index = 0
            self._message = ""

    def _heal(self, animal: AnimalInstance) -> None:
        if animal.current_hp >= animal.max_hp:
            self._message = f"{animal.name_ar} بصحة كاملة."
            return
        heal = (animal.max_hp - animal.current_hp) * HEAL_ITEM_PERCENT // 100
        animal.current_hp += heal
        self._state.bag["heal"] -= 1
        if self._state.bag["heal"] <= 0:
            del self._state.bag["heal"]
        self._message = f"استعاد {animal.name_ar} {heal / 10:g} من الحيوية."

    def draw(self, surface: pygame.Surface) -> None:
        if self._phase == ITEM_PHASE:
            surface.blit(self._renderer.render_line("الحقيبة", 46, ACCENT_COLOR), (60, 60))
            for row, item in enumerate(self._items):
                selected = row == self._index
                color = ACCENT_COLOR if selected else TEXT_COLOR
                marker = "> " if selected else "  "
                count = self._state.bag.get(item.id, 0)
                label = f"{marker}{item.name_ar} ×{count}"
                surface.blit(self._renderer.render_line(label, 30, color), (80, 170 + row * 52))
        else:
            surface.blit(self._renderer.render_line("استخدم الشفاء على", 40, ACCENT_COLOR),
                         (60, 60))
            for row, animal in enumerate(self._state.party):
                selected = row == self._index
                color = ACCENT_COLOR if selected else TEXT_COLOR
                marker = "> " if selected else "  "
                hp = f"{animal.current_hp / 10:g}/{animal.max_hp / 10:g}"
                label = f"{marker}{animal.name_ar} — {hp}"
                surface.blit(self._renderer.render_line(label, 30, color), (80, 170 + row * 52))
        if self._message:
            surface.blit(self._renderer.render_line(self._message, 26, TEXT_COLOR), (80, 480))
        self.draw_text(surface, "ENTER: use     ESC: back", (80, 520), ACCENT_COLOR, 22)
