"""اختبارات النقود والحقيبة والمتجر والحفظ الإصدار 2، والتحقق من بيانات العناصر."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from src.core.game_state import GameState
from src.core.save import SAVE_VERSION, SaveError, restore, snapshot
from src.utils.data_loader import (
    MapValidationError,
    load_catalog,
    load_items_file,
    load_map_file,
    validate_items,
)
from src.utils.paths import resource_path

ANIMALS_FILE = resource_path("data", "animals.json")
MOVES_FILE = resource_path("data", "moves.json")
CATALOG = load_catalog(ANIMALS_FILE, MOVES_FILE)
ITEMS = load_items_file(resource_path("data", "items.json"))
SIZES = {"village_01": (30, 18), "dinder_01": (30, 18)}


def fresh() -> GameState:
    return GameState(player_name="الأمين", map_id="village_01", templates=CATALOG.animals)


def test_spend_refuses_when_short() -> None:
    state = fresh()
    state.add_money(20)
    assert not state.spend(30)
    assert state.money == 20


def test_spend_deducts_when_enough() -> None:
    state = fresh()
    state.add_money(100)
    assert state.spend(45)
    assert state.money == 55


def test_bag_counts_items() -> None:
    state = fresh()
    state.add_item("heal")
    state.add_item("heal")
    assert state.bag == {"heal": 2}


def test_real_item_prices_match_approved_values() -> None:
    prices = {item_id: item.price for item_id, item in ITEMS.items()}
    assert prices == {"heal": 30, "power": 45, "defense": 60}
    assert "upgrade" not in ITEMS


def test_real_rewards_match_approved_values() -> None:
    rewards = {animal_id: CATALOG.animals[animal_id].reward_money
               for animal_id in ("ghazal_reem", "timsah_nile", "wolf", "leopard", "asad_dinder")}
    assert rewards == {"ghazal_reem": 10, "timsah_nile": 20, "wolf": 25, "leopard": 30,
                       "asad_dinder": 50}


def test_merchant_is_a_shop_npc_and_needs_no_dialogue() -> None:
    spec = load_map_file(resource_path("data", "maps", "village_01.json"))
    merchant = next(npc for npc in spec.npcs if npc.id == "merchant")
    assert merchant.role == "shop"


def test_save_version_two_round_trips_money_and_bag() -> None:
    state = fresh()
    state.add_money(77)
    state.add_item("power")
    data = snapshot(state)
    assert data["save_version"] == SAVE_VERSION
    restored = restore(data, CATALOG.animals, SIZES, item_ids=set(ITEMS))
    assert restored.money == 77 and restored.bag == {"power": 1}


def test_version_one_save_loads_with_empty_money_and_bag() -> None:
    data = snapshot(fresh())
    data["save_version"] = 1
    del data["money"]
    del data["bag"]
    restored = restore(data, CATALOG.animals, SIZES, item_ids=set(ITEMS))
    assert restored.money == 0 and restored.bag == {}


def test_unknown_item_in_bag_is_rejected() -> None:
    data = snapshot(fresh())
    data["bag"] = {"dragon_egg": 1}
    with pytest.raises(SaveError) as info:
        restore(data, CATALOG.animals, SIZES, item_ids=set(ITEMS))
    assert info.value.field == "bag"


def test_negative_money_is_rejected() -> None:
    data = snapshot(fresh())
    data["money"] = -5
    with pytest.raises(SaveError) as info:
        restore(data, CATALOG.animals, SIZES, item_ids=set(ITEMS))
    assert info.value.field == "money"


def test_zero_count_in_bag_is_rejected() -> None:
    data = snapshot(fresh())
    data["bag"] = {"heal": 0}
    with pytest.raises(SaveError) as info:
        restore(data, CATALOG.animals, SIZES, item_ids=set(ITEMS))
    assert info.value.field == "bag"


def error_for(rows: dict[str, Any]) -> MapValidationError:
    with pytest.raises(MapValidationError) as info:
        validate_items(rows, "items.json")
    return info.value


def test_zero_price_is_named() -> None:
    assert error_for({"heal": {"name_ar": "شفاء", "price": 0}}).field == "heal.price"


def test_missing_item_name_is_named() -> None:
    assert error_for({"heal": {"price": 30}}).field == "heal.name_ar"


def test_items_file_round_trips_through_disk() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "items.json"
        path.write_text(json.dumps({"heal": {"name_ar": "شفاء", "price": 30}}), encoding="utf-8")
        assert load_items_file(path)["heal"].price == 30
