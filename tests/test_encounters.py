"""اختبارات مناطق المواجهة البرية (بلا pygame)."""

from __future__ import annotations

from src.world.encounters import EncounterEntry, EncounterZone, roll_encounter

ENTRIES = (EncounterEntry("ghazal", 1), EncounterEntry("timsah", 3))
ZONE = EncounterZone("fields", 1, 1, 4, 2, 100, ENTRIES)


class ConstRng:
    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


def test_zone_contains_only_inside_cells() -> None:
    assert ZONE.contains(1, 1) and ZONE.contains(4, 2)
    assert not ZONE.contains(5, 1) and not ZONE.contains(1, 3)


def test_outside_zone_never_encounters() -> None:
    assert roll_encounter([ZONE], 0, 0, ConstRng(0.0)) is None  # type: ignore[arg-type]


def test_zero_rate_never_encounters() -> None:
    zero = EncounterZone("quiet", 0, 0, 2, 2, 0, ENTRIES)
    assert roll_encounter([zero], 0, 0, ConstRng(0.0)) is None  # type: ignore[arg-type]


def test_full_rate_always_encounters() -> None:
    assert roll_encounter([ZONE], 1, 1, ConstRng(0.99)) is not None  # type: ignore[arg-type]


def test_weighted_pick_selects_lighter_entry_for_low_roll() -> None:
    assert roll_encounter([ZONE], 1, 1, ConstRng(0.1)) == "ghazal"  # type: ignore[arg-type]


def test_weighted_pick_selects_heavier_entry_for_high_roll() -> None:
    assert roll_encounter([ZONE], 1, 1, ConstRng(0.9)) == "timsah"  # type: ignore[arg-type]
