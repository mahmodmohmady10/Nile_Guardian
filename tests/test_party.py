"""اختبارات الفريق: التبديل يستهلك الدور، والسقوط التلقائي، والخسارة، والاصطياد، والاستبدال."""

from __future__ import annotations

import pytest
from src.core.game_state import GameState
from src.core.save import SaveError, restore, snapshot
from src.logic.battle_engine import (
    ACTION_ATTACK,
    ACTION_CAPTURE,
    ACTION_SWITCH,
    CAPTURE_CHANCE,
    KIND_ATTACK,
    KIND_AUTO_SWITCH,
    KIND_CAPTURE_FAILED,
    KIND_CAPTURED,
    KIND_SWITCH,
    OUTCOME_CAPTURED,
    OUTCOME_LOST,
    BattleEngine,
    BattleEvent,
)
from src.logic.battle_text import describe_event
from src.logic.models import MAX_PARTY_SIZE, AnimalInstance, AnimalTemplate, Effect, Move
from src.utils.data_loader import load_catalog
from src.utils.paths import resource_path

ANIMALS_FILE = resource_path("data", "animals.json")
MOVES_FILE = resource_path("data", "moves.json")


class ConstRng:
    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


MOVES = {
    "peck": Move("peck", "نقرة", Effect()),
    "dive": Move("dive", "انقضاض", Effect("extra_damage", 1.5)),
}


def make(
    animal_id: str,
    name: str,
    hp: int = 150,
    atk: int = 50,
    dfn: int = 30,
    speed: int = 10,
    catchable: bool = True,
) -> AnimalTemplate:
    return AnimalTemplate(
        animal_id, name, hp, atk, dfn, speed, "peck", "dive", 0.0, 2.0, 1.0, 1.0,
        None, None, catchable,
    )


def test_switch_costs_turn_and_enemy_hits_the_newcomer() -> None:
    first = AnimalInstance.fresh(make("a", "صقر"))
    second = AnimalInstance.fresh(make("b", "ثعلب"))
    enemy = AnimalInstance.fresh(make("e", "خصم", atk=10, dfn=10, hp=500))
    engine = BattleEngine([first, second], enemy, MOVES, ConstRng(0.5))
    events = engine.turn(ACTION_SWITCH, target=1)
    assert events[0].kind == KIND_SWITCH
    assert not any(event.kind == KIND_ATTACK for event in events)
    assert engine.player is second


def test_cannot_switch_to_active_or_fainted() -> None:
    first = AnimalInstance.fresh(make("a", "صقر"))
    fainted = AnimalInstance(make("b", "ثعلب"), 0)
    enemy = AnimalInstance.fresh(make("e", "خصم", hp=500))
    engine = BattleEngine([first, fainted], enemy, MOVES, ConstRng(0.5))
    assert not engine.can_switch()
    with pytest.raises(ValueError):
        engine.turn(ACTION_SWITCH, target=1)
    with pytest.raises(ValueError):
        engine.turn(ACTION_SWITCH, target=0)


def test_active_fainting_brings_next_member_without_losing() -> None:
    first = AnimalInstance(make("a", "صقر", speed=5), 1)
    second = AnimalInstance.fresh(make("b", "ثعلب", speed=5))
    enemy = AnimalInstance.fresh(make("e", "خصم", atk=50, dfn=10, speed=20, hp=500))
    engine = BattleEngine([first, second], enemy, MOVES, ConstRng(0.5))
    events = engine.turn(ACTION_ATTACK)
    assert any(event.kind == KIND_AUTO_SWITCH for event in events)
    assert engine.outcome is None and engine.player is second


def test_loss_only_when_whole_party_falls() -> None:
    first = AnimalInstance(make("a", "صقر", speed=5), 1)
    second = AnimalInstance(make("b", "ثعلب", speed=5), 1)
    enemy = AnimalInstance.fresh(make("e", "خصم", atk=50, dfn=10, speed=20, hp=500))
    engine = BattleEngine([first, second], enemy, MOVES, ConstRng(0.5))
    engine.turn(ACTION_ATTACK)
    assert engine.outcome is None
    engine.turn(ACTION_ATTACK)
    assert engine.outcome == OUTCOME_LOST


def test_capture_refused_above_threshold() -> None:
    enemy = AnimalInstance.fresh(make("e", "خصم", hp=200))
    engine = BattleEngine([AnimalInstance.fresh(make("a", "صقر"))], enemy, MOVES, ConstRng(0.5))
    assert not engine.can_capture()
    with pytest.raises(ValueError):
        engine.turn(ACTION_CAPTURE)


def test_capture_refused_for_uncatchable_even_when_weak() -> None:
    enemy = AnimalInstance(make("e", "أسد", hp=200, catchable=False), 10)
    engine = BattleEngine([AnimalInstance.fresh(make("a", "صقر"))], enemy, MOVES, ConstRng(0.5))
    assert not engine.can_capture()


def test_capture_succeeds_at_threshold_and_joins_healed() -> None:
    enemy = AnimalInstance(make("e", "غزال", hp=200), 10)  # 5% من الصحة
    engine = BattleEngine([AnimalInstance.fresh(make("a", "صقر"))], enemy, MOVES, ConstRng(0.0))
    events = engine.turn(ACTION_CAPTURE)
    assert events[0].kind == KIND_CAPTURED and engine.outcome == OUTCOME_CAPTURED
    assert engine.captured is enemy and enemy.current_hp == enemy.max_hp
    assert not engine.needs_replacement()


def test_failed_capture_lets_enemy_strike() -> None:
    enemy = AnimalInstance(make("e", "غزال", hp=200, atk=10, dfn=10), 10)
    engine = BattleEngine([AnimalInstance.fresh(make("a", "صقر"))], enemy, MOVES, ConstRng(0.99))
    events = engine.turn(ACTION_CAPTURE)
    assert events[0].kind == KIND_CAPTURE_FAILED and engine.outcome is None


def test_full_party_requires_replacement_and_swaps_member() -> None:
    party = [AnimalInstance.fresh(make(f"m{i}", f"حيوان{i}"))
             for i in range(MAX_PARTY_SIZE)]
    enemy = AnimalInstance(make("wild", "غزال", hp=200), 10)
    engine = BattleEngine(party, enemy, MOVES, ConstRng(0.0))
    engine.turn(ACTION_CAPTURE)
    assert engine.needs_replacement()
    engine.replace_member(1)
    assert [animal.id for animal in party] == ["m0", "wild", "m2"]
    assert len(party) == MAX_PARTY_SIZE


def test_replacement_refused_without_capture() -> None:
    engine = BattleEngine(
        [AnimalInstance.fresh(make("a", "صقر"))],
        AnimalInstance.fresh(make("e", "خصم", hp=500)),
        MOVES,
        ConstRng(0.5),
    )
    with pytest.raises(RuntimeError):
        engine.replace_member(0)


def test_party_larger_than_limit_rejected_by_engine() -> None:
    party = [AnimalInstance.fresh(make(f"m{i}", "x")) for i in range(MAX_PARTY_SIZE + 1)]
    enemy = AnimalInstance.fresh(make("e", "y"))
    with pytest.raises(ValueError):
        BattleEngine(party, enemy, MOVES, ConstRng(0.5))


def test_game_state_refuses_fourth_member() -> None:
    catalog = load_catalog(ANIMALS_FILE, MOVES_FILE)
    state = GameState(player_name="الأمين", map_id="village_01", templates=catalog.animals)
    for animal_id in ("saqr_jedi", "ghazal_reem", "timsah_nile"):
        state.give_animal(animal_id)
    with pytest.raises(ValueError):
        state.give_animal("wolf")


def test_save_rejects_oversized_party() -> None:
    catalog = load_catalog(ANIMALS_FILE, MOVES_FILE)
    state = GameState(player_name="الأمين", map_id="village_01", templates=catalog.animals)
    ids = ("saqr_jedi", "ghazal_reem", "timsah_nile", "wolf")
    state.party = [AnimalInstance.fresh(catalog.animals[i]) for i in ids]
    data = snapshot(state)
    with pytest.raises(SaveError) as info:
        restore(data, catalog.animals, {"village_01": (30, 18)})
    assert info.value.field == "party"


def test_capture_text_is_arabic() -> None:
    assert "اصطدت" in describe_event(BattleEvent(KIND_CAPTURED, "صقر", "غزال"))


def test_capture_chance_is_a_probability() -> None:
    assert 0 < CAPTURE_CHANCE <= 1
