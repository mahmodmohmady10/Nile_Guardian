"""اختبارات الأهداف وسهم التوجيه: الترتيب، والإنجاز، والاتجاه، والبوابات، والملفات الفعلية."""

from __future__ import annotations

from typing import Any

import pytest
from src.core.game_state import GameState
from src.utils.data_loader import (
    MapValidationError,
    build_guide,
    check_objectives,
    load_catalog,
    load_map_file,
    validate_objectives,
)
from src.utils.paths import resource_path
from src.world.objectives import (
    DONE_DEFEATED,
    DONE_FLAG,
    TARGET_NPC,
    TARGET_ZONE,
    Objective,
    direction,
    has_reached,
    is_done,
    next_objective,
    resolve_point,
)


SEQUENCE = (
    Objective("talk", "تحدث", "village_01", TARGET_NPC, "elder", DONE_FLAG, "got_starter"),
    Objective(
        "ghazal", "الغزال", "village_01", TARGET_ZONE, "fields", DONE_DEFEATED, "ghazal_reem"
    ),
    Objective("wolf", "الذئب", "dinder_01", TARGET_ZONE, "savanna", DONE_DEFEATED, "wolf"),
)


def test_first_objective_comes_first_without_progress() -> None:
    assert next_objective(SEQUENCE, set(), set()).id == "talk"


def test_flag_completes_talk_objective() -> None:
    assert next_objective(SEQUENCE, {"got_starter"}, set()).id == "ghazal"


def test_defeat_completes_objective() -> None:
    assert next_objective(SEQUENCE, {"got_starter"}, {"ghazal_reem"}).id == "wolf"


def test_all_done_returns_none() -> None:
    assert next_objective(SEQUENCE, {"got_starter"}, {"ghazal_reem", "wolf"}) is None


def test_done_types_are_distinct() -> None:
    flag_obj, defeat_obj = SEQUENCE[0], SEQUENCE[1]
    assert is_done(flag_obj, {"got_starter"}, set())
    assert not is_done(flag_obj, set(), {"got_starter"})
    assert is_done(defeat_obj, set(), {"ghazal_reem"})
    assert not is_done(defeat_obj, {"ghazal_reem"}, set())


POINTS = {"village_01": {"fields": (4.0, 3.0, 3.0), "elder": (10.0, 8.0, 1.5)}}
GATES = {"village_01": {"dinder_01": (0.0, 9.0, 0.5)}}


def test_same_map_resolves_to_zone_point() -> None:
    assert resolve_point(SEQUENCE[1], "village_01", POINTS, GATES) == (4.0, 3.0, 3.0)


def test_other_map_resolves_to_gate() -> None:
    assert resolve_point(SEQUENCE[2], "village_01", POINTS, GATES) == (0.0, 9.0, 0.5)


def test_missing_gate_resolves_to_none() -> None:
    assert resolve_point(SEQUENCE[2], "dinder_01", POINTS, GATES) is None


def test_direction_is_unit_vector() -> None:
    vector = direction((0.0, 0.0), (3.0, 4.0))
    assert vector is not None
    assert abs(vector[0] - 0.6) < 1e-9 and abs(vector[1] - 0.8) < 1e-9


def test_direction_none_at_same_point() -> None:
    assert direction((2.0, 2.0), (2.0, 2.0)) is None


def test_reached_inside_radius_only() -> None:
    assert has_reached((4.0, 3.0, 3.0), (5.0, 3.0))
    assert not has_reached((4.0, 3.0, 3.0), (9.0, 3.0))


def test_game_state_progress_drives_next_objective() -> None:
    state = GameState(player_name="الأمين", map_id="village_01")
    state.set_flag("got_starter")
    state.mark_defeated("ghazal_reem")
    assert next_objective(SEQUENCE, state.flags, state.defeated).id == "wolf"


def valid_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": "a",
        "text_ar": "نص",
        "map_id": "village_01",
        "target": {"type": "npc", "id": "elder"},
        "done": {"type": "flag", "id": "f"},
    }
    row.update(overrides)
    return row


def error_for(rows: list[dict[str, Any]]) -> MapValidationError:
    with pytest.raises(MapValidationError) as info:
        validate_objectives(rows, "objectives.json")
    return info.value


def test_valid_objective_loads() -> None:
    result = validate_objectives([valid_row()], "objectives.json")
    assert result[0].target_type == TARGET_NPC and result[0].done_type == DONE_FLAG


def test_unknown_target_type_is_named() -> None:
    assert error_for([valid_row(target={"type": "cave", "id": "x"})]).field == "[0].target.type"


def test_duplicate_objective_id_rejected() -> None:
    assert error_for([valid_row(), valid_row()]).field == "[1].id"


def test_unknown_done_type_is_named() -> None:
    assert error_for([valid_row(done={"type": "magic", "id": "x"})]).field == "[0].done.type"


def test_real_objectives_match_maps_and_catalog() -> None:
    maps = {
        "village_01": load_map_file(resource_path("data", "maps", "village_01.json")),
        "dinder_01": load_map_file(resource_path("data", "maps", "dinder_01.json")),
    }
    catalog = load_catalog(
        resource_path("data", "animals.json"), resource_path("data", "moves.json")
    )
    from src.utils.data_loader import load_objectives_file

    objectives = load_objectives_file(resource_path("data", "objectives.json"))
    check_objectives(objectives, maps, catalog, "objectives.json")
    assert [o.id for o in objectives] == [
        "meet_elder", "find_ghazal", "find_timsah", "find_wolf", "find_leopard", "find_lion",
    ]


def test_real_guide_has_gates_both_ways() -> None:
    maps = {
        "village_01": load_map_file(resource_path("data", "maps", "village_01.json")),
        "dinder_01": load_map_file(resource_path("data", "maps", "dinder_01.json")),
    }
    from src.utils.data_loader import load_objectives_file

    guide = build_guide(maps, load_objectives_file(resource_path("data", "objectives.json")))
    assert guide.gates["village_01"]["dinder_01"][:2] == (0.0, 9.0)
    assert guide.gates["dinder_01"]["village_01"][:2] == (29.0, 9.0)
    assert "elder_tayeb" in guide.points["village_01"]
