"""اختبارات نظام الأحداث وحالة اللعبة (بلا pygame)."""

from __future__ import annotations

from src.core.event_system import (
    ACTION_DIALOGUE,
    ACTION_GIVE_ANIMAL,
    ACTION_SET_FLAG,
    FLAG_NOT_SET,
    FLAG_SET,
    ON_INTERACT,
    Action,
    Condition,
    EventRunner,
    EventSpec,
    ShowDialogue,
    Trigger,
    select_event,
)
from src.core.game_state import GameState
from src.logic.models import AnimalTemplate

SAQR = AnimalTemplate("saqr", "صقر", 40, 12, 8, 14, "peck", "dive")


def fresh_state() -> GameState:
    return GameState(player_name="الأمين", map_id="village_01", templates={"saqr": SAQR})


def interact(npc: str) -> Trigger:
    return Trigger(ON_INTERACT, npc_id=npc)


def first_meeting() -> EventSpec:
    return EventSpec(
        "first",
        interact("elder"),
        (Condition(FLAG_NOT_SET, "got"),),
        (
            Action(ACTION_DIALOGUE, dialogue_id="d1"),
            Action(ACTION_GIVE_ANIMAL, animal_id="saqr"),
            Action(ACTION_SET_FLAG, flag="got"),
        ),
    )


def return_visit() -> EventSpec:
    return EventSpec(
        "return",
        interact("elder"),
        (Condition(FLAG_SET, "got"),),
        (Action(ACTION_DIALOGUE, dialogue_id="d2"),),
    )


def test_select_picks_event_whose_conditions_hold() -> None:
    chosen = select_event((first_meeting(), return_visit()), interact("elder"), fresh_state())
    assert chosen is not None and chosen.id == "first"


def test_second_talk_selects_return_visit_after_flag() -> None:
    state = fresh_state()
    runner = EventRunner()
    runner.start(first_meeting(), state)
    assert runner.next_command() == ShowDialogue("d1")
    assert runner.next_command() is None
    chosen = select_event((first_meeting(), return_visit()), interact("elder"), state)
    assert chosen is not None and chosen.id == "return"


def test_no_event_when_trigger_does_not_match() -> None:
    assert select_event((first_meeting(),), interact("someone_else"), fresh_state()) is None


def test_actions_apply_after_dialogue_resumes() -> None:
    state = fresh_state()
    runner = EventRunner()
    runner.start(first_meeting(), state)
    assert runner.next_command() == ShowDialogue("d1")
    assert state.party == [] and not state.has_flag("got")
    assert runner.next_command() is None
    assert [animal.id for animal in state.party] == ["saqr"]
    assert state.has_flag("got") and not runner.busy


def test_runner_refuses_second_event_while_busy() -> None:
    runner = EventRunner()
    runner.start(first_meeting(), fresh_state())
    try:
        runner.start(return_visit(), fresh_state())
    except RuntimeError:
        return
    raise AssertionError("كان يجب أن يُرفض التشغيل الثاني")


def test_give_animal_does_not_duplicate() -> None:
    state = fresh_state()
    state.give_animal("saqr")
    state.give_animal("saqr")
    assert len(state.party) == 1


def test_event_with_no_dialogue_finishes_immediately() -> None:
    state = fresh_state()
    event = EventSpec(
        "silent", Trigger("on_map_enter"), (), (Action(ACTION_SET_FLAG, flag="seen"),)
    )
    runner = EventRunner()
    runner.start(event, state)
    assert runner.next_command() is None
    assert state.has_flag("seen") and not runner.busy


def test_runner_yields_teleport_command() -> None:
    from src.core.event_system import ACTION_TELEPORT, Teleport

    event = EventSpec(
        "go",
        Trigger("on_step", x=0, y=0),
        (),
        (Action(ACTION_TELEPORT, map_id="dinder_01", x=28, y=9),),
    )
    runner = EventRunner()
    runner.start(event, fresh_state())
    assert runner.next_command() == Teleport("dinder_01", 28, 9)
    assert runner.next_command() is None
