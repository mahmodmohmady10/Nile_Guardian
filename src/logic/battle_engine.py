"""محرك المعركة القائمة على الأدوار: مبادرة بالسرعة، وفعل واحد للاعب في كل دور. بلا pygame.

M5 يعرض معركة واحدة ضد حيوان بري واحد، والرفيق الأول هو الذي يقاتل.
الانسحاب ينجح دائماً في هذا الإصدار، وسيُضاف احتمال لاحقاً إن لزم.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass

from src.logic.damage import compute_attack
from src.logic.models import AnimalInstance, Move

ACTION_ATTACK = "attack"
ACTION_SPECIAL = "special"
ACTION_FLEE = "flee"

KIND_ATTACK = "attack"
KIND_MISS = "miss"
KIND_FAINT = "faint"
KIND_FLEE = "flee"

OUTCOME_WON = "won"
OUTCOME_LOST = "lost"
OUTCOME_FLED = "fled"

ENEMY_SPECIAL_CHANCE = 0.3


@dataclass(frozen=True)
class BattleEvent:
    kind: str
    actor_name: str
    target_name: str
    move_name: str = ""
    damage: int = 0
    critical: bool = False


class BattleEngine:
    def __init__(
        self,
        player: AnimalInstance,
        enemy: AnimalInstance,
        moves: Mapping[str, Move],
        rng: random.Random,
    ) -> None:
        self.player = player
        self.enemy = enemy
        self._moves = moves
        self._rng = rng
        self.outcome: str | None = None

    def turn(self, action: str) -> list[BattleEvent]:
        if self.outcome is not None:
            raise RuntimeError("المعركة انتهت")
        if action == ACTION_FLEE:
            self.outcome = OUTCOME_FLED
            return [BattleEvent(KIND_FLEE, self.player.name_ar, self.enemy.name_ar)]
        if action == ACTION_ATTACK:
            player_move_id = self.player.template.basic_move
        elif action == ACTION_SPECIAL:
            player_move_id = self.player.template.special_move
        else:
            raise ValueError(f"فعل غير معروف: {action}")

        enemy_move_id = self._choose_enemy_move_id()
        strikes = [
            (self.player, self.enemy, self._moves[player_move_id]),
            (self.enemy, self.player, self._moves[enemy_move_id]),
        ]
        if self.enemy.template.speed > self.player.template.speed:
            strikes.reverse()  # التعادل يمنح اللاعب الأسبقية

        events: list[BattleEvent] = []
        for attacker, defender, move in strikes:
            if attacker.is_fainted:
                continue
            events.extend(self._strike(attacker, defender, move))
            if defender.is_fainted:
                self.outcome = OUTCOME_WON if defender is self.enemy else OUTCOME_LOST
                break
        return events

    def _choose_enemy_move_id(self) -> str:
        roll = self._rng.random()
        if roll < ENEMY_SPECIAL_CHANCE:
            return self.enemy.template.special_move
        return self.enemy.template.basic_move

    def _strike(
        self, attacker: AnimalInstance, defender: AnimalInstance, move: Move
    ) -> list[BattleEvent]:
        result = compute_attack(attacker, defender, move, self._rng)
        if not result.hit:
            return [BattleEvent(KIND_MISS, attacker.name_ar, defender.name_ar, move.name_ar)]
        defender.current_hp = max(0, defender.current_hp - result.damage)
        events = [
            BattleEvent(
                KIND_ATTACK,
                attacker.name_ar,
                defender.name_ar,
                move.name_ar,
                result.damage,
                result.critical,
            )
        ]
        if defender.is_fainted:
            events.append(BattleEvent(KIND_FAINT, attacker.name_ar, defender.name_ar))
        return events
