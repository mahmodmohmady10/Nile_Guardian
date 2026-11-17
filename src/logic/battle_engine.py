"""محرك المعركة: فريق من حتى 3 حيوانات، وتبديل يستهلك الدور، واصطياد. بلا pygame.

- الحيوان النشط يقاتل، ويدخل الحيوان الحي التالي تلقائياً عند سقوط النشط (دون استهلاك دور).
- الخسارة تحدث حين يسقط الفريق كله.
- الاصطياد متاح عند 10% أو أقل من صحة الخصم، وليس للأسد.
- التبديل يستهلك الدور، ويهاجم الخصم الحيوان الداخل.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, MutableSequence
from dataclasses import dataclass

from src.logic.damage import compute_attack
from src.logic.models import MAX_PARTY_SIZE, AnimalInstance, Move

ACTION_ATTACK = "attack"
ACTION_SPECIAL = "special"
ACTION_FLEE = "flee"
ACTION_SWITCH = "switch"
ACTION_CAPTURE = "capture"
ACTION_ITEM = "item"
ACTION_SKILL = "skill"

KIND_ATTACK = "attack"
KIND_COUNTER = "counter"
KIND_NO_EFFECT = "no_effect"
KIND_HEAL = "heal"
KIND_LAST_STAND = "last_stand"
KIND_FAINT = "faint"
KIND_FLEE = "flee"
KIND_ENEMY_FLED = "enemy_fled"
KIND_SWITCH = "switch"
KIND_AUTO_SWITCH = "auto_switch"
KIND_CAPTURED = "captured"
KIND_CAPTURE_FAILED = "capture_failed"
KIND_ITEM_HEAL = "item_heal"
KIND_ITEM_POWER = "item_power"
KIND_ITEM_DEFENSE = "item_defense"

OUTCOME_WON = "won"
OUTCOME_LOST = "lost"
OUTCOME_FLED = "fled"
OUTCOME_ENEMY_FLED = "enemy_fled"
OUTCOME_CAPTURED = "captured"

ENEMY_SPECIAL_CHANCE = 0.3
CAPTURE_THRESHOLD_PERCENT = 10
CAPTURE_CHANCE = 0.5
EXTRA_EFFECT = "extra_damage"
HEAL_EFFECT = "heal_percent"
PRIORITY_EFFECT = "priority_next_turn"
HEAL_ITEM_PERCENT = 50
POWER_MULTIPLIER = 5.0
DEFENSE_BOOST = 1.5


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
        party: MutableSequence[AnimalInstance],
        enemy: AnimalInstance,
        moves: Mapping[str, Move],
        rng: random.Random,
    ) -> None:
        if len(party) > MAX_PARTY_SIZE:
            raise ValueError("الفريق أكبر من الحد المسموح")
        active = next((i for i, animal in enumerate(party) if not animal.is_fainted), None)
        if active is None:
            raise ValueError("لا يوجد حيوان حي في الفريق")
        self.party = party  # المرجع نفسه، فتنعكس التغييرات على حالة اللعبة
        self.enemy = enemy
        self._moves = moves
        self._rng = rng
        self._active = active
        self.outcome: str | None = None
        self.captured: AnimalInstance | None = None
        self._power_armed: set[int] = set()
        self._defense_boosted: set[int] = set()

    @property
    def player(self) -> AnimalInstance:
        return self.party[self._active]

    def switch_candidates(self) -> list[int]:
        return [
            i
            for i, animal in enumerate(self.party)
            if i != self._active and not animal.is_fainted
        ]

    def can_switch(self) -> bool:
        return self.outcome is None and bool(self.switch_candidates())

    def can_capture(self) -> bool:
        return (
            self.outcome is None
            and self.enemy.template.catchable
            and not self.enemy.is_fainted
            and self.enemy.current_hp * 100 <= self.enemy.max_hp * CAPTURE_THRESHOLD_PERCENT
        )

    def capture_block_reason(self) -> str | None:
        """سبب تعذر الاصطياد الآن، أو None إن كان متاحاً."""
        if self.outcome is not None:
            return "المعركة انتهت."
        if not self.enemy.template.catchable:
            return "هذا الحيوان لا يمكن اصطياده."
        if self.enemy.is_fainted or not self.can_capture():
            return "الاصطياد ممكن عندما تصل صحة الخصم إلى 10% أو أقل."
        return None

    def needs_replacement(self) -> bool:
        return self.outcome == OUTCOME_CAPTURED and len(self.party) >= MAX_PARTY_SIZE

    def replace_member(self, index: int) -> None:
        if not self.needs_replacement():
            raise RuntimeError("لا حاجة لاستبدال حيوان الآن")
        if not 0 <= index < len(self.party):
            raise ValueError("اختيار غير صالح")
        if self.captured is None:
            raise RuntimeError("لا يوجد حيوان مُصطاد")
        self.party[index] = self.captured

    def turn(self, action: str, target: int | str | None = None) -> list[BattleEvent]:
        if self.outcome is not None:
            raise RuntimeError("المعركة انتهت")
        if action == ACTION_FLEE:
            self.outcome = OUTCOME_FLED
            return [BattleEvent(KIND_FLEE, self.player.name_ar, self.enemy.name_ar)]
        if action == ACTION_SWITCH:
            return self._switch(target)
        if action == ACTION_CAPTURE:
            return self._capture()
        if action == ACTION_ITEM:
            return self._use_item(target)
        if action == ACTION_ATTACK:
            player_move = self._moves[self.player.template.basic_move]
        elif action == ACTION_SPECIAL:
            player_move = self._moves[self.player.template.special_move]
        elif action == ACTION_SKILL:
            if not isinstance(target, str) or target not in self.player.available_skill_moves():
                raise ValueError("هذه المهارة غير مفتوحة لهذا الحيوان")
            player_move = self._moves[target]
        else:
            raise ValueError(f"فعل غير معروف: {action}")

        enemy_move = self._moves[self._choose_enemy_move_id()]
        acting_player = self.player
        events: list[BattleEvent] = []
        acted: set[int] = set()
        for attacker, defender, move in self._ordered(acting_player, player_move, enemy_move):
            if attacker.is_fainted:
                continue
            acted.add(id(attacker))
            events.extend(self._last_stand(attacker))
            events.extend(self._act(attacker, defender, move))
            if self.enemy.is_fainted:
                self.outcome = OUTCOME_WON
                break
            if self._resolve_player_faint(events):
                break
            if self._enemy_fled():
                self.outcome = OUTCOME_ENEMY_FLED
                events.append(BattleEvent(KIND_ENEMY_FLED, self.enemy.name_ar, self.player.name_ar))
                break

        acting_player.priority_next = (
            id(acting_player) in acted and player_move.effect.kind == PRIORITY_EFFECT
        )
        self.enemy.priority_next = (
            id(self.enemy) in acted and enemy_move.effect.kind == PRIORITY_EFFECT
        )
        return events

    def _switch(self, target: int | None) -> list[BattleEvent]:
        if target is None or target not in self.switch_candidates():
            raise ValueError("لا يمكن التبديل إلى هذا الحيوان")
        self._active = target
        for animal in self.party:
            animal.priority_next = False
        events = [BattleEvent(KIND_SWITCH, self.player.name_ar, self.enemy.name_ar)]
        enemy_move = self._moves[self._choose_enemy_move_id()]
        events.extend(self._act(self.enemy, self.player, enemy_move))
        self._resolve_player_faint(events)
        self.enemy.priority_next = enemy_move.effect.kind == PRIORITY_EFFECT
        return events

    def _capture(self) -> list[BattleEvent]:
        if not self.can_capture():
            raise ValueError("الاصطياد غير متاح الآن")
        player = self.player
        if self._rng.random() < CAPTURE_CHANCE:
            self.enemy.heal_full()
            self.captured = self.enemy
            self.outcome = OUTCOME_CAPTURED
            return [BattleEvent(KIND_CAPTURED, player.name_ar, self.enemy.name_ar)]
        events = [BattleEvent(KIND_CAPTURE_FAILED, player.name_ar, self.enemy.name_ar)]
        enemy_move = self._moves[self._choose_enemy_move_id()]
        events.extend(self._act(self.enemy, player, enemy_move))
        self._resolve_player_faint(events)
        return events

    def _resolve_player_faint(self, events: list[BattleEvent]) -> bool:
        """يُرجع True إن خسر الفريق كله. وإلا يدخل الحيوان الحي التالي تلقائياً."""
        if not self.player.is_fainted:
            return False
        alive = [i for i, animal in enumerate(self.party) if not animal.is_fainted]
        if not alive:
            self.outcome = OUTCOME_LOST
            return True
        self._active = alive[0]
        events.append(BattleEvent(KIND_AUTO_SWITCH, self.player.name_ar, self.enemy.name_ar))
        return False

    def _ordered(
        self, player: AnimalInstance, player_move: Move, enemy_move: Move
    ) -> list[tuple[AnimalInstance, AnimalInstance, Move]]:
        pair = [(player, self.enemy, player_move), (self.enemy, player, enemy_move)]
        if player.priority_next != self.enemy.priority_next:
            player_first = player.priority_next
        else:
            player_first = player.template.speed >= self.enemy.template.speed
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
        if attacker is not self.enemy and id(attacker) in self._power_armed:
            multiplier *= POWER_MULTIPLIER
            self._power_armed.discard(id(attacker))
        result = compute_attack(
            attacker, defender, multiplier, self._rng, defense=self._defense_of(defender)
        )
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

    def _defense_of(self, animal: AnimalInstance) -> float:
        base = float(animal.template.defense)
        return base * DEFENSE_BOOST if id(animal) in self._defense_boosted else base

    def can_use_item(self, item_id: str) -> bool:
        if self.outcome is not None:
            return False
        player = self.player
        if item_id == "heal":
            return player.current_hp < player.max_hp
        if item_id == "power":
            return id(player) not in self._power_armed
        if item_id == "defense":
            return id(player) not in self._defense_boosted
        return False

    def _use_item(self, item_id: int | str | None) -> list[BattleEvent]:
        if not isinstance(item_id, str) or not self.can_use_item(item_id):
            raise ValueError("لا يمكن استخدام هذا العنصر الآن")
        player = self.player
        if item_id == "heal":
            heal = (player.max_hp - player.current_hp) * HEAL_ITEM_PERCENT // 100
            player.current_hp += heal
            events = [BattleEvent(KIND_ITEM_HEAL, player.name_ar, player.name_ar, "شفاء", heal)]
        elif item_id == "power":
            self._power_armed.add(id(player))
            events = [BattleEvent(KIND_ITEM_POWER, player.name_ar, player.name_ar)]
        else:
            self._defense_boosted.add(id(player))
            events = [BattleEvent(KIND_ITEM_DEFENSE, player.name_ar, player.name_ar)]
        for animal in self.party:
            animal.priority_next = False
        enemy_move = self._moves[self._choose_enemy_move_id()]
        events.extend(self._act(self.enemy, player, enemy_move))
        self._resolve_player_faint(events)
        return events

    def _enemy_fled(self) -> bool:
        threshold = self.enemy.template.flee_at_percent
        if threshold is None or self.enemy.is_fainted:
            return False
        return self.enemy.current_hp * 100 <= self.enemy.max_hp * threshold
