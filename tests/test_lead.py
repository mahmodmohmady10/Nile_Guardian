"""اختبارات قائد الفريق: الحيوان الذي تلعب به يقاتل أولاً، والفريق لا يصبح فارغاً."""

from __future__ import annotations

import random

import pytest
from src.core.game_state import GameState
from src.logic.battle_engine import ACTION_ATTACK, BattleEngine
from src.logic.models import AnimalInstance
from src.utils.data_loader import load_catalog
from src.utils.paths import resource_path

CATALOG = load_catalog(resource_path("data", "animals.json"), resource_path("data", "moves.json"))


def party_state() -> GameState:
    state = GameState(player_name="الأمين", map_id="village_01", templates=CATALOG.animals)
    for animal_id in ("saqr_jedi", "ghazal_reem", "timsah_nile"):
        state.give_animal(animal_id)
    return state


def test_set_lead_moves_chosen_animal_to_front() -> None:
    state = party_state()
    state.set_lead(2)
    assert [animal.id for animal in state.party] == ["timsah_nile", "saqr_jedi", "ghazal_reem"]
    assert state.lead() is not None and state.lead().id == "timsah_nile"


def test_set_lead_rejects_invalid_index() -> None:
    with pytest.raises(ValueError):
        party_state().set_lead(5)


def test_party_never_becomes_empty_when_leading() -> None:
    state = party_state()
    for index in (1, 2, 0):
        state.set_lead(index)
    assert len(state.party) == 3


def test_battle_starts_with_the_chosen_lead() -> None:
    state = party_state()
    state.set_lead(1)
    enemy = AnimalInstance.fresh(CATALOG.animals["ghazal_reem"])
    engine = BattleEngine(state.party, enemy, CATALOG.moves, random.Random(1))
    assert engine.player.id == "ghazal_reem"
    events = engine.turn(ACTION_ATTACK)
    assert events[0].actor_name == CATALOG.animals["ghazal_reem"].name_ar


def test_heal_party_restores_every_member() -> None:
    state = party_state()
    for animal in state.party:
        animal.current_hp = 1
    state.heal_party()
    assert all(animal.current_hp == animal.max_hp for animal in state.party)
