"""اختبارات الحفظ والتحميل: التسلسل، والتحقق من كل حقل، والكتابة الذرية."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from src.core.game_state import GameState
from src.core.save import SAVE_VERSION, SaveError, restore, snapshot
from src.utils.data_loader import load_catalog
from src.utils.paths import resource_path
from src.utils.saves import AUTOSAVE_ID, read_save, slot_path, write_save

CATALOG = load_catalog(resource_path("data", "animals.json"), resource_path("data", "moves.json"))
SIZES = {"village_01": (30, 18), "dinder_01": (30, 18)}


def sample_state() -> GameState:
    state = GameState(
        player_name="الأمين", map_id="dinder_01", templates=CATALOG.animals, grid_x=12, grid_y=5,
        facing="left",
    )
    state.give_animal("saqr_jedi")
    lead = state.lead()
    assert lead is not None
    lead.current_hp = 40
    lead.last_stand_used = True
    state.set_flag("got_starter")
    state.mark_defeated("ghazal_reem")
    return state


def valid_data() -> dict[str, Any]:
    return snapshot(sample_state())


def error_for(data: Any) -> SaveError:
    with pytest.raises(SaveError) as info:
        restore(data, CATALOG.animals, SIZES)
    return info.value


def test_round_trip_restores_everything() -> None:
    original = sample_state()
    restored = restore(snapshot(original), CATALOG.animals, SIZES)
    placement = (restored.player_name, restored.map_id, restored.grid_x, restored.grid_y)
    assert placement == ("الأمين", "dinder_01", 12, 5)
    assert restored.facing == "left"
    assert restored.flags == {"got_starter"} and restored.defeated == {"ghazal_reem"}
    lead = restored.lead()
    assert lead is not None and lead.id == "saqr_jedi"
    assert lead.current_hp == 40 and lead.last_stand_used is True


def test_snapshot_changes_when_progress_changes() -> None:
    state = sample_state()
    before = snapshot(state)
    state.set_flag("arrived_village")
    assert snapshot(state) != before


def test_unknown_map_is_named() -> None:
    data = valid_data()
    data["map_id"] = "moon"
    assert error_for(data).field == "map_id"


def test_unknown_animal_is_named() -> None:
    data = valid_data()
    data["party"][0]["id"] = "dragon"
    assert error_for(data).field == "party[0].id"


def test_zero_hp_is_rejected() -> None:
    data = valid_data()
    data["party"][0]["current_hp"] = 0
    assert error_for(data).field == "party[0].current_hp"


def test_hp_above_max_is_rejected() -> None:
    data = valid_data()
    data["party"][0]["current_hp"] = 9999
    assert error_for(data).field == "party[0].current_hp"


def test_out_of_bounds_position_is_rejected() -> None:
    data = valid_data()
    data["grid_x"] = 30
    assert error_for(data).field == "grid_x"


def test_invalid_facing_is_rejected() -> None:
    data = valid_data()
    data["facing"] = "sideways"
    assert error_for(data).field == "facing"


def test_wrong_version_is_rejected() -> None:
    data = valid_data()
    data["save_version"] = SAVE_VERSION + 1
    assert error_for(data).field == "save_version"


def test_flags_must_be_text_list() -> None:
    data = valid_data()
    data["flags"] = "got_starter"
    assert error_for(data).field == "flags"


def test_defeated_must_be_known_animals() -> None:
    data = valid_data()
    data["defeated"] = ["dragon"]
    assert error_for(data).field == "defeated"


def test_duplicate_party_member_is_rejected() -> None:
    data = valid_data()
    data["party"].append(dict(data["party"][0]))
    assert error_for(data).field == "party[1].id"


def test_write_then_read_round_trip_and_no_temp_left() -> None:
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        data = valid_data()
        write_save(folder, AUTOSAVE_ID, data)
        assert read_save(folder, AUTOSAVE_ID) == data
        assert not slot_path(folder, AUTOSAVE_ID).with_suffix(".tmp").exists()


def test_overwrite_replaces_previous_save() -> None:
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        write_save(folder, "slot1", valid_data())
        newer = valid_data()
        newer["grid_x"] = 3
        write_save(folder, "slot1", newer)
        assert read_save(folder, "slot1") == newer


def test_missing_slot_reads_as_none() -> None:
    with tempfile.TemporaryDirectory() as directory:
        assert read_save(Path(directory), "slot2") is None


def test_corrupt_file_raises_save_error() -> None:
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        slot_path(folder, "slot3").write_text("{not json", encoding="utf-8")
        with pytest.raises(SaveError):
            read_save(folder, "slot3")


def test_saved_file_is_utf8_json() -> None:
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        write_save(folder, "slot1", valid_data())
        loaded = json.loads(slot_path(folder, "slot1").read_text(encoding="utf-8"))
        assert loaded["player_name"] == "الأمين"
