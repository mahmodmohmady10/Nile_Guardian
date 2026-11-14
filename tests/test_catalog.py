"""اختبارات كتالوج الحيوانات والحركات، والمراجع بينه وبين الخريطة."""

from __future__ import annotations

from typing import Any

import pytest
from src.utils.data_loader import (
    MapValidationError,
    check_animal_refs,
    check_party_refs,
    load_catalog,
    load_map_file,
    validate_animals,
    validate_map,
    validate_moves,
    validate_new_game,
)
from src.utils.paths import resource_path


def moves_data() -> dict[str, Any]:
    return {"peck": {"name_ar": "نقرة", "power": 30, "accuracy": 95}}


def animal_data() -> dict[str, Any]:
    return {
        "saqr": {"name_ar": "صقر", "max_hp": 40, "attack": 12, "defense": 8,
                 "speed": 14, "basic_move": "peck", "special_move": "peck"}
    }


def test_valid_catalog_pieces_load() -> None:
    moves = validate_moves(moves_data(), "moves.json")
    animals = validate_animals(animal_data(), moves, "animals.json")
    assert animals["saqr"].basic_move == "peck"


def test_accuracy_out_of_range_is_named() -> None:
    data = moves_data()
    data["peck"]["accuracy"] = 150
    with pytest.raises(MapValidationError) as info:
        validate_moves(data, "moves.json")
    assert info.value.field == "peck.accuracy"


def test_unknown_move_reference_is_named() -> None:
    moves = validate_moves(moves_data(), "moves.json")
    data = animal_data()
    data["saqr"]["special_move"] = "ghost"
    with pytest.raises(MapValidationError) as info:
        validate_animals(data, moves, "animals.json")
    assert info.value.field == "saqr.special_move"


def test_zero_max_hp_rejected() -> None:
    moves = validate_moves(moves_data(), "moves.json")
    data = animal_data()
    data["saqr"]["max_hp"] = 0
    with pytest.raises(MapValidationError) as info:
        validate_animals(data, moves, "animals.json")
    assert info.value.field == "saqr.max_hp"


def test_real_catalog_loads_and_every_move_exists() -> None:
    catalog = load_catalog(
        resource_path("data", "animals.json"), resource_path("data", "moves.json")
    )
    assert {"saqr_jedi", "ghazal_reem", "timsah_nile", "asad_dinder"} <= set(catalog.animals)
    for animal in catalog.animals.values():
        assert animal.basic_move in catalog.moves and animal.special_move in catalog.moves


def test_zone_with_unknown_animal_is_rejected() -> None:
    catalog = load_catalog(
        resource_path("data", "animals.json"), resource_path("data", "moves.json")
    )
    data: dict[str, Any] = {
        "width": 3,
        "height": 3,
        "tile_legend": {".": {"name": "grass", "solid": False, "color": [1, 2, 3]}},
        "grid": ["...", "...", "..."],
        "spawn": {"x": 0, "y": 0},
        "npcs": [],
        "events": [],
        "encounter_zones": [
            {
                "id": "fields",
                "x": 0,
                "y": 0,
                "width": 2,
                "height": 2,
                "rate_percent": 10,
                "table": [{"animal_id": "dragon", "weight": 1}],
            }
        ],
    }
    spec = validate_map(data, "map.json")
    with pytest.raises(MapValidationError) as info:
        check_animal_refs(spec, catalog, "map.json")
    assert info.value.field == "encounter_zones[fields]"


def test_real_village_animal_references_resolve() -> None:
    catalog = load_catalog(
        resource_path("data", "animals.json"), resource_path("data", "moves.json")
    )
    spec = load_map_file(resource_path("data", "maps", "village_01.json"))
    check_animal_refs(spec, catalog, "village_01.json")
    assert len(spec.encounter_zones) == 1


def test_party_with_unknown_animal_is_rejected() -> None:
    catalog = load_catalog(
        resource_path("data", "animals.json"), resource_path("data", "moves.json")
    )
    new_game = validate_new_game(
        {"player_name": "الأمين", "map_id": "village_01", "party": ["dragon"]}, "new_game.json"
    )
    with pytest.raises(MapValidationError) as info:
        check_party_refs(new_game, catalog, "new_game.json")
    assert info.value.field == "party"
