"""اختبارات المهارات: تُفتح بالمستوى، وتُرفض المغلقة، وتُنفَّذ المفتوحة، وتطابق الجدول المعتمد."""

from __future__ import annotations

import random
from dataclasses import replace

import pytest
from src.logic.battle_engine import (
    ACTION_SKILL,
    KIND_ATTACK,
    BattleEngine,
)
from src.logic.models import AnimalInstance
from src.utils.data_loader import load_catalog
from src.utils.paths import resource_path

CATALOG = load_catalog(resource_path("data", "animals.json"), resource_path("data", "moves.json"))
SAQR = CATALOG.animals["saqr_jedi"]


class ConstRng:
    def __init__(self, value: float) -> None:
        self.value = value

    def random(self) -> float:
        return self.value


def saqr_at_xp(xp: int) -> AnimalInstance:
    animal = AnimalInstance.fresh(SAQR)
    animal.xp = xp
    return animal


@pytest.mark.parametrize(("xp", "count"), [(0, 1), (30, 2), (100, 3), (210, 4)])
def test_skills_unlock_with_level(xp: int, count: int) -> None:
    assert len(saqr_at_xp(xp).available_skill_moves()) == count


def test_locked_skill_is_refused() -> None:
    enemy = AnimalInstance.fresh(CATALOG.animals["ghazal_reem"])
    engine = BattleEngine([saqr_at_xp(0)], enemy, CATALOG.moves,
                          random.Random(1))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        engine.turn(ACTION_SKILL, "swoop")


def test_unlocked_skill_is_used() -> None:
    enemy = AnimalInstance.fresh(replace(CATALOG.animals["ghazal_reem"], attack=10, defense=1))
    engine = BattleEngine([saqr_at_xp(30)], enemy, CATALOG.moves,
                          ConstRng(0.5))  # type: ignore[arg-type]
    events = engine.turn(ACTION_SKILL, "hawk_strike")
    attacks = [event for event in events if event.kind == KIND_ATTACK]
    assert attacks and attacks[0].move_name == "هجمة الصقر"


def test_healing_skill_restores_hp() -> None:
    asad = CATALOG.animals["asad_dinder"]
    lion = AnimalInstance(asad, 100)
    lion.xp = 100
    enemy = AnimalInstance.fresh(replace(CATALOG.animals["ghazal_reem"], attack=10, defense=500))
    engine = BattleEngine([lion], enemy, CATALOG.moves,
                          ConstRng(0.5))  # type: ignore[arg-type]
    engine.turn(ACTION_SKILL, "double_roar")
    assert lion.current_hp == 140  # 100 + 20% من 200


def test_base_skill_is_always_available() -> None:
    assert saqr_at_xp(0).available_skill_moves()[0] == SAQR.special_move


def test_approved_skill_table_is_in_the_data() -> None:
    expected = {
        "saqr_jedi": [(3, "hawk_strike"), (5, "leap"), (7, "swoop")],
        "ghazal_reem": [(3, "quick_hop"), (5, "charge"), (7, "storm")],
        "timsah_nile": [(3, "heavy_bite"), (5, "relax"), (7, "jaw_strike")],
        "wolf": [(3, "howl"), (5, "fang_power"), (7, "chase")],
        "leopard": [(3, "snatch"), (5, "ambush_leap"), (7, "ambush")],
        "asad_dinder": [(3, "heavy_claw"), (5, "double_roar"), (7, "majesty")],
    }
    for animal_id, skills in expected.items():
        assert list(CATALOG.animals[animal_id].skills) == skills
        for _, move_id in skills:
            assert move_id in CATALOG.moves
