"""معادلة الضرر: الدقة والضربة الحرجة والتفاوت العشوائي. بلا pygame.

ترتيب استهلاك الأرقام العشوائية ثابت دائماً (دقة، ثم حرجة، ثم تفاوت)،
فتبقى الاختبارات حتمية حتى عند الإخفاق.

الضرر = قوة_الحركة × هجوم_المهاجم ÷ دفاع_المدافع × 0.5 × التفاوت × (1.5 إن حرجة)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.logic.models import AnimalInstance, Move

DAMAGE_SCALE = 0.5
CRITICAL_CHANCE = 1 / 16
CRITICAL_MULTIPLIER = 1.5
VARIANCE_MIN = 0.85
VARIANCE_MAX = 1.0


@dataclass(frozen=True)
class AttackResult:
    hit: bool
    critical: bool
    damage: int


def compute_attack(
    attacker: AnimalInstance,
    defender: AnimalInstance,
    move: Move,
    rng: random.Random,
) -> AttackResult:
    hit_roll = rng.random()
    crit_roll = rng.random()
    variance_roll = rng.random()
    if hit_roll >= move.accuracy / 100:
        return AttackResult(hit=False, critical=False, damage=0)
    critical = crit_roll < CRITICAL_CHANCE
    variance = VARIANCE_MIN + variance_roll * (VARIANCE_MAX - VARIANCE_MIN)
    base = move.power * attacker.template.attack / max(1, defender.template.defense)
    multiplier = CRITICAL_MULTIPLIER if critical else 1.0
    damage = max(1, round(base * DAMAGE_SCALE * variance * multiplier))
    return AttackResult(hit=True, critical=critical, damage=damage)
