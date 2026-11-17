"""تقطيع صورة الحيوانات (شبكة 3×2) إلى صور فردية بخلفية شفافة.

الترتيب داخل الشبكة (من اليسار إلى اليمين، ثم من الأعلى إلى الأسفل):
الصف الأول: صقر الجديان، غزال الريم، تمساح النيل
الصف الثاني: الذئب، النمر، أسد الدندر

الاستخدام من جذر المشروع:
    python tools/slice_sheet.py path\\to\\sheet.png
الناتج: data/images/animals/<id>.png
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

ORDER = ["saqr_jedi", "ghazal_reem", "timsah_nile", "wolf", "leopard", "asad_dinder"]
COLS, ROWS = 3, 2
OUTPUT_SIDE = 128
TOLERANCE = 40
ROOT = Path(__file__).resolve().parents[1]


def is_background(color: pygame.Color, background: pygame.Color) -> bool:
    return (
        abs(color.r - background.r) <= TOLERANCE
        and abs(color.g - background.g) <= TOLERANCE
        and abs(color.b - background.b) <= TOLERANCE
    )


def cut_out(cell: pygame.Surface) -> pygame.Surface:
    """يجعل الخلفية (لون الزاوية العليا) شفافة، ويقص الصورة إلى حدود الحيوان."""
    width, height = cell.get_size()
    background = cell.get_at((0, 0))
    left, top, right, bottom = width, height, -1, -1
    for y in range(height):
        for x in range(width):
            if not is_background(cell.get_at((x, y)), background):
                left, right = min(left, x), max(right, x)
                top, bottom = min(top, y), max(bottom, y)
    if right < 0:
        raise ValueError("لم يُعثر على حيوان في الخانة")
    crop = pygame.Surface((right - left + 1, bottom - top + 1), pygame.SRCALPHA)
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            color = cell.get_at((x, y))
            if is_background(color, background):
                crop.set_at((x - left, y - top), (0, 0, 0, 0))
            else:
                crop.set_at((x - left, y - top), (color.r, color.g, color.b, 255))
    return crop


def fit(surface: pygame.Surface, side: int) -> pygame.Surface:
    width, height = surface.get_size()
    scale = side / max(width, height)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    canvas = pygame.Surface((side, side), pygame.SRCALPHA)
    scaled = pygame.transform.smoothscale(surface, size)
    canvas.blit(scaled, ((side - size[0]) // 2, side - size[1]))
    return canvas


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("الاستخدام: python tools/slice_sheet.py sheet.png")
        return 1
    pygame.init()
    sheet = pygame.image.load(argv[1])
    cell_w, cell_h = sheet.get_width() // COLS, sheet.get_height() // ROWS
    output = ROOT / "data" / "images" / "animals"
    output.mkdir(parents=True, exist_ok=True)
    for index, animal_id in enumerate(ORDER):
        column, row = index % COLS, index // COLS
        cell = sheet.subsurface(pygame.Rect(column * cell_w, row * cell_h, cell_w, cell_h)).copy()
        image = fit(cut_out(cell), OUTPUT_SIDE)
        pygame.image.save(image, str(output / f"{animal_id}.png"))
        print("حُفظ:", animal_id)
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
