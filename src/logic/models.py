"""نماذج المعارك: التأثيرات والحركات والحيوانات (قوالب ونسخ بالحيوية). بلا pygame."""

from __future__ import annotations

from dataclasses import dataclass

MAX_PARTY_SIZE = 3


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


@dataclass
class AnimalInstance:
    template: AnimalTemplate
    current_hp: int
    last_stand_used: bool = False
    priority_next: bool = False

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

    def heal_full(self) -> None:
        self.current_hp = self.template.max_hp
        self.last_stand_used = False
        self.priority_next = False
