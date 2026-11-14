"""مناطق المواجهات البرية: احتمال الظهور وجدول الحيوانات بالأوزان. بلا pygame."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class EncounterEntry:
    animal_id: str
    weight: int


@dataclass(frozen=True)
class EncounterZone:
    id: str
    x: int
    y: int
    width: int
    height: int
    rate_percent: int
    table: tuple[EncounterEntry, ...]

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


def roll_encounter(
    zones: Sequence[EncounterZone], x: int, y: int, rng: random.Random
) -> str | None:
    """يُرجع معرّف الحيوان البري إن ظهر، وإلا None. يستهلك الرقم العشوائي داخل المنطقة فقط."""
    zone = next((z for z in zones if z.contains(x, y)), None)
    if zone is None:
        return None
    if rng.random() * 100 >= zone.rate_percent:
        return None
    total = sum(entry.weight for entry in zone.table)
    pick = rng.random() * total
    cumulative = 0
    for entry in zone.table:
        cumulative += entry.weight
        if pick < cumulative:
            return entry.animal_id
    return zone.table[-1].animal_id
