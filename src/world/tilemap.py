"""شبكة البلاطات: الأبعاد والعوائق، بلا pygame."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TileType:
    name: str
    solid: bool
    color: tuple[int, int, int]


class TileMap:
    def __init__(
        self,
        width: int,
        height: int,
        rows: list[str],
        legend: dict[str, TileType],
    ) -> None:
        if len(rows) != height or any(len(row) != width for row in rows):
            raise ValueError("أبعاد الشبكة لا تطابق width و height")
        self.width = width
        self.height = height
        self._rows = rows
        self._legend = legend

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x: int, y: int) -> TileType:
        if not self.in_bounds(x, y):
            raise IndexError(f"({x}, {y}) خارج الخريطة")
        return self._legend[self._rows[y][x]]

    def is_solid(self, x: int, y: int) -> bool:
        """خارج الحدود يُعامل كعائق دائماً."""
        if not self.in_bounds(x, y):
            return True
        return self.tile_at(x, y).solid
