"""اختبارات تكامل: تدفّق اللعبة على البيانات الفعلية كاملة، بلا pygame."""

from __future__ import annotations

import random
from typing import Any

import pytest
from src.core.event_system import (
    ON_INTERACT,
    ON_MAP_ENTER,
    ON_STEP,
    Command,
    EventRunner,
    EventSpec,
    ShowDialogue,
    Teleport,
    Trigger,
    select_event,
)
from src.core.game_state import GameState
from src.logic.battle_engine import ACTION_ATTACK, ACTION_SPECIAL, BattleEngine
from src.logic.models import AnimalInstance
from src.utils.data_loader import (
    MapValidationError,
    check_animal_refs,
    check_event_dialogues,
    check_npc_dialogues,
    check_party_refs,
    check_teleport_refs,
    load_catalog,
    load_dialogues_file,
    load_map_file,
    load_new_game_file,
    validate_map,
)
from src.utils.paths import resource_path
from src.world.encounters import roll_encounter


def _load_world() -> dict[str, Any]:
    maps = {
        "village_01": load_map_file(resource_path("data", "maps", "village_01.json")),
        "dinder_01": load_map_file(resource_path("data", "maps", "dinder_01.json")),
    }
    return {
        "maps": maps,
        "dialogues": load_dialogues_file(resource_path("data", "dialogues.json")),
        "catalog": load_catalog(
            resource_path("data", "animals.json"), resource_path("data", "moves.json")
        ),
        "new_game": load_new_game_file(resource_path("data", "new_game.json")),
    }


WORLD = _load_world()


def fresh_state() -> GameState:
    state = GameState(
        player_name=WORLD["new_game"].player_name,
        map_id="village_01",
        templates=WORLD["catalog"].animals,
    )
    state.grid_x, state.grid_y = WORLD["maps"]["village_01"].spawn
    return state


def run_to_end(event: EventSpec, state: GameState) -> list[Command]:
    runner = EventRunner()
    runner.start(event, state)
    commands: list[Command] = []
    while (command := runner.next_command()) is not None:
        commands.append(command)
    return commands


def pick(map_id: str, trigger: Trigger, state: GameState) -> EventSpec:
    event = select_event(WORLD["maps"][map_id].events, trigger, state)
    assert event is not None, f"لم يُختر حدث للمحفز {trigger}"
    return event


def test_all_data_is_consistent() -> None:
    for map_id, spec in WORLD["maps"].items():
        source = f"{map_id}.json"
        check_npc_dialogues(spec, WORLD["dialogues"], source)
        check_event_dialogues(spec, WORLD["dialogues"], source)
        check_animal_refs(spec, WORLD["catalog"], source)
        check_teleport_refs(spec, WORLD["maps"], source)
    check_party_refs(WORLD["new_game"], WORLD["catalog"], "new_game.json")


def test_arrival_plays_once() -> None:
    state = fresh_state()
    assert run_to_end(pick("village_01", Trigger(ON_MAP_ENTER), state), state) == [
        ShowDialogue("village_arrival"),
        ShowDialogue("amin_arrival"),
    ]
    assert select_event(WORLD["maps"]["village_01"].events, Trigger(ON_MAP_ENTER), state) is None


def test_first_meeting_gives_starter_then_return_visit() -> None:
    state = fresh_state()
    trigger = Trigger(ON_INTERACT, npc_id="elder_tayeb")
    assert run_to_end(pick("village_01", trigger, state), state) == [
        ShowDialogue("elder_tayeb")
    ]
    assert [animal.id for animal in state.party] == ["saqr_jedi"]
    assert run_to_end(pick("village_01", trigger, state), state) == [
        ShowDialogue("elder_return")
    ]


def test_gate_to_dinder_opens_only_after_starter() -> None:
    state = fresh_state()
    gate = Trigger(ON_STEP, x=0, y=9)
    assert select_event(WORLD["maps"]["village_01"].events, gate, state) is None
    state.set_flag("got_starter")
    commands = run_to_end(pick("village_01", gate, state), state)
    assert commands == [ShowDialogue("dinder_entry"), Teleport("dinder_01", 28, 9)]


def test_dinder_exit_returns_to_village() -> None:
    state = fresh_state()
    commands = run_to_end(pick("dinder_01", Trigger(ON_STEP, x=29, y=9), state), state)
    assert commands == [Teleport("village_01", 1, 9)]


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_wild_battle_always_terminates(seed: int) -> None:
    state = fresh_state()
    state.give_animal("saqr_jedi")
    lead = state.lead()
    assert lead is not None
    enemy = AnimalInstance.fresh(WORLD["catalog"].animals["asad_dinder"])
    engine = BattleEngine([lead], enemy, WORLD["catalog"].moves, random.Random(seed))
    for turn in range(300):
        if engine.outcome is not None:
            break
        engine.turn(ACTION_SPECIAL if turn % 2 else ACTION_ATTACK)
    assert engine.outcome in {"won", "lost"}
    assert lead.current_hp >= 0 and enemy.current_hp >= 0


def test_savanna_produces_encounters() -> None:
    zones = WORLD["maps"]["dinder_01"].encounter_zones
    rng = random.Random(7)
    seen = {roll_encounter(zones, 5, 4, rng) for _ in range(500)}
    seen.discard(None)
    assert seen and seen <= {"ghazal_reem", "wolf", "leopard"}


def test_losing_restores_party_to_full() -> None:
    state = fresh_state()
    state.give_animal("saqr_jedi")
    lead = state.lead()
    assert lead is not None
    lead.current_hp = 1
    state.heal_party()
    assert lead.current_hp == lead.max_hp


def test_teleport_to_missing_map_is_rejected() -> None:
    data: dict[str, Any] = {
        "width": 3,
        "height": 1,
        "tile_legend": {".": {"name": "grass", "solid": False, "color": [1, 2, 3]}},
        "grid": ["..."],
        "spawn": {"x": 0, "y": 0},
        "npcs": [],
        "events": [
            {
                "id": "lost",
                "trigger": {"type": "on_step", "x": 0, "y": 0},
                "conditions": [],
                "actions": [{"type": "teleport", "map_id": "ghost", "x": 0, "y": 0}],
            }
        ],
    }
    spec = validate_map(data, "map.json")
    with pytest.raises(MapValidationError) as info:
        check_teleport_refs(spec, {"self": spec}, "map.json")
    assert info.value.field == "events[0].actions"
