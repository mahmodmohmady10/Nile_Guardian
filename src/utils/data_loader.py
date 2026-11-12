"""تحميل ملفات الخرائط والتحقق منها قبل أن تصل إلى المنطق."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.world.tilemap import TileType

REQUIRED_FIELDS = ("width", "height", "tile_legend", "grid", "spawn", "npcs", "events")


class MapValidationError(ValueError):
    """خطأ تحقق يذكر الملف والحقل والسبب."""

    def __init__(self, source: str, field: str, message: str) -> None:
        super().__init__(f"{source} — الحقل '{field}': {message}")
        self.source = source
        self.field = field


@dataclass(frozen=True)
class NpcSpec:
    id: str
    name_ar: str
    x: int
    y: int
    event_id: str | None


@dataclass(frozen=True)
class MapSpec:
    width: int
    height: int
    legend: dict[str, TileType]
    rows: list[str]
    spawn: tuple[int, int]
    npcs: list[NpcSpec]
    events: list[dict[str, Any]]


def load_map_file(path: Path) -> MapSpec:
    source = path.name
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MapValidationError(source, "<file>", f"تعذر قراءة الملف: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MapValidationError(source, "<json>", f"صياغة JSON غير صحيحة: {exc}") from exc
    return validate_map(data, source)


def validate_map(data: Any, source: str) -> MapSpec:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise MapValidationError(source, field, "حقل إلزامي مفقود")
    width = _positive_int(data, "width", source)
    height = _positive_int(data, "height", source)
    legend = _parse_legend(data["tile_legend"], source)
    rows = _parse_grid(data["grid"], width, height, legend, source)
    spawn = _parse_point(data["spawn"], "spawn", width, height, source)
    if legend[rows[spawn[1]][spawn[0]]].solid:
        raise MapValidationError(source, "spawn", "نقطة الظهور تقع على بلاطة صلبة")
    events = _parse_events(data["events"], source)
    event_ids = {event["id"] for event in events}
    npcs = _parse_npcs(data["npcs"], width, height, legend, rows, event_ids, source)
    return MapSpec(width, height, legend, rows, spawn, npcs, events)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _positive_int(data: dict[str, Any], field: str, source: str) -> int:
    value = data[field]
    if not _is_int(value) or value <= 0:
        raise MapValidationError(source, field, "يجب أن يكون عدداً صحيحاً موجباً")
    return value


def _parse_legend(value: Any, source: str) -> dict[str, TileType]:
    if not isinstance(value, dict) or not value:
        raise MapValidationError(source, "tile_legend", "يجب أن يكون كائناً غير فارغ")
    legend: dict[str, TileType] = {}
    for symbol, spec in value.items():
        field = f"tile_legend.{symbol}"
        if len(symbol) != 1:
            raise MapValidationError(source, field, "الرمز يجب أن يكون حرفاً واحداً")
        if not isinstance(spec, dict):
            raise MapValidationError(source, field, "يجب أن يكون كائناً")
        name, solid, color = spec.get("name"), spec.get("solid"), spec.get("color")
        if not isinstance(name, str) or not name:
            raise MapValidationError(source, f"{field}.name", "اسم البلاطة مطلوب ونصّي")
        if not isinstance(solid, bool):
            raise MapValidationError(source, f"{field}.solid", "يجب أن يكون true أو false")
        if (
            not isinstance(color, list)
            or len(color) != 3
            or not all(_is_int(c) and 0 <= c <= 255 for c in color)
        ):
            raise MapValidationError(source, f"{field}.color", "[R, G, B] بقيم 0 إلى 255")
        legend[symbol] = TileType(name=name, solid=solid, color=(color[0], color[1], color[2]))
    return legend


def _parse_grid(
    value: Any, width: int, height: int, legend: dict[str, TileType], source: str
) -> list[str]:
    if not isinstance(value, list) or len(value) != height:
        raise MapValidationError(source, "grid", f"يجب أن يحتوي على {height} صفاً بالضبط")
    rows: list[str] = []
    for y, row in enumerate(value):
        field = f"grid[{y}]"
        if not isinstance(row, str) or len(row) != width:
            raise MapValidationError(source, field, f"يجب أن يكون نصاً من {width} حرفاً")
        for x, symbol in enumerate(row):
            if symbol not in legend:
                raise MapValidationError(
                    source, field, f"الرمز '{symbol}' في العمود {x} غير معرّف في tile_legend"
                )
        rows.append(row)
    return rows


def _parse_point(
    value: Any, field: str, width: int, height: int, source: str
) -> tuple[int, int]:
    if not isinstance(value, dict):
        raise MapValidationError(source, field, "يجب أن يكون كائناً يحوي x و y")
    x, y = value.get("x"), value.get("y")
    if not _is_int(x) or not _is_int(y):
        raise MapValidationError(source, field, "x و y يجب أن يكونا عددين صحيحين")
    if not (0 <= x < width and 0 <= y < height):
        raise MapValidationError(source, field, "الإحداثيات خارج حدود الخريطة")
    return x, y


def _parse_events(value: Any, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise MapValidationError(source, "events", "يجب أن تكون قائمة")
    seen: set[str] = set()
    events: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        field = f"events[{index}].id"
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise MapValidationError(source, field, "معرّف الحدث مطلوب ونصّي")
        if item["id"] in seen:
            raise MapValidationError(source, field, f"معرّف مكرر: {item['id']}")
        seen.add(item["id"])
        events.append(item)
    return events


def _parse_npcs(
    value: Any,
    width: int,
    height: int,
    legend: dict[str, TileType],
    rows: list[str],
    event_ids: set[str],
    source: str,
) -> list[NpcSpec]:
    if not isinstance(value, list):
        raise MapValidationError(source, "npcs", "يجب أن تكون قائمة")
    seen: set[str] = set()
    npcs: list[NpcSpec] = []
    for index, item in enumerate(value):
        field = f"npcs[{index}]"
        if not isinstance(item, dict):
            raise MapValidationError(source, field, "يجب أن يكون كائناً")
        npc_id, name, event_id = item.get("id"), item.get("name_ar"), item.get("event_id")
        if not isinstance(npc_id, str) or not npc_id:
            raise MapValidationError(source, f"{field}.id", "معرّف الشخصية مطلوب ونصّي")
        if npc_id in seen:
            raise MapValidationError(source, f"{field}.id", f"معرّف مكرر: {npc_id}")
        if not isinstance(name, str) or not name:
            raise MapValidationError(source, f"{field}.name_ar", "الاسم العربي مطلوب")
        x, y = _parse_point(item, field, width, height, source)
        if legend[rows[y][x]].solid:
            raise MapValidationError(source, field, "موقع الشخصية على بلاطة صلبة")
        if event_id is not None and event_id not in event_ids:
            raise MapValidationError(
                source, f"{field}.event_id", f"يشير إلى حدث غير موجود: {event_id}"
            )
        seen.add(npc_id)
        npcs.append(NpcSpec(npc_id, name, x, y, event_id))
    return npcs
