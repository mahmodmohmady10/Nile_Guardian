"""اختبارات المعركة: الضرر والمبادرة والنهايات، بأرقام عشوائية محقونة (حتمية)."""

from __future__ import annotations

import pytest
from src.core.game_state import GameState
from src.logic.battle_engine import (
    ACTION_ATTACK,
    ACTION_FLEE,
    ACTION_SPECIAL,
    KIND_ATTACK,
    KIND_FAINT,
    KIND_FLEE,
    OUTCOME_FLED,
    OUTCOME_LOST,
    OUTCOME_WON,
    BattleEngine,
    BattleEvent,
)
from src.logic.battle_text import describe_event
from src.logic.damage import compute_attack
from src.logic.models import AnimalInstance, AnimalTemplate, Move


class ConstRng:
    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


MOVES = {
    "peck": Move("peck", "نقرة", 30, 95),
    "dive": Move("dive", "انقضاض", 50, 75),
    "bite": Move("bite", "عضة", 32, 90),
    "tail": Move("tail", "ضربة الذيل", 46, 78),
}


def player_template(speed: int = 14) -> AnimalTemplate:
    return AnimalTemplate("saqr", "صقر", 40, 12, 8, speed, "peck", "dive")


def enemy_template(speed: int = 6, defense: int = 12) -> AnimalTemplate:
    return AnimalTemplate("timsah", "تمساح", 48, 13, defense, speed, "bite", "tail")


def fight(
    rng: ConstRng | None = None,
    player_speed: int = 14,
    enemy_speed: int = 6,
    player_hp: int = 40,
    enemy_hp: int = 48,
) -> tuple[BattleEngine, AnimalInstance, AnimalInstance]:
    player = AnimalInstance(player_template(player_speed), player_hp)
    enemy = AnimalInstance(enemy_template(enemy_speed), enemy_hp)
    engine = BattleEngine(player, enemy, MOVES, rng or ConstRng(0.5))  # type: ignore[arg-type]
    return engine, player, enemy


def test_hit_damage_follows_formula() -> None:
    player = AnimalInstance.fresh(player_template())
    enemy = AnimalInstance.fresh(enemy_template())
    result = compute_attack(player, enemy, MOVES["peck"], ConstRng(0.5))  # type: ignore[arg-type]
    assert result.hit and not result.critical and result.damage == 14


def test_roll_above_accuracy_misses() -> None:
    player = AnimalInstance.fresh(player_template())
    enemy = AnimalInstance.fresh(enemy_template())
    result = compute_attack(player, enemy, MOVES["peck"], ConstRng(0.99))  # type: ignore[arg-type]
    assert not result.hit and result.damage == 0


def test_critical_hit_multiplies_damage() -> None:
    player = AnimalInstance.fresh(player_template())
    enemy = AnimalInstance.fresh(enemy_template())
    result = compute_attack(player, enemy, MOVES["peck"], ConstRng(0.0))  # type: ignore[arg-type]
    assert result.hit and result.critical and result.damage == 19


def test_damage_is_at_least_one_on_hit() -> None:
    player = AnimalInstance.fresh(player_template())
    armored = AnimalInstance.fresh(enemy_template(defense=10_000))
    result = compute_attack(player, armored, MOVES["peck"], ConstRng(0.5))  # type: ignore[arg-type]
    assert result.damage == 1


def test_faster_player_acts_first() -> None:
    engine, _, _ = fight(player_speed=14, enemy_speed=6)
    events = engine.turn(ACTION_ATTACK)
    assert events[0].actor_name == "صقر"


def test_faster_enemy_acts_first() -> None:
    engine, _, _ = fight(player_speed=10, enemy_speed=20)
    events = engine.turn(ACTION_ATTACK)
    assert events[0].actor_name == "تمساح"


def test_speed_tie_goes_to_player() -> None:
    engine, _, _ = fight(player_speed=10, enemy_speed=10)
    assert engine.turn(ACTION_ATTACK)[0].actor_name == "صقر"


def test_defeating_enemy_ends_in_win() -> None:
    engine, _, enemy = fight(enemy_hp=5)
    events = engine.turn(ACTION_ATTACK)
    assert engine.outcome == OUTCOME_WON
    assert events[-1].kind == KIND_FAINT and events[-1].target_name == "تمساح"
    assert enemy.is_fainted


def test_losing_lead_animal_ends_in_loss() -> None:
    engine, player, _ = fight(player_hp=1)
    engine.turn(ACTION_ATTACK)
    assert engine.outcome == OUTCOME_LOST
    assert player.is_fainted


def test_flee_ends_battle_with_single_event() -> None:
    engine, _, _ = fight()
    events = engine.turn(ACTION_FLEE)
    assert engine.outcome == OUTCOME_FLED
    assert len(events) == 1 and events[0].kind == KIND_FLEE


def test_no_turn_after_battle_ended() -> None:
    engine, _, _ = fight()
    engine.turn(ACTION_FLEE)
    with pytest.raises(RuntimeError):
        engine.turn(ACTION_ATTACK)


def test_unknown_action_rejected() -> None:
    engine, _, _ = fight()
    with pytest.raises(ValueError):
        engine.turn("dance")


def test_player_special_uses_special_move() -> None:
    engine, _, _ = fight()
    events = engine.turn(ACTION_SPECIAL)
    assert events[0].kind == KIND_ATTACK and events[0].move_name == "انقضاض"


def test_enemy_uses_special_when_roll_is_low() -> None:
    engine, _, _ = fight(rng=ConstRng(0.0))
    events = engine.turn(ACTION_ATTACK)
    assert any(event.move_name == "ضربة الذيل" for event in events)


def test_critical_text_is_arabic_and_marked() -> None:
    event = BattleEvent(KIND_ATTACK, "صقر", "تمساح", "نقرة", 19, True)
    assert "ضربة حرجة" in describe_event(event)


def test_flee_text_mentions_retreat() -> None:
    assert "انسحب" in describe_event(BattleEvent(KIND_FLEE, "صقر", "تمساح"))


def test_healing_party_restores_full_hp() -> None:
    template = player_template()
    state = GameState(
        player_name="الأمين", map_id="village_01", templates={"saqr": template}
    )
    state.give_animal("saqr")
    lead = state.lead()
    assert lead is not None
    lead.current_hp = 3
    state.heal_party()
    assert lead.current_hp == lead.max_hp
