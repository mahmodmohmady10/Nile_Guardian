"""تحميل الصور بالبكسل وتحقق من صحتها (بلا pygame). كل صورة شبكة نصية 12×12 وألوانها في palette."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.utils.data_loader import MapValidationError, _read_json

SPRITE_SIZE = 16


@dataclass(frozen=True)
class SpriteSpec:
    palette: dict[str, tuple[int, int, int]]
    rows: tuple[str, ...]


def load_sprites_file(path: Path) -> dict[str, SpriteSpec]:
    data, source = _read_json(path)
    return validate_sprites(data, source)


def validate_sprites(data: Any, source: str) -> dict[str, SpriteSpec]:
    if not isinstance(data, dict):
        raise MapValidationError(source, "<root>", "يجب أن يكون الجذر كائناً")
    sprites: dict[str, SpriteSpec] = {}
    for sprite_id, body in data.items():
        if not isinstance(body, dict):
            raise MapValidationError(source, sprite_id, "يجب أن يكون كائناً")
        palette_raw = body.get("palette")
        if not isinstance(palette_raw, dict) or not palette_raw:
            raise MapValidationError(source, f"{sprite_id}.palette", "لوحة ألوان مطلوبة")
        palette: dict[str, tuple[int, int, int]] = {}
        for symbol, rgb in palette_raw.items():
            if len(symbol) != 1 or symbol == ".":
                raise MapValidationError(source, f"{sprite_id}.palette", f"رمز غير صالح: {symbol}")
            if not isinstance(rgb, list) or len(rgb) != 3 or not all(
                isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255 for c in rgb
            ):
                raise MapValidationError(source, f"{sprite_id}.palette.{symbol}", "[R, G, B]")
            palette[symbol] = (rgb[0], rgb[1], rgb[2])
        rows = body.get("rows")
        if not isinstance(rows, list) or len(rows) != SPRITE_SIZE:
            raise MapValidationError(source, f"{sprite_id}.rows", f"{SPRITE_SIZE} صفاً بالضبط")
        for index, row in enumerate(rows):
            if not isinstance(row, str) or len(row) != SPRITE_SIZE:
                raise MapValidationError(
                    source, f"{sprite_id}.rows[{index}]", f"{SPRITE_SIZE} حرفاً"
                )
            for char in row:
                if char != "." and char not in palette:
                    raise MapValidationError(source, f"{sprite_id}.rows[{index}]",
                                             f"الرمز '{char}' غير معرّف في اللوحة")
        sprites[sprite_id] = SpriteSpec(palette, tuple(rows))
    return sprites


def check_sprites_cover(animal_ids: set[str], sprites: dict[str, SpriteSpec], source: str) -> None:
    for animal_id in sorted(animal_ids):
        if animal_id not in sprites:
            raise MapValidationError(source, animal_id, "لا توجد صورة لهذا الحيوان")


Pixel = tuple[int, int, int] | None


def shaded_pixels(spec: SpriteSpec) -> list[list[Pixel]]:
    """ألوان البكسلات بعد التظليل الآلي: الحافة العليا أفتح، والسفلية أغمق، لتظهر التفاصيل."""
    size = SPRITE_SIZE
    base: list[list[Pixel]] = []
    for row in spec.rows:
        base.append([None if char == "." else spec.palette[char] for char in row])

    def filled(x: int, y: int) -> bool:
        return 0 <= x < size and 0 <= y < size and base[y][x] is not None

    result: list[list[Pixel]] = [[None] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            color = base[y][x]
            if color is None:
                continue
            red, green, blue = color
            if not filled(x, y - 1):
                red, green, blue = (min(255, red + 40), min(255, green + 40), min(255, blue + 40))
            elif not filled(x, y + 1):
                red, green, blue = (max(0, red - 35), max(0, green - 35), max(0, blue - 35))
            result[y][x] = (red, green, blue)
    return result
