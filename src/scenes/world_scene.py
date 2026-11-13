"""مشهد القرية: رسم الخريطة والأمين، والتفاعل مع الشخصيات بـ Enter أمام الشخصية."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from src.config import MOVE_SECONDS_PER_TILE, TEXT_COLOR, TILE_SIZE
from src.scenes.base_scene import BaseScene
from src.utils.data_loader import MapSpec, NpcSpec
from src.world.player_controller import DIRECTIONS, PlayerController
from src.world.tilemap import TileMap

PLAYER_COLOR = (250, 230, 120)
NPC_COLOR = (200, 120, 230)


class WorldScene(BaseScene):
    def __init__(
        self,
        spec: MapSpec,
        on_back: Callable[[], None],
        open_dialogue: Callable[[str], None],
    ) -> None:
        self._on_back = on_back
        self._open_dialogue = open_dialogue
        self._map = TileMap(spec.width, spec.height, spec.rows, spec.legend)
        self._npcs = spec.npcs
        self._npc_at: dict[tuple[int, int], NpcSpec] = {(n.x, n.y): n for n in spec.npcs}
        self._player = PlayerController(spec.spawn[0], spec.spawn[1], MOVE_SECONDS_PER_TILE)
        self._map_surface: pygame.Surface | None = None

    def set_held(self, held: tuple[str, ...]) -> None:
        self._player.set_held(held)

    def update(self, dt: float) -> None:
        self._player.update(dt, self._can_enter)

    def handle_action(self, action: str) -> None:
        if action == "cancel":
            self._on_back()
        elif action == "confirm":
            self._interact()

    def _interact(self) -> None:
        if self._player.is_moving:
            return
        dx, dy = DIRECTIONS[self._player.facing]
        npc = self._npc_at.get((self._player.x + dx, self._player.y + dy))
        if npc is not None:
            self._open_dialogue(npc.id)

    def draw(self, surface: pygame.Surface) -> None:
        if self._map_surface is None:
            self._map_surface = self._build_map_surface()
        surface.blit(self._map_surface, (0, 0))
        for npc in self._npcs:
            center = (npc.x * TILE_SIZE + TILE_SIZE // 2, npc.y * TILE_SIZE + TILE_SIZE // 2)
            pygame.draw.circle(surface, NPC_COLOR, center, TILE_SIZE // 3)
        px, py = self._player.visual_position()
        rect = pygame.Rect(
            round(px * TILE_SIZE) + 6, round(py * TILE_SIZE) + 6, TILE_SIZE - 12, TILE_SIZE - 12
        )
        pygame.draw.rect(surface, PLAYER_COLOR, rect)
        self.draw_text(surface, "ESC: menu   ENTER: talk", (10, 8), TEXT_COLOR, 24)

    def _can_enter(self, x: int, y: int) -> bool:
        return not self._map.is_solid(x, y) and (x, y) not in self._npc_at

    def _build_map_surface(self) -> pygame.Surface:
        surface = pygame.Surface((self._map.width * TILE_SIZE, self._map.height * TILE_SIZE))
        for y in range(self._map.height):
            for x in range(self._map.width):
                color = self._map.tile_at(x, y).color
                rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(surface, color, rect)
        return surface
