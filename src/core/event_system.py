"""نظام الأحداث التصريحي: محفزات وشروط وأفعال، ومشغّل يستأنف بعد كل أمر (بلا pygame).

- المحفز يُطابَق بالنوع والمعرّف أو الإحداثيات.
- الشروط تُفحص عند الإطلاق، فيُختار أول حدث تنطبق شروطه.
- الأفعال تُنفَّذ بالترتيب. الحوار والانتقال يُرجعان أمراً للمشهد، والمشغّل يستأنف بعده.
- حدث واحد يعمل في كل لحظة. أي محفز يأتي أثناء تشغيل حدث آخر يُتجاهل.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from src.core.game_state import GameState

ON_INTERACT = "on_interact"
ON_STEP = "on_step"
ON_MAP_ENTER = "on_map_enter"
TRIGGER_TYPES = (ON_INTERACT, ON_STEP, ON_MAP_ENTER)

FLAG_SET = "flag_set"
FLAG_NOT_SET = "flag_not_set"
CONDITION_TYPES = (FLAG_SET, FLAG_NOT_SET)

ACTION_DIALOGUE = "dialogue"
ACTION_SET_FLAG = "set_flag"
ACTION_GIVE_ANIMAL = "give_animal"
ACTION_TELEPORT = "teleport"
ACTION_TYPES = (ACTION_DIALOGUE, ACTION_SET_FLAG, ACTION_GIVE_ANIMAL, ACTION_TELEPORT)


@dataclass(frozen=True)
class Trigger:
    type: str
    npc_id: str | None = None
    x: int | None = None
    y: int | None = None


@dataclass(frozen=True)
class Condition:
    type: str
    flag: str


@dataclass(frozen=True)
class Action:
    type: str
    dialogue_id: str | None = None
    flag: str | None = None
    animal_id: str | None = None
    map_id: str | None = None
    x: int | None = None
    y: int | None = None


@dataclass(frozen=True)
class EventSpec:
    id: str
    trigger: Trigger
    conditions: tuple[Condition, ...]
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class ShowDialogue:
    dialogue_id: str


@dataclass(frozen=True)
class Teleport:
    map_id: str
    x: int
    y: int


Command = ShowDialogue | Teleport


def conditions_hold(event: EventSpec, state: GameState) -> bool:
    for condition in event.conditions:
        has = state.has_flag(condition.flag)
        if condition.type == FLAG_SET and not has:
            return False
        if condition.type == FLAG_NOT_SET and has:
            return False
    return True


def select_event(
    events: Iterable[EventSpec], trigger: Trigger, state: GameState
) -> EventSpec | None:
    for event in events:
        if event.trigger == trigger and conditions_hold(event, state):
            return event
    return None


def _execute(event: EventSpec, state: GameState) -> Iterator[Command]:
    for action in event.actions:
        if action.type == ACTION_SET_FLAG and action.flag is not None:
            state.set_flag(action.flag)
        elif action.type == ACTION_GIVE_ANIMAL and action.animal_id is not None:
            state.give_animal(action.animal_id)
        elif action.type == ACTION_DIALOGUE and action.dialogue_id is not None:
            yield ShowDialogue(action.dialogue_id)
        elif (
            action.type == ACTION_TELEPORT
            and action.map_id is not None
            and action.x is not None
            and action.y is not None
        ):
            yield Teleport(action.map_id, action.x, action.y)


class EventRunner:
    def __init__(self) -> None:
        self._active: Iterator[Command] | None = None

    @property
    def busy(self) -> bool:
        return self._active is not None

    def start(self, event: EventSpec, state: GameState) -> None:
        if self._active is not None:
            raise RuntimeError("حدث آخر ما زال يعمل")
        self._active = _execute(event, state)

    def next_command(self) -> Command | None:
        """يتقدم إلى الأمر التالي. None يعني أن الحدث انتهى."""
        if self._active is None:
            return None
        try:
            return next(self._active)
        except StopIteration:
            self._active = None
            return None
