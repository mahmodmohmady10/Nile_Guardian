"""اختبارات التحقق من الأحداث وحالة اللعبة، والملفات الفعلية."""

from __future__ import annotations

from typing import Any

import pytest
from src.utils.data_loader import (
    MapValidationError,
    check_event_dialogues,
    load_dialogues_file,
    load_map_file,
    load_new_game_file,
    validate_map,
    validate_new_game,
)
from src.utils.paths import resource_path


def base_map() -> dict[str, Any]:
    return {
        "width": 3,
        "height": 3,
        "tile_legend": {
            ".": {"name": "grass", "solid": False, "color": [1, 2, 3]},
            "#": {"name": "tree", "solid": True, "color": [4, 5, 6]},
        },
        "grid": ["...", ".#.", "..."],
        "spawn": {"x": 0, "y": 0},
        "npcs": [{"id": "elder", "name_ar": "العم", "x": 0, "y": 2, "event_id": None}],
        "events": [
            {
                "id": "talk",
                "trigger": {"type": "on_interact", "npc_id": "elder"},
                "conditions": [{"type": "flag_not_set", "flag": "seen"}],
                "actions": [
                    {"type": "dialogue", "dialogue_id": "elder"},
                    {"type": "set_flag", "flag": "seen"},
                ],
            }
        ],
    }


def error_for(data: dict[str, Any]) -> MapValidationError:
    with pytest.raises(MapValidationError) as info:
        validate_map(data, "map.json")
    return info.value


def test_valid_events_load() -> None:
    spec = validate_map(base_map(), "map.json")
    assert spec.events[0].trigger.npc_id == "elder"
    assert spec.events[0].actions[1].flag == "seen"


def test_unknown_trigger_is_named() -> None:
    data = base_map()
    data["events"][0]["trigger"]["type"] = "on_sneeze"
    assert error_for(data).field == "events[0].trigger.type"


def test_unsupported_action_is_named() -> None:
    data = base_map()
    data["events"][0]["actions"].append({"type": "battle", "enemy_id": "x"})
    assert error_for(data).field == "events[0].actions[2].type"


def test_interact_on_unknown_npc_rejected() -> None:
    data = base_map()
    data["events"][0]["trigger"]["npc_id"] = "ghost"
    assert error_for(data).field == "events[0].trigger.npc_id"


def test_step_trigger_outside_map_rejected() -> None:
    data = base_map()
    data["events"][0]["trigger"] = {"type": "on_step", "x": 9, "y": 9}
    assert error_for(data).field == "events[0].trigger"


def test_event_with_no_actions_rejected() -> None:
    data = base_map()
    data["events"][0]["actions"] = []
    assert error_for(data).field == "events[0].actions"


def test_unknown_condition_is_named() -> None:
    data = base_map()
    data["events"][0]["conditions"] = [{"type": "flag_maybe", "flag": "x"}]
    assert error_for(data).field == "events[0].conditions[0].type"


def test_event_dialogue_must_exist() -> None:
    spec = validate_map(base_map(), "map.json")
    with pytest.raises(MapValidationError) as info:
        check_event_dialogues(spec, {}, "map.json")
    assert info.value.field == "events[0].actions"


def test_real_village_events_reference_existing_dialogues() -> None:
    spec = load_map_file(resource_path("data", "maps", "village_01.json"))
    dialogues = load_dialogues_file(resource_path("data", "dialogues.json"))
    check_event_dialogues(spec, dialogues, "village_01.json")
    assert len(spec.events) == 3


def test_new_game_requires_player_name() -> None:
    with pytest.raises(MapValidationError) as info:
        validate_new_game({"map_id": "village_01", "party": []}, "new_game.json")
    assert info.value.field == "player_name"


def test_real_new_game_loads() -> None:
    spec = load_new_game_file(resource_path("data", "new_game.json"))
    assert spec.map_id == "village_01" and spec.party == ()
