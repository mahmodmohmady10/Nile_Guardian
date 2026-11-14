"""اختبارات التوازن المعتمد: قيم البطاقات، ونسب الفوز بالمحرك الفعلي."""

from __future__ import annotations

import random

from src.logic.battle_engine import (
    ACTION_ATTACK,
    ACTION_SPECIAL,
    OUTCOME_ENEMY_FLED,
    OUTCOME_WON,
    BattleEngine,
)
from src.logic.models import AnimalInstance
from src.utils.data_loader import load_catalog
from src.utils.paths import resource_path

SAMPLES = 400


def catalog():  # type: ignore[no-untyped-def]
    return load_catalog(resource_path("data", "animals.json"), resource_path("data", "moves.json"))


def win_rate(enemy_id: str) -> float:
    cat = catalog()
    wins = 0
    for seed in range(SAMPLES):
        player = AnimalInstance.fresh(cat.animals["saqr_jedi"])
        enemy = AnimalInstance.fresh(cat.animals[enemy_id])
        engine = BattleEngine(player, enemy, cat.moves, random.Random(seed))
        turn = 0
        while engine.outcome is None and turn < 300:
            engine.turn(ACTION_SPECIAL if turn % 3 == 2 else ACTION_ATTACK)
            turn += 1
        wins += engine.outcome in (OUTCOME_WON, OUTCOME_ENEMY_FLED)
    return wins / SAMPLES * 100


def test_approved_card_values() -> None:
    cat = catalog()
    saqr, ghazal = cat.animals["saqr_jedi"], cat.animals["ghazal_reem"]
    timsah, asad = cat.animals["timsah_nile"], cat.animals["asad_dinder"]
    assert (saqr.max_hp, saqr.attack, saqr.defense) == (150, 52, 30)
    assert (ghazal.max_hp, ghazal.attack, ghazal.defense) == (100, 20, 30)
    assert ghazal.flee_at_percent == 30
    assert (timsah.max_hp, timsah.attack, timsah.defense) == (200, 50, 25)
    assert (asad.max_hp, asad.attack, asad.defense) == (200, 45, 30)
    assert asad.last_stand is not None and asad.last_stand.threshold_percent == 5
    assert asad.last_stand.bonus_percent == 25


def test_ghazal_is_easy() -> None:
    assert win_rate("ghazal_reem") >= 85


def test_timsah_is_easy_after_attack_52() -> None:
    assert 85 <= win_rate("timsah_nile") <= 100


def test_asad_is_the_real_challenge() -> None:
    assert 60 <= win_rate("asad_dinder") <= 85


def test_wolf_is_medium_hard() -> None:
    assert 75 <= win_rate("wolf") <= 90


def test_leopard_is_hard() -> None:
    assert 70 <= win_rate("leopard") <= 85


def test_difficulty_ladder_is_monotonic() -> None:
    ladder = ["ghazal_reem", "timsah_nile", "wolf", "leopard", "asad_dinder"]
    rates = [win_rate(animal) for animal in ladder]
    assert all(rates[i] >= rates[i + 1] for i in range(len(rates) - 1)), rates
