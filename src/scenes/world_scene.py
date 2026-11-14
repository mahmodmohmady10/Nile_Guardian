"""مشهد القرية: الخريطة والأمين، والأحداث، والتفاعل، ومواجهات الأعشاب."""

from __future__ import annotations

import random
from collections.abc import Callable

import pygame

from src.config import MOVE_SECONDS_PER_TILE, TEXT_COLOR, TILE_SIZE
from src.core.event_system import (
    ON_INTERACT,
    ON_MAP_ENTER,
    ON_STEP,
    EventRunner,
    Trigger,
    select_event,
)
from src.core.game_state import GameState
from src.logic.battle_engine import OUTCOME_LOST
from src.scenes.base_scene import BaseScene
from src.utils.data_loader import MapSpec, NpcSpec
from src.world.encounters import EncounterZone, roll_encounter
from src.world.player_controller import DIRECTIONS, PlayerController
from src.world.tilemap import TileMap

PLAYER_COLOR = (250, 230, 120)
NPC_COLOR = (200, 120, 230)


class WorldScene(BaseScene):
    def __init__(
        self,
        spec: MapSpec,
        state: GameState,
        on_back: Callable[[], None],
        open_dialogue: Callable[[str, Callable[[], None]], None],
        open_battle: Callable[[str, Callable[[str], None]], None],
        rng: random.Random,
    ) -> None:
        self._on_back = on_back
        self._open_dialogue = open_dialogue
        self._open_battle = open_battle
        self._rng = rng
        self._state = state
        self._events = spec.events
        self._zones: tuple[EncounterZone, ...] = spec.encounter_zones
        self._spawn = spec.spawn
        self._runner = EventRunner()
        self._waiting_for_dialogue = False
        self._map = TileMap(spec.width, spec.height, spec.rows, spec.legend)
        self._npcs = spec.npcs
        self._npc_at: dict[tuple[int, int], NpcSpec] = {(n.x, n.y): n for n in spec.npcs}
        self._player = PlayerController(spec.spawn[0], spec.spawn[1], MOVE_SECONDS_PER_TILE)
        self._map_surface: pygame.Surface | None = None
        state.grid_x, state.grid_y = spec.spawn

    def on_enter(self) -> None:
        self._trigger(Trigger(ON_MAP_ENTER))

    def set_held(self, held: tuple[str, ...]) -> None:
        self._player.set_held(held)

    def update(self, dt: float) -> None:
        if self._runner.busy:
            if not self._waiting_for_dialogue:
                command = self._runner.next_command()
                if command is not None:
                    self._waiting_for_dialogue = True
                    self._open_dialogue(command.dialogue_id, self._resume)
            return
        self._player.update(dt, self._can_enter)
        arrival = self._player.pop_arrival()
        if arrival is not None:
            x, y = arrival
            self._state.grid_x, self._state.grid_y = x, y
            self._state.facing = self._player.facing
            self._trigger(Trigger(ON_STEP, x=x, y=y))
            if not self._runner.busy:
                self._maybe_encounter(x, y)

    def handle_action(self, action: str) -> None:
        if self._runner.busy:
            return
        if action == "cancel":
            self._on_back()
        elif action == "confirm":
            self._interact()

    def _resume(self) -> None:
        self._waiting_for_dialogue = False

    def _trigger(self, trigger: Trigger) -> None:
        if self._runner.busy:
            return
        event = select_event(self._events, trigger, self._state)
        if event is not None:
            self._runner.start(event, self._state)

    def _interact(self) -> None:
        if self._player.is_moving:
            return
        dx, dy = DIRECTIONS[self._player.facing]
        npc = self._npc_at.get((self._player.x + dx, self._player.y + dy))
        if npc is not None:
            self._trigger(Trigger(ON_INTERACT, npc_id=npc.id))

    def _maybe_encounter(self, x: int, y: int) -> None:
        if self._state.lead() is None:
            return
        enemy_id = roll_encounter(self._zones, x, y, self._rng)
        if enemy_id is not None:
            self._open_battle(enemy_id, self._battle_ended)

    def _battle_ended(self, outcome: str) -> None:
        if outcome == OUTCOME_LOST:
            self._return_to_spawn()

    def _return_to_spawn(self) -> None:
        spawn_x, spawn_y = self._spawn
        self._player = PlayerController(spawn_x, spawn_y, MOVE_SECONDS_PER_TILE)
        self._state.grid_x, self._state.grid_y = spawn_x, spawn_y

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
