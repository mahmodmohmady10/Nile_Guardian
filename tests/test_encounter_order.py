"""اختبارات ترتيب اللقاءات: الحيوان المشروط لا يظهر قبل هزيمة الحيوان المطلوب."""

from __future__ import annotations

import random

from src.world.encounters import EncounterEntry, EncounterZone, roll_encounter

ZONE = EncounterZone(
    id="savanna",
    x=0,
    y=0,
    width=5,
    height=5,
    rate_percent=100,
    table=(
        EncounterEntry("ghazal_reem", 3),
        EncounterEntry("wolf", 2),
        EncounterEntry("leopard", 1, requires="wolf"),
    ),
)


def rolls(defeated: frozenset[str], count: int = 400) -> set[str]:
    rng = random.Random(7)
    seen: set[str] = set()
    for _ in range(count):
        enemy = roll_encounter((ZONE,), 1, 1, rng, defeated)
        if enemy is not None:
            seen.add(enemy)
    return seen


def test_leopard_never_appears_before_wolf_is_defeated() -> None:
    assert "leopard" not in rolls(frozenset())


def test_leopard_appears_after_wolf_is_defeated() -> None:
    assert "leopard" in rolls(frozenset({"wolf"}))


def test_wolf_and_ghazal_are_available_from_the_start() -> None:
    seen = rolls(frozenset())
    assert {"ghazal_reem", "wolf"} <= seen


def test_no_encounter_when_every_entry_is_locked() -> None:
    locked = EncounterZone(
        id="x", x=0, y=0, width=5, height=5, rate_percent=100,
        table=(EncounterEntry("leopard", 1, requires="wolf"),),
    )
    assert roll_encounter((locked,), 1, 1, random.Random(1), frozenset()) is None
