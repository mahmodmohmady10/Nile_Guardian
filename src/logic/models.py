"""نماذج المعارك: الحركات والحيوانات (قوالب ونسخ بالحيوية). بلا pygame."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    id: str
    name_ar: str
    power: int
    accuracy: int  # من 1 إلى 100


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


@dataclass
class AnimalInstance:
    template: AnimalTemplate
    current_hp: int

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
