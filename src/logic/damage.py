"""معادلة الضرر (توازن 0.7). بلا pygame.

- إن كان الهجوم أكبر من الدفاع: الضرر = (الهجوم − الدفاع) × مضاعف المهارة × الحرجة × التفاوت.
- إن كان الهجوم أقل من الدفاع: المهاجم يتضرر بالفرق (ضرر مرتد)، والمدافع لا يتضرر.
- الحرجة وقيمتها والتفاوت خاصة بكل حيوان.
ترتيب الأرقام العشوائية ثابت (حرجة ثم تفاوت) عند الضرر الموجب، فتبقى الاختبارات حتمية.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from src.logic.models import AnimalInstance


@dataclass(frozen=True)
class AttackResult:
    damage: int
    self_damage: int
    critical: bool


def compute_attack(
    attacker: AnimalInstance,
    defender: AnimalInstance,
    multiplier: float,
    rng: random.Random,
) -> AttackResult:
    difference = attacker.template.attack - defender.template.defense
    if difference < 0:
        return AttackResult(damage=0, self_damage=-difference, critical=False)
    if difference == 0:
        return AttackResult(damage=0, self_damage=0, critical=False)
    template = attacker.template
    crit_roll = rng.random()
    variance_roll = rng.random()
    critical = crit_roll < template.crit_chance
    spread = template.variance_max - template.variance_min
    variance = template.variance_min + variance_roll * spread
    critical_multiplier = template.crit_multiplier if critical else 1.0
    damage = max(1, round(difference * multiplier * critical_multiplier * variance))
    return AttackResult(damage=damage, self_damage=0, critical=critical)
