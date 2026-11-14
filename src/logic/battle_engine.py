"""محرك المعركة القائمة على الأدوار (توازن 0.7). بلا pygame.

- معركة واحدة ضد حيوان بري واحد، ويقاتل الرفيق الأول.
- الترتيب: مهارة «أولاً في الدور التالي» أولاً، وإلا الأسرع، والتعادل للاعب.
- الحيوان يتحسن مرة واحدة عند أقل من عتبته (الأسد)، قبل أن يتصرف.
- الخصم الذي ينسحب عند الضعف (الغزال) يُحسب فوزاً للاعب.
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
KIND_COUNTER = "counter"
KIND_NO_EFFECT = "no_effect"
KIND_HEAL = "heal"
KIND_LAST_STAND = "last_stand"
KIND_FAINT = "faint"
KIND_FLEE = "flee"
KIND_ENEMY_FLED = "enemy_fled"

OUTCOME_WON = "won"
OUTCOME_LOST = "lost"
OUTCOME_FLED = "fled"
OUTCOME_ENEMY_FLED = "enemy_fled"

ENEMY_SPECIAL_CHANCE = 0.3
EXTRA_EFFECT = "extra_damage"
HEAL_EFFECT = "heal_percent"
PRIORITY_EFFECT = "priority_next_turn"


@dataclass(frozen=True)
class BattleEvent:
    kind: str
    actor_name: str
    target_name: str
    move_name: str = ""
    amount: int = 0
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
            player_move = self._moves[self.player.template.basic_move]
        elif action == ACTION_SPECIAL:
            player_move = self._moves[self.player.template.special_move]
        else:
            raise ValueError(f"فعل غير معروف: {action}")
        enemy_move = self._moves[self._choose_enemy_move_id()]

        events: list[BattleEvent] = []
        acted: set[int] = set()
        for attacker, defender, move in self._ordered(player_move, enemy_move):
            if attacker.is_fainted:
                continue
            acted.add(id(attacker))
            events.extend(self._last_stand(attacker))
            events.extend(self._act(attacker, defender, move))
            if self.enemy.is_fainted:
                self.outcome = OUTCOME_WON
                break
            if self.player.is_fainted:
                self.outcome = OUTCOME_LOST
                break
            if self._enemy_fled():
                self.outcome = OUTCOME_ENEMY_FLED
                events.append(BattleEvent(KIND_ENEMY_FLED, self.enemy.name_ar, self.player.name_ar))
                break

        self.player.priority_next = (
            id(self.player) in acted and player_move.effect.kind == PRIORITY_EFFECT
        )
        self.enemy.priority_next = (
            id(self.enemy) in acted and enemy_move.effect.kind == PRIORITY_EFFECT
        )
        return events

    def _ordered(
        self, player_move: Move, enemy_move: Move
    ) -> list[tuple[AnimalInstance, AnimalInstance, Move]]:
        pair = [
            (self.player, self.enemy, player_move),
            (self.enemy, self.player, enemy_move),
        ]
        if self.player.priority_next != self.enemy.priority_next:
            player_first = self.player.priority_next
        else:
            player_first = self.player.template.speed >= self.enemy.template.speed
        return pair if player_first else [pair[1], pair[0]]

    def _choose_enemy_move_id(self) -> str:
        if self._rng.random() < ENEMY_SPECIAL_CHANCE:
            return self.enemy.template.special_move
        return self.enemy.template.basic_move

    def _last_stand(self, animal: AnimalInstance) -> list[BattleEvent]:
        rule = animal.template.last_stand
        if rule is None or animal.last_stand_used or animal.is_fainted:
            return []
        if animal.current_hp * 100 >= animal.max_hp * rule.threshold_percent:
            return []
        animal.last_stand_used = True
        bonus = animal.max_hp * rule.bonus_percent // 100
        animal.current_hp = min(animal.max_hp, animal.current_hp + bonus)
        return [BattleEvent(KIND_LAST_STAND, animal.name_ar, animal.name_ar, amount=bonus)]

    def _act(
        self, attacker: AnimalInstance, defender: AnimalInstance, move: Move
    ) -> list[BattleEvent]:
        effect = move.effect
        if effect.kind == HEAL_EFFECT:
            before = attacker.current_hp
            heal = attacker.max_hp * effect.percent // 100
            attacker.current_hp = min(attacker.max_hp, before + heal)
            healed = attacker.current_hp - before
            return [
                BattleEvent(KIND_HEAL, attacker.name_ar, attacker.name_ar, move.name_ar, healed)
            ]

        multiplier = effect.multiplier if effect.kind == EXTRA_EFFECT else 1.0
        result = compute_attack(attacker, defender, multiplier, self._rng)
        events: list[BattleEvent] = []
        if result.self_damage:
            attacker.current_hp = max(0, attacker.current_hp - result.self_damage)
            events.append(
                BattleEvent(KIND_COUNTER, attacker.name_ar, defender.name_ar, move.name_ar,
                            result.self_damage)
            )
            if attacker.is_fainted:
                events.append(BattleEvent(KIND_FAINT, attacker.name_ar, attacker.name_ar))
        if result.damage:
            defender.current_hp = max(0, defender.current_hp - result.damage)
            events.append(
                BattleEvent(KIND_ATTACK, attacker.name_ar, defender.name_ar, move.name_ar,
                            result.damage, result.critical)
            )
            if defender.is_fainted:
                events.append(BattleEvent(KIND_FAINT, attacker.name_ar, defender.name_ar))
        if not events:
            events.append(
                BattleEvent(KIND_NO_EFFECT, attacker.name_ar, defender.name_ar, move.name_ar)
            )
        return events

    def _enemy_fled(self) -> bool:
        threshold = self.enemy.template.flee_at_percent
        if threshold is None or self.enemy.is_fainted:
            return False
        return self.enemy.current_hp * 100 <= self.enemy.max_hp * threshold
