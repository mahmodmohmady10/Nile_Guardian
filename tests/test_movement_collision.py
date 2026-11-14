"""اختبارات الحركة والاصطدام على الشبكة (بلا pygame)."""

from __future__ import annotations

import pytest
from src.world.player_controller import PlayerController
from src.world.tilemap import TileMap, TileType

STEP = 1.0 / 60.0
SECONDS_PER_TILE = 0.15
GRASS = TileType("grass", False, (0, 0, 0))
TREE = TileType("tree", True, (0, 0, 0))
LEGEND = {".": GRASS, "#": TREE}


def run(ctrl: PlayerController, can_enter, steps: int) -> None:  # type: ignore[no-untyped-def]
    for _ in range(steps):
        ctrl.update(STEP, can_enter)


def open_field(x: int, y: int) -> bool:
    return True


def test_one_tile_takes_nine_steps() -> None:
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, open_field, 8)
    assert ctrl.x == 0 and ctrl.is_moving
    run(ctrl, open_field, 1)
    assert ctrl.x == 1


def test_continuous_hold_moves_tile_after_tile() -> None:
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, open_field, 27)
    assert ctrl.x == 3 and ctrl.is_moving


def test_blocked_tile_keeps_player_and_turns_to_face() -> None:
    ctrl = PlayerController(1, 1, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, lambda x, y: (x, y) != (2, 1), 20)
    assert (ctrl.x, ctrl.y) == (1, 1)
    assert not ctrl.is_moving
    assert ctrl.facing == "right"


def test_release_stops_after_current_tile_completes() -> None:
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, open_field, 4)
    ctrl.set_held(())
    run(ctrl, open_field, 5)
    assert ctrl.x == 1 and not ctrl.is_moving
    run(ctrl, open_field, 9)
    assert ctrl.x == 1


def test_direction_change_applies_after_completion() -> None:
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, open_field, 4)
    ctrl.set_held(("down",))
    run(ctrl, open_field, 5)
    assert (ctrl.x, ctrl.y) == (1, 0)
    assert ctrl.is_moving and ctrl.facing == "down"
    run(ctrl, open_field, 9)
    assert (ctrl.x, ctrl.y) == (1, 1)


def test_last_pressed_direction_wins() -> None:
    ctrl = PlayerController(2, 0, SECONDS_PER_TILE)
    ctrl.set_held(("left", "right"))
    run(ctrl, open_field, 9)
    assert ctrl.x == 3


def test_idle_without_input_does_not_move() -> None:
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    run(ctrl, open_field, 30)
    assert (ctrl.x, ctrl.y) == (0, 0) and not ctrl.is_moving


def test_visual_position_interpolates_within_tile() -> None:
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, open_field, 4)
    visual_x, visual_y = ctrl.visual_position()
    assert abs(visual_x - 4 / 9) < 1e-6 and visual_y == 0.0


def test_non_positive_speed_rejected() -> None:
    with pytest.raises(ValueError):
        PlayerController(0, 0, 0.0)


def test_tilemap_blocks_trees_and_bounds() -> None:
    tiles = TileMap(3, 1, ["..#"], LEGEND)
    assert not tiles.is_solid(0, 0)
    assert tiles.is_solid(2, 0)
    assert tiles.is_solid(-1, 0)
    assert tiles.is_solid(3, 0)


def test_player_cannot_walk_into_tree() -> None:
    tiles = TileMap(3, 1, ["..#"], LEGEND)
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, lambda x, y: not tiles.is_solid(x, y), 60)
    assert ctrl.x == 1 and not ctrl.is_moving


def test_tilemap_rejects_mismatched_rows() -> None:
    with pytest.raises(ValueError):
        TileMap(3, 2, ["..."], LEGEND)


def test_arrival_is_reported_once_per_tile() -> None:
    ctrl = PlayerController(0, 0, SECONDS_PER_TILE)
    ctrl.set_held(("right",))
    run(ctrl, open_field, 9)
    assert ctrl.pop_arrival() == (1, 0)
    assert ctrl.pop_arrival() is None
