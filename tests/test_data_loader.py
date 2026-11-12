"""اختبارات محمّل الخرائط: كل خطأ يذكر الحقل، والخريطة الفعلية صالحة."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import pytest
from src.utils.data_loader import MapValidationError, load_map_file, validate_map
from src.utils.paths import resource_path

GRASS = {"name": "grass", "solid": False, "color": [78, 132, 64]}
TREE = {"name": "tree", "solid": True, "color": [34, 88, 44]}


def valid_data() -> dict[str, Any]:
    return {
        "width": 3,
        "height": 3,
        "tile_legend": {".": dict(GRASS), "#": dict(TREE)},
        "grid": ["...", ".#.", "..."],
        "spawn": {"x": 0, "y": 0},
        "npcs": [],
        "events": [],
    }


def error_for(data: dict[str, Any]) -> MapValidationError:
    with pytest.raises(MapValidationError) as info:
        validate_map(data, "test.json")
    return info.value


def test_valid_map_loads() -> None:
    spec = validate_map(valid_data(), "test.json")
    assert (spec.width, spec.height, spec.spawn) == (3, 3, (0, 0))


def test_missing_field_is_named() -> None:
    data = valid_data()
    del data["grid"]
    assert error_for(data).field == "grid"


def test_wrong_row_length_names_the_row() -> None:
    data = valid_data()
    data["grid"][0] = "...."
    assert error_for(data).field == "grid[0]"


def test_unknown_symbol_is_reported() -> None:
    data = valid_data()
    data["grid"][2] = "..?"
    assert error_for(data).field == "grid[2]"


def test_bool_is_not_accepted_as_integer() -> None:
    data = valid_data()
    data["width"] = True
    assert error_for(data).field == "width"


def test_spawn_on_solid_tile_rejected() -> None:
    data = valid_data()
    data["spawn"] = {"x": 1, "y": 1}
    assert error_for(data).field == "spawn"


def test_spawn_out_of_bounds_rejected() -> None:
    data = valid_data()
    data["spawn"] = {"x": 5, "y": 0}
    assert error_for(data).field == "spawn"


def test_npc_on_solid_tile_rejected() -> None:
    data = valid_data()
    data["npcs"] = [{"id": "a", "name_ar": "أ", "x": 1, "y": 1, "event_id": None}]
    assert error_for(data).field == "npcs[0]"


def test_npc_referring_to_missing_event_rejected() -> None:
    data = valid_data()
    data["npcs"] = [{"id": "a", "name_ar": "أ", "x": 0, "y": 2, "event_id": "ghost"}]
    assert error_for(data).field == "npcs[0].event_id"


def test_duplicate_npc_id_rejected() -> None:
    data = valid_data()
    data["npcs"] = [
        {"id": "a", "name_ar": "أ", "x": 0, "y": 2, "event_id": None},
        {"id": "a", "name_ar": "ب", "x": 2, "y": 2, "event_id": None},
    ]
    assert error_for(data).field == "npcs[1].id"


def test_broken_json_file_reports_json_field() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "bad.json"
        path.write_text("{bad", encoding="utf-8")
        with pytest.raises(MapValidationError) as info:
            load_map_file(path)
        assert info.value.field == "<json>"


def test_real_village_map_is_valid() -> None:
    spec = load_map_file(resource_path("data", "maps", "village_01.json"))
    assert (spec.width, spec.height) == (30, 18)
    assert spec.width * 32 == 960 and spec.height * 32 == 576
    assert len(spec.npcs) >= 1
