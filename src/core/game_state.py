"""الحالة المشتركة للعبة: الموقع والرفاق وعلامات القصة. بلا pygame."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.logic.models import MAX_PARTY_SIZE, AnimalInstance, AnimalTemplate


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
    defeated: set[str] = field(default_factory=set)
    money: int = 0
    bag: dict[str, int] = field(default_factory=dict)

    def has_flag(self, flag: str) -> bool:
        return flag in self.flags

    def set_flag(self, flag: str) -> None:
        self.flags.add(flag)

    def mark_defeated(self, animal_id: str) -> None:
        self.defeated.add(animal_id)

    def give_animal(self, animal_id: str) -> None:
        if any(animal.id == animal_id for animal in self.party):
            return
        if len(self.party) >= MAX_PARTY_SIZE:
            raise ValueError("الفريق ممتلئ")
        self.party.append(AnimalInstance.fresh(self.templates[animal_id]))

    def lead(self) -> AnimalInstance | None:
        return self.party[0] if self.party else None

    def set_lead(self, index: int) -> None:
        """ينقل الحيوان المختار إلى المقدمة، فيكون هو الذي يقاتل أولاً."""
        if not 0 <= index < len(self.party):
            raise ValueError("اختيار غير صالح")
        self.party.insert(0, self.party.pop(index))

    def heal_party(self) -> None:
        for animal in self.party:
            animal.heal_full()

    def add_money(self, amount: int) -> None:
        self.money += amount

    def spend(self, amount: int) -> bool:
        if self.money < amount:
            return False
        self.money -= amount
        return True

    def add_item(self, item_id: str) -> None:
        self.bag[item_id] = self.bag.get(item_id, 0) + 1

    def award_xp(self, amount: int) -> None:
        for animal in self.party:
            animal.xp += amount
