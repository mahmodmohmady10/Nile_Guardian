"""اختبارات العناصر داخل المعركة: الشفاء، والقوة لضربة واحدة، والدفاع حتى نهاية المعركة."""

from __future__ import annotations

import pytest
from src.logic.battle_engine import (
    ACTION_ATTACK,
    ACTION_ITEM,
    KIND_ATTACK,
    KIND_ITEM_HEAL,
    BattleEngine,
)
from src.logic.models import AnimalInstance, AnimalTemplate, Effect, Move


class ConstRng:
    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


MOVES = {
    "peck": Move("peck", "نقرة", Effect()),
    "dive": Move("dive", "انقضاض", Effect("extra_damage", 1.5)),
}


def make(animal_id: str, name: str, hp: int = 150, atk: int = 50, dfn: int = 30,
         speed: int = 14) -> AnimalTemplate:
    return AnimalTemplate(animal_id, name, hp, atk, dfn, speed, "peck", "dive",
                          0.0, 2.0, 1.0, 1.0, None, None, True)


def weak_enemy() -> AnimalInstance:
    return AnimalInstance.fresh(make("e", "خصم", hp=500, atk=10, dfn=30, speed=6))


def test_heal_restores_half_of_missing_hp() -> None:
    player = AnimalInstance(make("a", "صقر"), 50)
    engine = BattleEngine([player], weak_enemy(), MOVES, ConstRng(0.5))  # type: ignore[arg-type]
    events = engine.turn(ACTION_ITEM, "heal")
    assert events[0].kind == KIND_ITEM_HEAL
    assert player.current_hp == 100


def test_heal_refused_at_full_hp() -> None:
    engine = BattleEngine([AnimalInstance.fresh(make("a", "صقر"))], weak_enemy(), MOVES,
                          ConstRng(0.5))  # type: ignore[arg-type]
    assert not engine.can_use_item("heal")
    with pytest.raises(ValueError):
        engine.turn(ACTION_ITEM, "heal")


def test_item_costs_the_turn_and_enemy_strikes() -> None:
    player = AnimalInstance(make("a", "صقر"), 50)
    enemy = AnimalInstance.fresh(make("e", "خصم", hp=500, atk=50, dfn=30, speed=6))
    engine = BattleEngine([player], enemy, MOVES, ConstRng(0.5))  # type: ignore[arg-type]
    events = engine.turn(ACTION_ITEM, "heal")
    assert any(event.actor_name == "خصم" for event in events)


def test_power_multiplies_only_the_next_strike() -> None:
    player = AnimalInstance.fresh(make("a", "صقر", atk=50))
    enemy = AnimalInstance.fresh(make("e", "خصم", hp=500, atk=10, dfn=30, speed=6))
    engine = BattleEngine([player], enemy, MOVES, ConstRng(0.5))  # type: ignore[arg-type]
    engine.turn(ACTION_ITEM, "power")
    assert not engine.can_use_item("power")
    first = [e for e in engine.turn(ACTION_ATTACK) if e.kind == KIND_ATTACK]
    second = [e for e in engine.turn(ACTION_ATTACK) if e.kind == KIND_ATTACK]
    assert first[0].amount == 100
    assert second[0].amount == 20


def test_defense_boost_lasts_the_whole_battle() -> None:
    player = AnimalInstance.fresh(make("a", "صقر", dfn=30))
    enemy = AnimalInstance.fresh(make("e", "خصم", hp=500, atk=50, dfn=30, speed=6))
    engine = BattleEngine([player], enemy, MOVES, ConstRng(0.5))  # type: ignore[arg-type]
    engine.turn(ACTION_ITEM, "defense")
    assert not engine.can_use_item("defense")
    before = player.current_hp
    engine.turn(ACTION_ATTACK)
    assert before - player.current_hp == 5  # 50 - (30 × 1.5)


def test_unknown_item_is_refused() -> None:
    engine = BattleEngine([AnimalInstance.fresh(make("a", "صقر"))], weak_enemy(), MOVES,
                          ConstRng(0.5))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        engine.turn(ACTION_ITEM, "magic")
