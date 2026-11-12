"""اختبارات مكدس المشاهد: ترتيب الدورة وتوجيه الأفعال والرسم."""

from __future__ import annotations

import pytest
from src.core.scene import Scene
from src.core.scene_stack import EmptySceneStackError, SceneStack


class Recorder(Scene):
    def __init__(self, name: str, log: list[str], opaque: bool = True) -> None:
        self.name = name
        self.log = log
        self.opaque = opaque

    def on_enter(self) -> None:
        self.log.append(f"enter:{self.name}")

    def on_exit(self) -> None:
        self.log.append(f"exit:{self.name}")

    def on_pause(self) -> None:
        self.log.append(f"pause:{self.name}")

    def on_resume(self) -> None:
        self.log.append(f"resume:{self.name}")

    def update(self, dt: float) -> None:
        self.log.append(f"update:{self.name}")

    def handle_action(self, action: str) -> None:
        self.log.append(f"act:{self.name}:{action}")

    def draw(self, surface: object) -> None:
        self.log.append(f"draw:{self.name}")


def test_push_pauses_previous_and_enters_new() -> None:
    log: list[str] = []
    stack = SceneStack()
    stack.push(Recorder("map", log))
    stack.push(Recorder("dialogue", log))
    assert log == ["enter:map", "pause:map", "enter:dialogue"]


def test_pop_exits_top_and_resumes_below() -> None:
    log: list[str] = []
    stack = SceneStack()
    stack.push(Recorder("map", log))
    stack.push(Recorder("dialogue", log))
    log.clear()
    removed = stack.pop()
    assert removed.name == "dialogue"  # type: ignore[attr-defined]
    assert log == ["exit:dialogue", "resume:map"]


def test_replace_swaps_top_without_resuming_old() -> None:
    log: list[str] = []
    stack = SceneStack()
    stack.push(Recorder("menu", log))
    stack.push(Recorder("map", log))
    log.clear()
    stack.replace(Recorder("battle", log))
    assert log == ["exit:map", "enter:battle"]
    assert len(stack) == 2


def test_only_top_receives_update_and_actions() -> None:
    log: list[str] = []
    stack = SceneStack()
    stack.push(Recorder("map", log))
    stack.push(Recorder("dialogue", log))
    log.clear()
    stack.update(1 / 60)
    stack.dispatch_action("confirm")
    assert log == ["update:dialogue", "act:dialogue:confirm"]


def test_pop_on_empty_stack_raises() -> None:
    with pytest.raises(EmptySceneStackError):
        SceneStack().pop()


def test_top_on_empty_stack_raises() -> None:
    with pytest.raises(EmptySceneStackError):
        _ = SceneStack().top


def test_is_empty_after_last_pop() -> None:
    stack = SceneStack()
    stack.push(Recorder("menu", []))
    assert not stack.is_empty
    stack.pop()
    assert stack.is_empty


def test_visible_stops_at_opaque_scene() -> None:
    log: list[str] = []
    stack = SceneStack()
    stack.push(Recorder("base", log))
    stack.push(Recorder("top", log))
    assert [s.name for s in stack.visible()] == ["top"]  # type: ignore[attr-defined]


def test_visible_includes_scenes_under_transparent_overlay() -> None:
    log: list[str] = []
    stack = SceneStack()
    stack.push(Recorder("map", log))
    stack.push(Recorder("dialogue", log, opaque=False))
    stack.push(Recorder("menu-hint", log, opaque=False))
    names = [s.name for s in stack.visible()]  # type: ignore[attr-defined]
    assert names == ["map", "dialogue", "menu-hint"]
