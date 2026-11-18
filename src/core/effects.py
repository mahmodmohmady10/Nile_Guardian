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
    shakes: dict[str, list[float]] = field(default_factory=dict)

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

    def add_shake(self, side: str, strength: float) -> None:
        """يهز الجانب المصاب بقوة تتناسب مع حجم الضرر (بالبكسل)."""
        self.shakes[side] = [strength, SHAKE_LIFE, 0.0]

    def update(self, dt: float) -> None:
        for text in self.texts:
            text.elapsed += dt
        self.texts = [text for text in self.texts if not text.done]
        for side in list(self.flash):
            self.flash[side] -= dt
            if self.flash[side] <= 0:
                del self.flash[side]
        for side in list(self.shakes):
            entry = self.shakes[side]
            entry[1] -= dt
            entry[2] += dt
            if entry[1] <= 0:
                del self.shakes[side]

    def is_flashing(self, side: str) -> bool:
        return side in self.flash

    def shake_offset(self, side: str) -> tuple[int, int]:
        if side not in self.shakes:
            return (0, 0)
        strength, _left, elapsed = self.shakes[side]
        direction = 1 if int(elapsed * 40) % 2 == 0 else -1
        return (round(strength * direction), 0)
