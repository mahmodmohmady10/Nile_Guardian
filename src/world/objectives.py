"""الأهداف الإرشادية وسهم التوجيه: الهدف التالي وموضعه والاتجاه (بلا pygame).

الهدف يُعرَّف بالمحفز (الشخصية أو المنطقة) وبشرط الإنجاز (علامة أو حيوان مهزوم).
نقطة الهدف = (x، y، نصف القطر). الوصول يعني أن اللاعب داخل نصف القطر.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

TARGET_NPC = "npc"
TARGET_ZONE = "zone"
DONE_FLAG = "flag"
DONE_DEFEATED = "defeated"

Point = tuple[float, float, float]


@dataclass(frozen=True)
class Objective:
    id: str
    text_ar: str
    map_id: str
    target_type: str
    target_id: str
    done_type: str
    done_id: str


@dataclass(frozen=True)
class GuideData:
    objectives: tuple[Objective, ...]
    points: Mapping[str, Mapping[str, Point]]
    gates: Mapping[str, Mapping[str, Point]]


def is_done(objective: Objective, flags: set[str], defeated: set[str]) -> bool:
    if objective.done_type == DONE_FLAG:
        return objective.done_id in flags
    return objective.done_id in defeated


def next_objective(
    objectives: Iterable[Objective], flags: set[str], defeated: set[str]
) -> Objective | None:
    for objective in objectives:
        if not is_done(objective, flags, defeated):
            return objective
    return None


def resolve_point(
    objective: Objective,
    current_map: str,
    points: Mapping[str, Mapping[str, Point]],
    gates: Mapping[str, Mapping[str, Point]],
) -> Point | None:
    """في الخريطة نفسها: نقطة الهدف. في خريطة أخرى: بوابة الانتقال نحوها."""
    if objective.map_id == current_map:
        return points.get(current_map, {}).get(objective.target_id)
    return gates.get(current_map, {}).get(objective.map_id)


def direction(
    origin: tuple[float, float], target: tuple[float, float]
) -> tuple[float, float] | None:
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return None
    return dx / length, dy / length


def has_reached(point: Point, position: tuple[float, float]) -> bool:
    return math.hypot(point[0] - position[0], point[1] - position[1]) <= point[2]
