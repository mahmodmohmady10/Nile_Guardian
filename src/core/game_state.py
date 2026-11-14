"""الحالة المشتركة للعبة: الموقع والرفاق وعلامات القصة. بلا pygame."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.logic.models import AnimalInstance, AnimalTemplate


@dataclass
class GameState:
    player_name: str
    map_id: str
    templates: dict[str, AnimalTemplate] = field(default_factory=dict)
    grid_x: int = 0
    grid_y: int = 0
    facing: str = "down"
    party: list[AnimalInstance] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)

    def has_flag(self, flag: str) -> bool:
        return flag in self.flags

    def set_flag(self, flag: str) -> None:
        self.flags.add(flag)

    def give_animal(self, animal_id: str) -> None:
        if any(animal.id == animal_id for animal in self.party):
            return
        self.party.append(AnimalInstance.fresh(self.templates[animal_id]))

    def lead(self) -> AnimalInstance | None:
        return self.party[0] if self.party else None

    def heal_party(self) -> None:
        for animal in self.party:
            animal.heal_full()
