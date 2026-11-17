"""اختبارات المعركة (توازن 0.7): الضرر والمرتد والحرجة والتفاوت والمهارات والنهايات."""

from __future__ import annotations

import pytest
from src.core.game_state import GameState
from src.logic.battle_engine import (
    ACTION_ATTACK,
    ACTION_SPECIAL,
    KIND_ATTACK,
    KIND_COUNTER,
    KIND_FAINT,
    KIND_HEAL,
    KIND_LAST_STAND,
    OUTCOME_LOST,
    OUTCOME_WON,
    BattleEngine,
    BattleEvent,
)
from src.logic.battle_text import describe_event
from src.logic.damage import AttackResult, compute_attack
from src.logic.models import AnimalInstance, AnimalTemplate, Effect, LastStand, Move


class ConstRng:
    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


def move(
    move_id: str,
    name: str,
    kind: str = "none",
    multiplier: float = 1.0,
    percent: int = 0,
) -> Move:
    return Move(move_id, name, Effect(kind, multiplier, percent))


MOVES = {
    "peck": move("peck", "نقرة"),
    "dive": move("dive", "انقضاض", "extra_damage", 1.5),
    "swift": move("swift", "وثبة سريعة", "priority_next_turn"),
    "roar": move("roar", "زئير", "heal_percent", percent=15),
    "bite": move("bite", "عضة"),
    "tail": move("tail", "ضربة الذيل", "extra_damage", 1.5),
}


def template(
    animal_id: str = "x",
    name: str = "س",
    hp: int = 150,
    atk: int = 50,
    dfn: int = 30,
    speed: int = 10,
    crit: float = 0.0,
    crit_mult: float = 2.0,
    vmin: float = 1.0,
    vmax: float = 1.0,
    flee: int | None = None,
    last: LastStand | None = None,
    basic: str = "peck",
    special: str = "dive",
) -> AnimalTemplate:
    return AnimalTemplate(
        animal_id, name, hp, atk, dfn, speed, basic, special,
        crit, crit_mult, vmin, vmax, flee, last,
    )


def hit(
    attacker: AnimalInstance, defender: AnimalInstance, multiplier: float = 1.0
) -> AttackResult:
    return compute_attack(attacker, defender, multiplier, ConstRng(0.5))  # type: ignore[arg-type]


def instance(t: AnimalTemplate, hp: int | None = None) -> AnimalInstance:
    animal = AnimalInstance.fresh(t)
    if hp is not None:
        animal.current_hp = hp
    return animal


def fight(
    player: AnimalTemplate,
    enemy: AnimalTemplate,
    player_hp: int | None = None,
    enemy_hp: int | None = None,
    rng: object | None = None,
) -> tuple[BattleEngine, AnimalInstance, AnimalInstance]:
    p = instance(player, player_hp)
    e = instance(enemy, enemy_hp)
    engine = BattleEngine([p], e, MOVES, rng or ConstRng(0.5))  # type: ignore[arg-type]
    return engine, p, e


# ---------- damage formula ----------

def test_damage_is_attack_minus_defense() -> None:
    result = hit(instance(template(atk=50)), instance(template(dfn=30)))
    assert result.damage == 20 and result.self_damage == 0 and not result.critical


def test_attack_below_defense_hurts_attacker_only() -> None:
    result = hit(instance(template(atk=20)), instance(template(dfn=30)))
    assert result.damage == 0 and result.self_damage == 10


def test_equal_attack_and_defense_deals_nothing() -> None:
    result = hit(instance(template(atk=30)), instance(template(dfn=30)))
    assert result.damage == 0 and result.self_damage == 0


def test_critical_uses_animal_multiplier() -> None:
    attacker = instance(template(atk=50, crit=1.0, crit_mult=2.5))
    result = hit(attacker, instance(template(dfn=30)))
    assert result.critical and result.damage == 50


def test_variance_is_per_animal() -> None:
    attacker = instance(template(atk=50, vmin=0.9, vmax=0.9))
    result = hit(attacker, instance(template(dfn=30)))
    assert result.damage == 18


def test_skill_multiplier_applies() -> None:
    result = hit(instance(template(atk=50)), instance(template(dfn=30)), 1.5)
    assert result.damage == 30


def test_positive_damage_is_at_least_one() -> None:
    attacker = instance(template(atk=31, vmin=0.5, vmax=0.5))
    result = hit(attacker, instance(template(dfn=30)))
    assert result.damage == 1


# ---------- battle engine ----------

def test_faster_player_acts_first() -> None:
    engine, _, _ = fight(template(name="صقر", speed=14), template(name="تمساح", speed=6))
    assert engine.turn(ACTION_ATTACK)[0].actor_name == "صقر"


def test_faster_enemy_acts_first() -> None:
    engine, _, _ = fight(template(name="صقر", speed=10), template(name="تمساح", speed=20))
    assert engine.turn(ACTION_ATTACK)[0].actor_name == "تمساح"


def test_speed_tie_goes_to_player() -> None:
    engine, _, _ = fight(template(name="صقر", speed=10), template(name="تمساح", speed=10))
    assert engine.turn(ACTION_ATTACK)[0].actor_name == "صقر"


def test_defeating_enemy_wins() -> None:
    engine, _, enemy = fight(template(speed=14), template(speed=6), enemy_hp=10)
    engine.turn(ACTION_ATTACK)
    assert engine.outcome == OUTCOME_WON and enemy.is_fainted


def test_losing_lead_animal_loses() -> None:
    engine, player, _ = fight(template(speed=14), template(speed=6), player_hp=10)
    engine.turn(ACTION_ATTACK)
    assert engine.outcome == OUTCOME_LOST and player.is_fainted



def test_last_stand_restores_quarter_once() -> None:
    rule = LastStand(threshold_percent=5, bonus_percent=25)
    asad = template(name="أسد", hp=200, speed=10, last=rule)
    engine, player, _ = fight(asad, template(hp=500, atk=10, dfn=10, speed=6), player_hp=9)
    first = engine.turn(ACTION_ATTACK)
    assert first[0].kind == KIND_LAST_STAND and first[0].amount == 50
    assert player.current_hp == 59
    player.current_hp = 9
    second = engine.turn(ACTION_ATTACK)
    assert not any(event.kind == KIND_LAST_STAND for event in second)


def test_roar_heals_without_damaging_user() -> None:
    asad = template(name="أسد", hp=200, speed=10, basic="peck", special="roar")
    engine, player, _ = fight(asad, template(hp=500, atk=10, dfn=10, speed=6), player_hp=100)
    events = engine.turn(ACTION_SPECIAL)
    assert any(event.kind == KIND_HEAL for event in events)
    assert player.current_hp == 130


def test_priority_move_acts_first_next_turn() -> None:
    falcon = template(name="صقر", speed=6, special="swift")
    goat = template(name="تمساح", speed=16, atk=10, dfn=10, hp=500)
    engine, _, _ = fight(falcon, goat)
    engine.turn(ACTION_SPECIAL)
    second = engine.turn(ACTION_ATTACK)
    assert second[0].actor_name == "صقر"


def test_counter_event_when_attack_below_defense() -> None:
    engine, player, _ = fight(
        template(name="صقر", atk=20, dfn=10, speed=14),
        template(name="تمساح", atk=5, dfn=30, hp=500),
    )
    events = engine.turn(ACTION_ATTACK)
    counter = [event for event in events if event.kind == KIND_COUNTER]
    assert counter and counter[0].amount == 10 and player.current_hp == 140



def test_no_turn_after_battle_ended() -> None:
    engine, _, _ = fight(template(), template(), enemy_hp=1)
    engine.turn(ACTION_ATTACK)
    with pytest.raises(RuntimeError):
        engine.turn(ACTION_ATTACK)


def test_unknown_action_rejected() -> None:
    engine, _, _ = fight(template(), template())
    with pytest.raises(ValueError):
        engine.turn("dance")


def test_enemy_uses_special_when_roll_is_low() -> None:
    crocodile = template(name="تمساح", basic="bite", special="tail")
    engine, _, _ = fight(template(), crocodile, rng=ConstRng(0.0))
    events = engine.turn(ACTION_ATTACK)
    assert any(event.move_name == "ضربة الذيل" for event in events)


# ---------- text and state ----------

def test_critical_text_shows_display_units() -> None:
    text = describe_event(BattleEvent(KIND_ATTACK, "صقر", "تمساح", "نقرة", 150, True))
    assert "ضربة حرجة" in text and "15" in text



def test_faint_text_names_target() -> None:
    assert "تراجع" in describe_event(BattleEvent(KIND_FAINT, "تمساح", "صقر"))


def test_healing_party_restores_full_hp_and_flags() -> None:
    saqr = template(animal_id="saqr")
    state = GameState(
        player_name="الأمين", map_id="village_01", templates={"saqr": saqr}
    )
    state.give_animal("saqr")
    lead = state.lead()
    assert lead is not None
    lead.current_hp = 3
    lead.last_stand_used = True
    state.heal_party()
    assert lead.current_hp == lead.max_hp and not lead.last_stand_used
