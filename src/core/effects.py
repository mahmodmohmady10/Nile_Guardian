"""مؤثرات بصرية المعركة: أرقام طائرة، ومضة، اهتزاز، شفاء (بلا pygame، مؤقتاتها تُحدَّث بالزمن)."""

from __future__ import annotations

from dataclasses import dataclass, field

FLOAT_LIFE = 0.9
FLASH_LIFE = 0.2
SHAKE_LIFE = 0.3
FLOAT_RISE = 70.0
COLUMNS = 3
COLUMN_GAP = 64

SIDE_ENEMY = "enemy"
SIDE_PLAYER = "player"


@dataclass
class FloatingText:
    text: str
    side: str
    color: tuple[int, int, int]
    column: int = 0
    elapsed: float = 0.0

    @property
    def done(self) -> bool:
        return self.elapsed >= FLOAT_LIFE

    @property
    def progress(self) -> float:
        return min(1.0, self.elapsed / FLOAT_LIFE)


@dataclass
class EffectsState:
    texts: list[FloatingText] = field(default_factory=list)
    flash: dict[str, float] = field(default_factory=dict)
    shake_left: float = 0.0
    shake_elapsed: float = 0.0

    def _next_column(self, side: str) -> int:
        active = sum(1 for text in self.texts if text.side == side)
        return active % COLUMNS

    def add_damage(self, side: str, amount: int, critical: bool = False) -> None:
        color = (255, 220, 80) if critical else (255, 110, 110)
        label = f"-{amount / 10:g}"
        text = ("!" + label) if critical else label
        self.texts.append(FloatingText(text, side, color, self._next_column(side)))
        self.flash[side] = FLASH_LIFE

    def add_heal(self, side: str, amount: int) -> None:
        self.texts.append(
            FloatingText(f"+{amount / 10:g}", side, (120, 230, 140), self._next_column(side))
        )

    def add_shake(self) -> None:
        self.shake_left = SHAKE_LIFE

    def update(self, dt: float) -> None:
        for text in self.texts:
            text.elapsed += dt
        self.texts = [text for text in self.texts if not text.done]
        for side in list(self.flash):
            self.flash[side] -= dt
            if self.flash[side] <= 0:
                del self.flash[side]
        if self.shake_left > 0:
            self.shake_left = max(0.0, self.shake_left - dt)
            self.shake_elapsed += dt

    def is_flashing(self, side: str) -> bool:
        return side in self.flash

    def shake_offset(self) -> tuple[int, int]:
        if self.shake_left <= 0:
            return (0, 0)
        direction = 1 if int(self.shake_elapsed * 40) % 2 == 0 else -1
        return (6 * direction, 0)
