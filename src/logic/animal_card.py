"""بطاقة تعريف الحيوان: المستوى والخبرة والإحصاءات والمهارات بحالة فتحها. بلا pygame."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from src.logic.models import LEVEL_THRESHOLDS, AnimalInstance


@dataclass(frozen=True)
class SkillRow:
    level: int
    name_ar: str
    unlocked: bool


@dataclass(frozen=True)
class AnimalCard:
    name_ar: str
    level: int
    xp: int
    next_level_xp: int | None
    current_hp: float
    max_hp: float
    attack: float
    defense: float
    speed: int
    upgraded: bool
    catchable: bool
    skills: tuple[SkillRow, ...]


def next_level_xp(level: int) -> int | None:
    if level > len(LEVEL_THRESHOLDS):
        return None
    return LEVEL_THRESHOLDS[level - 1]


def build_card(animal: AnimalInstance, move_names: Mapping[str, str]) -> AnimalCard:
    template = animal.template
    rows = [SkillRow(1, move_names.get(template.special_move, template.special_move), True)]
    for level, move_id in template.skills:
        rows.append(
            SkillRow(level, move_names.get(move_id, move_id), animal.level >= level)
        )
    return AnimalCard(
        name_ar=template.name_ar,
        level=animal.level,
        xp=animal.xp,
        next_level_xp=next_level_xp(animal.level),
        current_hp=max(0, animal.current_hp) / 10,
        max_hp=animal.max_hp / 10,
        attack=round(template.attack / 10, 2),
        defense=round(template.defense / 10, 2),
        speed=template.speed,
        upgraded=animal.upgraded,
        catchable=template.catchable,
        skills=tuple(rows),
    )
