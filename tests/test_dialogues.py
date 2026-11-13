"""اختبارات حالة الحوار، ومحمّل الحوارات، والربط بين الخريطة والحوارات."""

from __future__ import annotations

from typing import Any

import pytest
from src.core.dialogue import DialogueState
from src.utils.data_loader import (
    MapValidationError,
    check_npc_dialogues,
    load_dialogues_file,
    load_map_file,
    validate_dialogues,
)
from src.utils.paths import resource_path


def test_dialogue_state_advances_then_finishes() -> None:
    state = DialogueState("العم الطيب", ["أ", "ب", "ج"])
    assert state.current == "أ" and state.index == 0 and state.total == 3
    assert state.advance() is False
    assert state.advance() is False
    assert state.current == "ج"
    assert state.advance() is True


def test_dialogue_state_rejects_empty() -> None:
    with pytest.raises(ValueError):
        DialogueState("x", [])


def valid_dialogues() -> dict[str, Any]:
    return {"elder": {"speaker": "العم الطيب", "lines": ["مرحباً"]}}


def error_for(data: Any) -> MapValidationError:
    with pytest.raises(MapValidationError) as info:
        validate_dialogues(data, "dialogues.json")
    return info.value


def test_valid_dialogues_load() -> None:
    dialogues = validate_dialogues(valid_dialogues(), "dialogues.json")
    assert dialogues["elder"].speaker == "العم الطيب"
    assert dialogues["elder"].lines == ("مرحباً",)


def test_missing_speaker_is_named() -> None:
    data = valid_dialogues()
    del data["elder"]["speaker"]
    assert error_for(data).field == "elder.speaker"


def test_empty_lines_rejected() -> None:
    data = valid_dialogues()
    data["elder"]["lines"] = []
    assert error_for(data).field == "elder.lines"


def test_blank_line_names_index() -> None:
    data = valid_dialogues()
    data["elder"]["lines"] = ["ok", "   "]
    assert error_for(data).field == "elder.lines[1]"


def test_npc_without_dialogue_is_rejected() -> None:
    spec = load_map_file(resource_path("data", "maps", "village_01.json"))
    with pytest.raises(MapValidationError) as info:
        check_npc_dialogues(spec, {}, "village_01.json")
    assert info.value.field.startswith("npcs.")


def test_real_dialogues_cover_every_npc() -> None:
    spec = load_map_file(resource_path("data", "maps", "village_01.json"))
    dialogues = load_dialogues_file(resource_path("data", "dialogues.json"))
    check_npc_dialogues(spec, dialogues, "village_01.json")
    assert all(len(d.lines) >= 1 for d in dialogues.values())
