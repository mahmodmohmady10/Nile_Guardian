"""تسلسل الحالة والتحقق منها عند التحميل (بلا pygame). صيغة الحفظ رقم 1."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.core.game_state import GameState
from src.logic.models import AnimalInstance, AnimalTemplate

SAVE_VERSION = 1
FACINGS = ("up", "down", "left", "right")


class SaveError(ValueError):
    """خطأ في ملف الحفظ يذكر الحقل والسبب."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"الحفظ — الحقل '{field}': {message}")
        self.field = field


def snapshot(state: GameState) -> dict[str, Any]:
    return {
        "save_version": SAVE_VERSION,
        "player_name": state.player_name,
        "map_id": state.map_id,
        "grid_x": state.grid_x,
        "grid_y": state.grid_y,
        "facing": state.facing,
        "party": [
            {"id": animal.id, "current_hp": animal.current_hp,
             "last_stand_used": animal.last_stand_used}
            for animal in state.party
        ],
        "flags": sorted(state.flags),
        "defeated": sorted(state.defeated),
    }


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def restore(
    data: Any,
    templates: Mapping[str, AnimalTemplate],
    map_sizes: Mapping[str, tuple[int, int]],
) -> GameState:
    if not isinstance(data, dict):
        raise SaveError("<root>", "يجب أن يكون الجذر كائناً")
    if data.get("save_version") != SAVE_VERSION:
        raise SaveError("save_version", "إصدار الحفظ غير مدعوم")
    if not _is_text(data.get("player_name")):
        raise SaveError("player_name", "اسم اللاعب مطلوب")
    map_id = data.get("map_id")
    if map_id not in map_sizes:
        raise SaveError("map_id", f"خريطة غير معروفة: {map_id}")
    width, height = map_sizes[map_id]
    grid_x, grid_y = data.get("grid_x"), data.get("grid_y")
    if not _is_int(grid_x) or not 0 <= grid_x < width:
        raise SaveError("grid_x", "الإحداثي خارج الخريطة")
    if not _is_int(grid_y) or not 0 <= grid_y < height:
        raise SaveError("grid_y", "الإحداثي خارج الخريطة")
    if data.get("facing") not in FACINGS:
        raise SaveError("facing", "اتجاه غير معروف")

    party_raw = data.get("party")
    if not isinstance(party_raw, list):
        raise SaveError("party", "يجب أن يكون قائمة")
    party: list[AnimalInstance] = []
    seen: set[str] = set()
    for index, item in enumerate(party_raw):
        field = f"party[{index}]"
        if not isinstance(item, dict) or item.get("id") not in templates:
            raise SaveError(f"{field}.id", "حيوان غير معروف")
        animal_id = item["id"]
        if animal_id in seen:
            raise SaveError(f"{field}.id", f"حيوان مكرر: {animal_id}")
        seen.add(animal_id)
        template = templates[animal_id]
        hp = item.get("current_hp")
        if not _is_int(hp) or not 1 <= hp <= template.max_hp:
            raise SaveError(f"{field}.current_hp", "الصحة خارج الحدود")
        used = item.get("last_stand_used")
        if not isinstance(used, bool):
            raise SaveError(f"{field}.last_stand_used", "يجب أن يكون true أو false")
        party.append(AnimalInstance(template, hp, last_stand_used=used))

    flags = data.get("flags")
    if not isinstance(flags, list) or not all(_is_text(flag) for flag in flags):
        raise SaveError("flags", "قائمة علامات نصية مطلوبة")
    defeated = data.get("defeated")
    if not isinstance(defeated, list) or not all(
        isinstance(animal_id, str) and animal_id in templates for animal_id in defeated
    ):
        raise SaveError("defeated", "قائمة حيوانات معروفة مطلوبة")

    return GameState(
        player_name=data["player_name"],
        map_id=map_id,
        templates=dict(templates),
        grid_x=grid_x,
        grid_y=grid_y,
        facing=data["facing"],
        party=party,
        flags=set(flags),
        defeated=set(defeated),
    )
