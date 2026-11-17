"""اختبارات بطاقة الحيوان: المهارات بحالة فتحها، والخبرة للمستوى التالي، وسبب تعذر الاصطياد."""

from __future__ import annotations

import random

from src.logic.animal_card import build_card, next_level_xp
from src.logic.battle_engine import BattleEngine
from src.logic.models import AnimalInstance
from src.utils.data_loader import load_catalog
from src.utils.paths import resource_path

CATALOG = load_catalog(resource_path("data", "animals.json"), resource_path("data", "moves.json"))
NAMES = {move_id: move.name_ar for move_id, move in CATALOG.moves.items()}


def falcon_at(xp: int) -> AnimalInstance:
    animal = AnimalInstance.fresh(CATALOG.animals["saqr_jedi"])
    animal.xp = xp
    return animal


def test_card_marks_skills_by_level() -> None:
    card = build_card(falcon_at(30), NAMES)  # المستوى 3
    unlocked = [(row.level, row.unlocked) for row in card.skills]
    assert unlocked == [(1, True), (3, True), (5, False), (7, False)]


def test_locked_skill_names_its_level() -> None:
    card = build_card(falcon_at(0), NAMES)
    assert card.skills[1].name_ar == "هجمة الصقر" and not card.skills[1].unlocked


def test_next_level_threshold() -> None:
    assert next_level_xp(1) == 10
    assert next_level_xp(3) == 60
    assert next_level_xp(7) is None


def test_card_at_max_level_has_no_next_threshold() -> None:
    assert build_card(falcon_at(210), NAMES).next_level_xp is None


def test_card_shows_real_values_in_display_units() -> None:
    card = build_card(falcon_at(0), NAMES)
    assert card.max_hp == 15 and card.attack == 5.2 and card.defense == 3


def test_card_reports_capture_ability() -> None:
    lion = AnimalInstance.fresh(CATALOG.animals["asad_dinder"])
    assert not build_card(lion, NAMES).catchable
    assert build_card(falcon_at(0), NAMES).catchable


class _Rng:
    def random(self) -> float:
        return 0.5


def test_capture_reason_explains_threshold() -> None:
    enemy = AnimalInstance.fresh(CATALOG.animals["ghazal_reem"])
    engine = BattleEngine([falcon_at(0)], enemy, CATALOG.moves,
                          random.Random(1))  # type: ignore[arg-type]
    assert "10%" in (engine.capture_block_reason() or "")


def test_capture_reason_explains_uncatchable() -> None:
    lion = AnimalInstance(CATALOG.animals["asad_dinder"], 10)
    engine = BattleEngine([falcon_at(0)], lion, CATALOG.moves,
                          random.Random(1))  # type: ignore[arg-type]
    assert "لا يمكن اصطياده" in (engine.capture_block_reason() or "")


def test_capture_has_no_reason_when_available() -> None:
    ghazal = AnimalInstance(CATALOG.animals["ghazal_reem"], 5)
    engine = BattleEngine([falcon_at(0)], ghazal, CATALOG.moves,
                          random.Random(1))  # type: ignore[arg-type]
    assert engine.capture_block_reason() is None
