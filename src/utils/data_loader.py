"""تحميل ملفات البيانات والتحقق منها قبل أن تصل إلى المنطق."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.event_system import (
    ACTION_DIALOGUE,
    ACTION_GIVE_ANIMAL,
    ACTION_SET_FLAG,
    ACTION_TELEPORT,
    ACTION_TYPES,
    CONDITION_TYPES,
    ON_INTERACT,
    ON_STEP,
    TRIGGER_TYPES,
    Action,
    Condition,
    EventSpec,
    Trigger,
)
from src.logic.models import AnimalTemplate, Effect, Item, LastStand, Move
from src.world.encounters import EncounterEntry, EncounterZone
from src.world.objectives import (
    DONE_DEFEATED,
    DONE_FLAG,
    TARGET_NPC,
    TARGET_ZONE,
    GuideData,
    Objective,
)
from src.world.tilemap import TileType

REQUIRED_MAP_FIELDS = ("width", "height", "tile_legend", "grid", "spawn", "npcs", "events")


class MapValidationError(ValueError):
    """خطأ تحقق يذكر الملف والحقل والسبب."""

    def __init__(self, source: str, field: str, message: str) -> None:
        super().__init__(f"{source} — الحقل '{field}': {message}")
        self.source = source
        self.field = field


@dataclass(frozen=True)
class Dialogue:
    id: str
    speaker: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class NpcSpec:
    id: str
    name_ar: str
    x: int
    y: int
    event_id: str | None
    role: str = "talk"


@dataclass(frozen=True)
class MapSpec:
    width: int
    height: int
    legend: dict[str, TileType]
    rows: list[str]
    spawn: tuple[int, int]
    npcs: list[NpcSpec]
    events: tuple[EventSpec, ...]
    encounter_zones: tuple[EncounterZone, ...]


@dataclass(frozen=True)
class NewGameSpec:
    player_name: str
    map_id: str
    party: tuple[str, ...]


@dataclass(frozen=True)
class Catalog:
    animals: dict[str, AnimalTemplate]
    moves: dict[str, Move]


def _read_json(path: Path) -> tuple[Any, str]:
    source = path.name
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MapValidationError(source, "<file>", f"تعذر قراءة الملف: {exc}") from exc
    try:
        return json.loads(text), source
    except json.JSONDecodeError as exc:
        raise MapValidationError(source, "<json>", f"صياغة JSON غير صحيحة: {exc}") from exc


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


# ---------- catalog: moves and animals ----------

def load_catalog(animals_path: Path, moves_path: Path) -> Catalog:
    moves_data, moves_source = _read_json(moves_path)
    moves = validate_moves(moves_data, moves_source)
    animals_data, animals_source = _read_json(animals_path)
    animals = validate_animals(animals_data, moves, animals_source)
    return Catalog(animals=animals, moves=moves)


EFFECT_KINDS = ("none", "extra_damage", "heal_percent", "priority_next_turn")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_moves(data: Any, source: str) -> dict[str, Move]:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    moves: dict[str, Move] = {}
    for move_id, body in data.items():
        if not isinstance(body, dict):
            raise MapValidationError(source, move_id, "يجب أن يكون كائناً")
        if not _is_text(body.get("name_ar")):
            raise MapValidationError(source, f"{move_id}.name_ar", "الاسم العربي مطلوب")
        effect = body.get("effect")
        if not isinstance(effect, dict) or effect.get("type") not in EFFECT_KINDS:
            raise MapValidationError(source, f"{move_id}.effect.type", "نوع تأثير غير معروف")
        kind = effect["type"]
        if kind == "extra_damage":
            multiplier = effect.get("multiplier")
            if not _is_number(multiplier) or multiplier <= 0:
                raise MapValidationError(source, f"{move_id}.effect.multiplier", "مضاعف موجب مطلوب")
            parsed = Effect(kind, multiplier=float(multiplier))
        elif kind == "heal_percent":
            percent = effect.get("percent")
            if not _is_int(percent) or not 1 <= percent <= 100:
                raise MapValidationError(source, f"{move_id}.effect.percent", "النسبة بين 1 و100")
            parsed = Effect(kind, percent=percent)
        else:
            parsed = Effect(kind)
        moves[move_id] = Move(move_id, body["name_ar"], parsed)
    return moves


def validate_animals(data: Any, moves: dict[str, Move], source: str) -> dict[str, AnimalTemplate]:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    animals: dict[str, AnimalTemplate] = {}
    for animal_id, body in data.items():
        field = animal_id
        if not isinstance(body, dict):
            raise MapValidationError(source, field, "يجب أن يكون كائناً")
        if not _is_text(body.get("name_ar")):
            raise MapValidationError(source, f"{field}.name_ar", "الاسم العربي مطلوب")
        for stat in ("max_hp", "attack", "defense"):
            value = body.get(stat)
            if not _is_int(value) or value <= 0:
                raise MapValidationError(source, f"{field}.{stat}", "قيمة موجبة صحيحة مطلوبة")
        speed = body.get("speed")
        if not _is_int(speed) or speed < 0:
            raise MapValidationError(source, f"{field}.speed", "سرعة صحيحة غير سالبة")
        crit_chance = body.get("crit_chance")
        if not _is_number(crit_chance) or not 0 <= crit_chance <= 1:
            raise MapValidationError(source, f"{field}.crit_chance", "فرصة بين 0 و1")
        crit_multiplier = body.get("crit_multiplier")
        if not _is_number(crit_multiplier) or crit_multiplier < 1:
            raise MapValidationError(source, f"{field}.crit_multiplier", "مضاعف حرجة 1 أو أكثر")
        vmin, vmax = body.get("variance_min"), body.get("variance_max")
        if not _is_number(vmin) or not 0 < vmin <= 1:
            raise MapValidationError(source, f"{field}.variance_min", "قيمة بين 0 و1")
        if not _is_number(vmax) or not vmin <= vmax <= 1:
            raise MapValidationError(source, f"{field}.variance_max", "يجب أن يكون بين min و1")
        flee = body.get("flee_at_percent")
        if flee is not None and (not _is_int(flee) or not 1 <= flee <= 99):
            raise MapValidationError(source, f"{field}.flee_at_percent", "نسبة بين 1 و99 أو null")
        last_raw = body.get("last_stand")
        last: LastStand | None = None
        if last_raw is not None:
            if not isinstance(last_raw, dict):
                raise MapValidationError(source, f"{field}.last_stand", "كائن أو null")
            threshold, bonus = last_raw.get("threshold_percent"), last_raw.get("bonus_percent")
            if not _is_int(threshold) or not 1 <= threshold <= 50:
                raise MapValidationError(
                    source, f"{field}.last_stand.threshold_percent", "بين 1 و50"
                )
            if not _is_int(bonus) or not 1 <= bonus <= 100:
                raise MapValidationError(source, f"{field}.last_stand.bonus_percent", "بين 1 و100")
            last = LastStand(threshold, bonus)
        catchable = body.get("catchable", True)
        reward = body.get("reward_money", 0)
        if not _is_int(reward) or reward < 0:
            raise MapValidationError(source, f"{field}.reward_money", "مكافأة صحيحة غير سالبة")
        if not isinstance(catchable, bool):
            raise MapValidationError(source, f"{field}.catchable", "يجب أن يكون true أو false")
        for slot in ("basic_move", "special_move"):
            if body.get(slot) not in moves:
                raise MapValidationError(
                    source, f"{field}.{slot}", f"حركة غير موجودة: {body.get(slot)}"
                )
        animals[animal_id] = AnimalTemplate(
            id=animal_id,
            name_ar=body["name_ar"],
            max_hp=body["max_hp"],
            attack=body["attack"],
            defense=body["defense"],
            speed=speed,
            basic_move=body["basic_move"],
            special_move=body["special_move"],
            crit_chance=float(crit_chance),
            crit_multiplier=float(crit_multiplier),
            variance_min=float(vmin),
            variance_max=float(vmax),
            flee_at_percent=flee,
            last_stand=last,
            catchable=catchable,
            reward_money=reward,
        )
    return animals


# ---------- map ----------

def load_map_file(path: Path) -> MapSpec:
    data, source = _read_json(path)
    return validate_map(data, source)


def validate_map(data: Any, source: str) -> MapSpec:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    for field in REQUIRED_MAP_FIELDS:
        if field not in data:
            raise MapValidationError(source, field, "حقل إلزامي مفقود")
    width = _positive_int(data, "width", source)
    height = _positive_int(data, "height", source)
    legend = _parse_legend(data["tile_legend"], source)
    rows = _parse_grid(data["grid"], width, height, legend, source)
    spawn = _parse_point(data["spawn"], "spawn", width, height, source)
    if legend[rows[spawn[1]][spawn[0]]].solid:
        raise MapValidationError(source, "spawn", "نقطة الظهور تقع على بلاطة صلبة")
    events = _parse_events(data["events"], width, height, source)
    event_ids = {event.id for event in events}
    npcs = _parse_npcs(data["npcs"], width, height, legend, rows, event_ids, source)
    npc_ids = {npc.id for npc in npcs}
    for index, event in enumerate(events):
        if event.trigger.type == ON_INTERACT and event.trigger.npc_id not in npc_ids:
            raise MapValidationError(
                source, f"events[{index}].trigger.npc_id", "لا توجد شخصية بهذا المعرّف"
            )
    zones = _parse_zones(data.get("encounter_zones", []), width, height, source)
    return MapSpec(width, height, legend, rows, spawn, npcs, events, zones)


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
        if not _is_text(name):
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


def _parse_zones(value: Any, width: int, height: int, source: str) -> tuple[EncounterZone, ...]:
    if not isinstance(value, list):
        raise MapValidationError(source, "encounter_zones", "يجب أن تكون قائمة")
    zones: list[EncounterZone] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        field = f"encounter_zones[{index}]"
        if not isinstance(item, dict) or not _is_text(item.get("id")):
            raise MapValidationError(source, f"{field}.id", "معرّف المنطقة مطلوب ونصّي")
        zone_id = item["id"]
        if zone_id in seen:
            raise MapValidationError(source, f"{field}.id", f"معرّف مكرر: {zone_id}")
        seen.add(zone_id)
        x, y = _parse_point(item, field, width, height, source)
        zone_w, zone_h = item.get("width"), item.get("height")
        if not _is_int(zone_w) or not _is_int(zone_h) or zone_w <= 0 or zone_h <= 0:
            raise MapValidationError(source, field, "العرض والارتفاع موجبان وصحيحان")
        if x + zone_w > width or y + zone_h > height:
            raise MapValidationError(source, field, "المنطقة تتجاوز حدود الخريطة")
        rate = item.get("rate_percent")
        if not _is_int(rate) or not 0 <= rate <= 100:
            raise MapValidationError(source, f"{field}.rate_percent", "النسبة بين 0 و100")
        table_raw = item.get("table")
        if not isinstance(table_raw, list) or not table_raw:
            raise MapValidationError(source, f"{field}.table", "جدول حيوانات غير فارغ مطلوب")
        table: list[EncounterEntry] = []
        for row, entry in enumerate(table_raw):
            entry_field = f"{field}.table[{row}]"
            if not isinstance(entry, dict) or not _is_text(entry.get("animal_id")):
                raise MapValidationError(source, entry_field, "معرّف الحيوان مطلوب")
            weight = entry.get("weight")
            if not _is_int(weight) or weight <= 0:
                raise MapValidationError(source, f"{entry_field}.weight", "وزن موجب صحيح")
            table.append(EncounterEntry(entry["animal_id"], weight))
        zones.append(EncounterZone(zone_id, x, y, zone_w, zone_h, rate, tuple(table)))
    return tuple(zones)


def _parse_events(value: Any, width: int, height: int, source: str) -> tuple[EventSpec, ...]:
    if not isinstance(value, list):
        raise MapValidationError(source, "events", "يجب أن تكون قائمة")
    seen: set[str] = set()
    events: list[EventSpec] = []
    for index, item in enumerate(value):
        field = f"events[{index}]"
        if not isinstance(item, dict):
            raise MapValidationError(source, field, "يجب أن يكون كائناً")
        event_id = item.get("id")
        if not _is_text(event_id):
            raise MapValidationError(source, f"{field}.id", "معرّف الحدث مطلوب ونصّي")
        if event_id in seen:
            raise MapValidationError(source, f"{field}.id", f"معرّف مكرر: {event_id}")
        seen.add(event_id)
        trigger = _parse_trigger(item.get("trigger"), field, width, height, source)
        conditions = _parse_conditions(item.get("conditions"), field, source)
        actions = _parse_actions(item.get("actions"), field, source)
        events.append(EventSpec(event_id, trigger, conditions, actions))
    return tuple(events)


def _parse_trigger(value: Any, field: str, width: int, height: int, source: str) -> Trigger:
    if not isinstance(value, dict):
        raise MapValidationError(source, f"{field}.trigger", "المحفّز مطلوب ككائن")
    kind = value.get("type")
    if kind not in TRIGGER_TYPES:
        raise MapValidationError(source, f"{field}.trigger.type", f"نوع محفّز غير معروف: {kind}")
    if kind == ON_INTERACT:
        npc_id = value.get("npc_id")
        if not _is_text(npc_id):
            raise MapValidationError(source, f"{field}.trigger.npc_id", "معرّف الشخصية مطلوب")
        return Trigger(kind, npc_id=npc_id)
    if kind == ON_STEP:
        x, y = value.get("x"), value.get("y")
        if not _is_int(x) or not _is_int(y) or not (0 <= x < width and 0 <= y < height):
            raise MapValidationError(source, f"{field}.trigger", "إحداثيات البلاطة غير صالحة")
        return Trigger(kind, x=x, y=y)
    return Trigger(kind)


def _parse_conditions(value: Any, field: str, source: str) -> tuple[Condition, ...]:
    if not isinstance(value, list):
        raise MapValidationError(source, f"{field}.conditions", "يجب أن تكون قائمة (قد تكون فارغة)")
    conditions: list[Condition] = []
    for index, item in enumerate(value):
        item_field = f"{field}.conditions[{index}]"
        if not isinstance(item, dict) or item.get("type") not in CONDITION_TYPES:
            raise MapValidationError(source, f"{item_field}.type", "شرط غير معروف")
        if not _is_text(item.get("flag")):
            raise MapValidationError(source, f"{item_field}.flag", "اسم العلامة مطلوب")
        conditions.append(Condition(item["type"], item["flag"]))
    return tuple(conditions)


def _parse_actions(value: Any, field: str, source: str) -> tuple[Action, ...]:
    if not isinstance(value, list) or not value:
        raise MapValidationError(source, f"{field}.actions", "قائمة أفعال غير فارغة مطلوبة")
    actions: list[Action] = []
    for index, item in enumerate(value):
        item_field = f"{field}.actions[{index}]"
        kind = item.get("type") if isinstance(item, dict) else None
        if kind not in ACTION_TYPES:
            raise MapValidationError(
                source, f"{item_field}.type", f"فعل غير معروف أو غير مدعوم بعد: {kind}"
            )
        if kind == ACTION_DIALOGUE:
            if not _is_text(item.get("dialogue_id")):
                raise MapValidationError(source, f"{item_field}.dialogue_id", "معرّف الحوار مطلوب")
            actions.append(Action(kind, dialogue_id=item["dialogue_id"]))
        elif kind == ACTION_SET_FLAG:
            if not _is_text(item.get("flag")):
                raise MapValidationError(source, f"{item_field}.flag", "اسم العلامة مطلوب")
            actions.append(Action(kind, flag=item["flag"]))
        elif kind == ACTION_GIVE_ANIMAL:
            if not _is_text(item.get("animal_id")):
                raise MapValidationError(source, f"{item_field}.animal_id", "معرّف الحيوان مطلوب")
            actions.append(Action(kind, animal_id=item["animal_id"]))
        elif kind == ACTION_TELEPORT:
            map_id, x, y = item.get("map_id"), item.get("x"), item.get("y")
            if not _is_text(map_id):
                raise MapValidationError(source, f"{item_field}.map_id", "معرّف الخريطة مطلوب")
            if not _is_int(x) or not _is_int(y):
                raise MapValidationError(source, item_field, "x و y يجب أن يكونا عددين صحيحين")
            actions.append(Action(kind, map_id=map_id, x=x, y=y))
    return tuple(actions)


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
        if not _is_text(npc_id):
            raise MapValidationError(source, f"{field}.id", "معرّف الشخصية مطلوب ونصّي")
        if npc_id in seen:
            raise MapValidationError(source, f"{field}.id", f"معرّف مكرر: {npc_id}")
        if not _is_text(name):
            raise MapValidationError(source, f"{field}.name_ar", "الاسم العربي مطلوب")
        x, y = _parse_point(item, field, width, height, source)
        if legend[rows[y][x]].solid:
            raise MapValidationError(source, field, "موقع الشخصية على بلاطة صلبة")
        if event_id is not None and event_id not in event_ids:
            raise MapValidationError(
                source, f"{field}.event_id", f"يشير إلى حدث غير موجود: {event_id}"
            )
        seen.add(npc_id)
        role = item.get("role", "talk")
        if role not in ("talk", "shop", "hospital"):
            raise MapValidationError(source, f"{field}.role", "talk أو shop أو hospital")
        npcs.append(NpcSpec(npc_id, name, x, y, event_id, role))
    return npcs


# ---------- dialogues ----------

def load_dialogues_file(path: Path) -> dict[str, Dialogue]:
    data, source = _read_json(path)
    return validate_dialogues(data, source)


def validate_dialogues(data: Any, source: str) -> dict[str, Dialogue]:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    dialogues: dict[str, Dialogue] = {}
    for dialogue_id, body in data.items():
        if not _is_text(dialogue_id):
            raise MapValidationError(source, "<key>", "معرّف الحوار لا يمكن أن يكون فارغاً")
        if not isinstance(body, dict):
            raise MapValidationError(source, dialogue_id, "يجب أن يكون كائناً")
        speaker, lines = body.get("speaker"), body.get("lines")
        if not _is_text(speaker):
            raise MapValidationError(source, f"{dialogue_id}.speaker", "اسم المتحدث مطلوب")
        if not isinstance(lines, list) or not lines:
            raise MapValidationError(source, f"{dialogue_id}.lines", "قائمة أسطر غير فارغة مطلوبة")
        for index, line in enumerate(lines):
            if not _is_text(line):
                raise MapValidationError(source, f"{dialogue_id}.lines[{index}]", "سطر فارغ")
        dialogues[dialogue_id] = Dialogue(dialogue_id, speaker, tuple(lines))
    return dialogues


# ---------- cross references ----------

def check_npc_dialogues(spec: MapSpec, dialogues: dict[str, Dialogue], source: str) -> None:
    for npc in spec.npcs:
        if npc.role == "talk" and npc.id not in dialogues:
            raise MapValidationError(
                source, f"npcs.{npc.id}", "لا يوجد حوار بهذا المعرّف في dialogues.json"
            )


def check_event_dialogues(spec: MapSpec, dialogues: dict[str, Dialogue], source: str) -> None:
    for index, event in enumerate(spec.events):
        for action in event.actions:
            if action.type == ACTION_DIALOGUE and action.dialogue_id not in dialogues:
                raise MapValidationError(
                    source,
                    f"events[{index}].actions",
                    f"حوار غير موجود في dialogues.json: {action.dialogue_id}",
                )


def check_animal_refs(spec: MapSpec, catalog: Catalog, source: str) -> None:
    """كل حيوان يُذكر في مناطق المواجهة أو في الأحداث يجب أن يكون معرّفاً في animals.json."""
    for zone in spec.encounter_zones:
        for entry in zone.table:
            if entry.animal_id not in catalog.animals:
                raise MapValidationError(
                    source,
                    f"encounter_zones[{zone.id}]",
                    f"حيوان غير موجود في animals.json: {entry.animal_id}",
                )
    for index, event in enumerate(spec.events):
        for action in event.actions:
            if action.type == ACTION_GIVE_ANIMAL and action.animal_id not in catalog.animals:
                raise MapValidationError(
                    source,
                    f"events[{index}].actions",
                    f"حيوان غير موجود في animals.json: {action.animal_id}",
                )


# ---------- new game ----------

def load_new_game_file(path: Path) -> NewGameSpec:
    data, source = _read_json(path)
    return validate_new_game(data, source)


def validate_new_game(data: Any, source: str) -> NewGameSpec:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    if not _is_text(data.get("player_name")):
        raise MapValidationError(source, "player_name", "اسم اللاعب مطلوب")
    if not _is_text(data.get("map_id")):
        raise MapValidationError(source, "map_id", "معرّف الخريطة الابتدائية مطلوب")
    party = data.get("party")
    if not isinstance(party, list) or not all(_is_text(item) for item in party):
        raise MapValidationError(source, "party", "قائمة معرّفات حيوانات نصية")
    return NewGameSpec(data["player_name"], data["map_id"], tuple(party))


def check_party_refs(new_game: NewGameSpec, catalog: Catalog, source: str) -> None:
    for animal_id in new_game.party:
        if animal_id not in catalog.animals:
            raise MapValidationError(source, "party", f"حيوان غير موجود: {animal_id}")


def check_teleport_refs(spec: MapSpec, maps: dict[str, MapSpec], source: str) -> None:
    """الانتقال يجب أن يشير إلى خريطة موجودة، وإلى بلاطة صالحة وغير صلبة فيها."""
    for index, event in enumerate(spec.events):
        for action in event.actions:
            if action.type != ACTION_TELEPORT:
                continue
            target = maps.get(action.map_id or "")
            field = f"events[{index}].actions"
            if target is None:
                raise MapValidationError(source, field, f"خريطة غير موجودة: {action.map_id}")
            if action.x is None or action.y is None:
                raise MapValidationError(source, field, "إحداثيات الهدف ناقصة")
            if not (0 <= action.x < target.width and 0 <= action.y < target.height):
                raise MapValidationError(source, field, "الهدف خارج حدود الخريطة")
            if target.legend[target.rows[action.y][action.x]].solid:
                raise MapValidationError(source, field, "الهدف يقع على بلاطة صلبة")


# ---------- objectives and guide ----------

def load_objectives_file(path: Path) -> tuple[Objective, ...]:
    data, source = _read_json(path)
    return validate_objectives(data, source)


def validate_objectives(data: Any, source: str) -> tuple[Objective, ...]:
    if not isinstance(data, list):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر قائمة")
    seen: set[str] = set()
    objectives: list[Objective] = []
    for index, item in enumerate(data):
        field = f"[{index}]"
        if not isinstance(item, dict) or not _is_text(item.get("id")):
            raise MapValidationError(source, f"{field}.id", "معرّف الهدف مطلوب ونصّي")
        objective_id = item["id"]
        if objective_id in seen:
            raise MapValidationError(source, f"{field}.id", f"معرّف مكرر: {objective_id}")
        seen.add(objective_id)
        if not _is_text(item.get("text_ar")):
            raise MapValidationError(source, f"{field}.text_ar", "نص الهدف مطلوب")
        if not _is_text(item.get("map_id")):
            raise MapValidationError(source, f"{field}.map_id", "معرّف الخريطة مطلوب")
        target = item.get("target")
        if not isinstance(target, dict) or target.get("type") not in (TARGET_NPC, TARGET_ZONE):
            raise MapValidationError(source, f"{field}.target.type", "npc أو zone")
        if not _is_text(target.get("id")):
            raise MapValidationError(source, f"{field}.target.id", "المعرّف مطلوب")
        done = item.get("done")
        if not isinstance(done, dict) or done.get("type") not in (DONE_FLAG, DONE_DEFEATED):
            raise MapValidationError(source, f"{field}.done.type", "flag أو defeated")
        if not _is_text(done.get("id")):
            raise MapValidationError(source, f"{field}.done.id", "المعرّف مطلوب")
        objectives.append(
            Objective(
                id=objective_id,
                text_ar=item["text_ar"],
                map_id=item["map_id"],
                target_type=target["type"],
                target_id=target["id"],
                done_type=done["type"],
                done_id=done["id"],
            )
        )
    return tuple(objectives)


def check_objectives(
    objectives: tuple[Objective, ...],
    maps: dict[str, MapSpec],
    catalog: Catalog,
    source: str,
) -> None:
    for objective in objectives:
        field = f"objective[{objective.id}]"
        spec = maps.get(objective.map_id)
        if spec is None:
            raise MapValidationError(source, field, f"خريطة غير موجودة: {objective.map_id}")
        if objective.target_type == TARGET_NPC:
            known = {npc.id for npc in spec.npcs}
        else:
            known = {zone.id for zone in spec.encounter_zones}
        if objective.target_id not in known:
            raise MapValidationError(source, field, f"الهدف غير موجود: {objective.target_id}")
        if objective.done_type == DONE_DEFEATED and objective.done_id not in catalog.animals:
            raise MapValidationError(source, field, f"حيوان غير موجود: {objective.done_id}")


def build_guide(maps: dict[str, MapSpec], objectives: tuple[Objective, ...]) -> GuideData:
    """يبني نقاط الأهداف والبوابات من الخرائط نفسها، فلا تُكرَّر الإحداثيات يدوياً."""
    from src.core.event_system import ACTION_TELEPORT, ON_STEP

    points: dict[str, dict[str, tuple[float, float, float]]] = {}
    gates: dict[str, dict[str, tuple[float, float, float]]] = {}
    for map_id, spec in maps.items():
        local: dict[str, tuple[float, float, float]] = {}
        for npc in spec.npcs:
            local[npc.id] = (float(npc.x), float(npc.y), 1.5)
        for zone in spec.encounter_zones:
            local[zone.id] = (
                zone.x + (zone.width - 1) / 2,
                zone.y + (zone.height - 1) / 2,
                max(zone.width, zone.height) / 2,
            )
        points[map_id] = local
        local_gates: dict[str, tuple[float, float, float]] = {}
        for event in spec.events:
            trigger = event.trigger
            if trigger.type != ON_STEP or trigger.x is None or trigger.y is None:
                continue
            for action in event.actions:
                if action.type == ACTION_TELEPORT and action.map_id is not None:
                    local_gates.setdefault(
                        action.map_id, (float(trigger.x), float(trigger.y), 0.5)
                    )
        gates[map_id] = local_gates
    return GuideData(objectives=objectives, points=points, gates=gates)


# ---------- items ----------

def load_items_file(path: Path) -> dict[str, Item]:
    data, source = _read_json(path)
    return validate_items(data, source)


def validate_items(data: Any, source: str) -> dict[str, Item]:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    items: dict[str, Item] = {}
    for item_id, body in data.items():
        if not isinstance(body, dict):
            raise MapValidationError(source, item_id, "يجب أن يكون كائناً")
        if not _is_text(body.get("name_ar")):
            raise MapValidationError(source, f"{item_id}.name_ar", "الاسم العربي مطلوب")
        price = body.get("price")
        if not _is_int(price) or price <= 0:
            raise MapValidationError(source, f"{item_id}.price", "سعر موجب صحيح مطلوب")
        items[item_id] = Item(item_id, body["name_ar"], price)
    return items
