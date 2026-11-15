"""اختبارات الخبرة والمستويات والترقية في المستشفى، والحفظ الإصدار 3."""

from __future__ import annotations

import pytest
from src.core.game_state import GameState
from src.core.hospital import try_upgrade
from src.core.save import SAVE_VERSION, SaveError, restore, snapshot
from src.logic.models import (
    AnimalInstance,
    upgraded_template,
    xp_reward,
)
from src.utils.data_loader import load_catalog
from src.utils.paths import resource_path

ANIMALS_FILE = resource_path("data", "animals.json")
MOVES_FILE = resource_path("data", "moves.json")
CATALOG = load_catalog(ANIMALS_FILE, MOVES_FILE)
SIZES = {"village_01": (30, 18), "dinder_01": (30, 18)}


def fresh_state() -> GameState:
    state = GameState(player_name="الأمين", map_id="village_01", templates=CATALOG.animals)
    state.give_animal("saqr_jedi")
    return state


def test_approved_experience_rewards() -> None:
    rewards = {animal_id: xp_reward(CATALOG.animals[animal_id])
               for animal_id in ("ghazal_reem", "timsah_nile", "wolf", "leopard", "asad_dinder")}
    assert rewards == {"ghazal_reem": 12, "timsah_nile": 25, "wolf": 24, "leopard": 19,
                       "asad_dinder": 24}


@pytest.mark.parametrize(("xp", "level"), [(0, 1), (9, 1), (10, 2), (29, 2), (30, 3),
                                           (210, 7), (500, 7)])
def test_levels_follow_thresholds(xp: int, level: int) -> None:
    animal = AnimalInstance.fresh(CATALOG.animals["saqr_jedi"])
    animal.xp = xp
    assert animal.level == level


def test_experience_goes_to_the_whole_party() -> None:
    state = fresh_state()
    state.give_animal("ghazal_reem")
    state.award_xp(12)
    assert [animal.xp for animal in state.party] == [12, 12]


def test_upgrade_needs_ten_experience() -> None:
    state = fresh_state()
    state.add_money(500)
    lead = state.lead()
    assert lead is not None
    lead.xp = 9
    message = try_upgrade(state, lead)
    assert "نقطة خبرة" in message
    assert not lead.upgraded and state.money == 500


def test_upgrade_costs_100_and_raises_stats() -> None:
    state = fresh_state()
    state.add_money(150)
    lead = state.lead()
    assert lead is not None
    lead.xp = 10
    before_hp = lead.max_hp
    message = try_upgrade(state, lead)
    assert "تمت ترقية" in message
    assert lead.upgraded and state.money == 50
    assert lead.max_hp == round(before_hp * 1.1)


def test_upgrade_is_once_per_animal() -> None:
    state = fresh_state()
    state.add_money(500)
    lead = state.lead()
    assert lead is not None
    lead.xp = 10
    try_upgrade(state, lead)
    money_after = state.money
    message = try_upgrade(state, lead)
    assert "من قبل" in message and state.money == money_after


def test_upgrade_refused_without_money() -> None:
    state = fresh_state()
    lead = state.lead()
    assert lead is not None
    lead.xp = 10
    assert "غير كافية" in try_upgrade(state, lead)
    assert not lead.upgraded


def test_upgraded_template_matches_formula() -> None:
    base = CATALOG.animals["saqr_jedi"]
    upgraded = upgraded_template(base)
    assert upgraded.max_hp == 165
    assert abs(upgraded.attack - 52 * 1.01) < 1e-9
    assert abs(upgraded.defense - 33.0) < 1e-9


def test_save_version_three_round_trips_xp_and_upgrade() -> None:
    state = fresh_state()
    state.add_money(100)
    lead = state.lead()
    assert lead is not None
    lead.xp = 14
    try_upgrade(state, lead)
    data = snapshot(state)
    assert data["save_version"] == SAVE_VERSION == 3
    restored = restore(data, CATALOG.animals, SIZES, item_ids=set())
    restored_lead = restored.lead()
    assert restored_lead is not None
    assert restored_lead.xp == 14 and restored_lead.upgraded
    assert restored_lead.max_hp == 165


def test_version_two_save_loads_without_xp_or_upgrade() -> None:
    data = snapshot(fresh_state())
    data["save_version"] = 2
    for entry in data["party"]:
        del entry["xp"]
        del entry["upgraded"]
    restored = restore(data, CATALOG.animals, SIZES, item_ids=set())
    lead = restored.lead()
    assert lead is not None and lead.xp == 0 and not lead.upgraded


def test_negative_xp_is_rejected() -> None:
    data = snapshot(fresh_state())
    data["party"][0]["xp"] = -1
    with pytest.raises(SaveError) as info:
        restore(data, CATALOG.animals, SIZES, item_ids=set())
    assert info.value.field == "party[0].xp"


def test_non_boolean_upgrade_flag_is_rejected() -> None:
    data = snapshot(fresh_state())
    data["party"][0]["upgraded"] = "yes"
    with pytest.raises(SaveError) as info:
        restore(data, CATALOG.animals, SIZES, item_ids=set())
    assert info.value.field == "party[0].upgraded"
