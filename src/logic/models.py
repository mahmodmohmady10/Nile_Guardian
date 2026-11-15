"""نماذج المعارك: التأثيرات والحركات والحيوانات (قوالب ونسخ بالحيوية). بلا pygame."""

from __future__ import annotations

from dataclasses import dataclass, replace

MAX_PARTY_SIZE = 3

# الترقية الدائمة من مستشفى المدينة (مرة واحدة لكل حيوان)
UPGRADE_HP_PERCENT = 10
UPGRADE_DEFENSE_PERCENT = 10
UPGRADE_ATTACK_PERCENT = 1
UPGRADE_PRICE = 100  # تُدفع في مستشفى المدينة
UPGRADE_XP_REQUIRED = 10
LEVEL_THRESHOLDS = (10, 30, 60, 100, 150, 210)  # خبرة بداية المستوى 2 والمستوى 3 ...


@dataclass(frozen=True)
class Effect:
    kind: str = "none"  # none | extra_damage | heal_percent | priority_next_turn
    multiplier: float = 1.0
    percent: int = 0


@dataclass(frozen=True)
class Move:
    id: str
    name_ar: str
    effect: Effect


@dataclass(frozen=True)
class LastStand:
    threshold_percent: int
    bonus_percent: int


@dataclass(frozen=True)
class AnimalTemplate:
    id: str
    name_ar: str
    max_hp: int
    attack: int
    defense: int
    speed: int
    basic_move: str
    special_move: str
    crit_chance: float
    crit_multiplier: float
    variance_min: float
    variance_max: float
    flee_at_percent: int | None
    last_stand: LastStand | None
    catchable: bool = True
    reward_money: int = 0


@dataclass
class AnimalInstance:
    template: AnimalTemplate
    current_hp: int
    last_stand_used: bool = False
    priority_next: bool = False
    xp: int = 0
    upgraded: bool = False

    @classmethod
    def fresh(cls, template: AnimalTemplate) -> AnimalInstance:
        return cls(template, template.max_hp)

    @property
    def id(self) -> str:
        return self.template.id

    @property
    def name_ar(self) -> str:
        return self.template.name_ar

    @property
    def max_hp(self) -> int:
        return self.template.max_hp

    @property
    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    @property
    def level(self) -> int:
        return 1 + sum(1 for threshold in LEVEL_THRESHOLDS if self.xp >= threshold)

    @property
    def can_upgrade(self) -> bool:
        return not self.upgraded and self.xp >= UPGRADE_XP_REQUIRED

    def heal_full(self) -> None:
        self.current_hp = self.template.max_hp
        self.last_stand_used = False
        self.priority_next = False


@dataclass(frozen=True)
class Item:
    id: str
    name_ar: str
    price: int


def upgraded_template(template: AnimalTemplate) -> AnimalTemplate:
    """قالب الحيوان بعد الترقية: صحة ودفاع بنسبة 10%، وهجوم بنسبة 1%."""
    return replace(
        template,
        max_hp=round(template.max_hp * (100 + UPGRADE_HP_PERCENT) / 100),
        attack=template.attack * (100 + UPGRADE_ATTACK_PERCENT) / 100,
        defense=template.defense * (100 + UPGRADE_DEFENSE_PERCENT) / 100,
    )


def xp_reward(template: AnimalTemplate) -> int:
    """خبرة الفوز على الخصم: (الصحة + الهجوم) ÷ 10، مع تقريب للأسفل."""
    return (template.max_hp + template.attack) // 10
