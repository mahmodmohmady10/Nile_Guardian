"""حركة الأمين على الشبكة: بلاطة كاملة في كل مرة، بلا pygame.

القواعد (ADR-002):
- الضغط المطوّل يواصل الحركة بلاطة بلاطة، دون توقف بين البلاطات.
- تغيير الاتجاه يُطبَّق بعد اكتمال البلاطة الحالية، لا فوراً.
- المحاولة نحو عائق تُدير الوجه نحوه ولا تُحرّك اللاعب.
"""

from __future__ import annotations

from collections.abc import Callable

DIRECTIONS: dict[str, tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

_EPSILON = 1e-9


class PlayerController:
    def __init__(self, x: int, y: int, seconds_per_tile: float) -> None:
        if seconds_per_tile <= 0:
            raise ValueError("seconds_per_tile يجب أن يكون موجباً")
        self.x = x
        self.y = y
        self.facing = "down"
        self._seconds_per_tile = seconds_per_tile
        self._target: tuple[int, int] | None = None
        self._progress = 0.0
        self._held: str | None = None
        self._arrival: tuple[int, int] | None = None

    def pop_arrival(self) -> tuple[int, int] | None:
        """يُرجع البلاطة التي وصل إليها اللاعب مرة واحدة فقط."""
        arrival = self._arrival
        self._arrival = None
        return arrival

    @property
    def is_moving(self) -> bool:
        return self._target is not None

    def set_held(self, held: tuple[str, ...]) -> None:
        """يأخذ آخر اتجاه مضغوط، ويتجاهل الأفعال غير الاتجاهية."""
        direction: str | None = None
        for action in held:
            if action in DIRECTIONS:
                direction = action
        self._held = direction

    def update(self, dt: float, can_enter: Callable[[int, int], bool]) -> None:
        if self._target is None:
            if self._held is None or not self._try_start(can_enter):
                return
        self._progress += dt / self._seconds_per_tile
        if self._progress >= 1.0 - _EPSILON:
            self.x, self.y = self._target  # type: ignore[misc]
            self._arrival = (self.x, self.y)
            self._target = None
            self._progress = 0.0
            if self._held is not None:
                self._try_start(can_enter)

    def visual_position(self) -> tuple[float, float]:
        if self._target is None:
            return float(self.x), float(self.y)
        target_x, target_y = self._target
        t = self._progress
        return self.x + (target_x - self.x) * t, self.y + (target_y - self.y) * t

    def _try_start(self, can_enter: Callable[[int, int], bool]) -> bool:
        if self._held is None:
            return False
        dx, dy = DIRECTIONS[self._held]
        self.facing = self._held
        target = (self.x + dx, self.y + dy)
        if can_enter(*target):
            self._target = target
            return True
        return False
