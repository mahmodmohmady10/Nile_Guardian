"""تجهيز صور اللعبة من الملفات الأصلية في data/images/_source حسب manifest.json.

يزيل الخلفية البيضاء أو الخضراء (لون الزاوية) عندما يكون cut_out = true،
ثم يضبط الحجم ويحفظ PNG في المكان المحدد داخل data/images/.

الاستخدام من جذر المشروع:
    python tools/process_images.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slice_sheet import cut_out, fit  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "data" / "images"
SOURCE = IMAGES / "_source"


def center_square(image: pygame.Surface) -> pygame.Surface:
    width, height = image.get_size()
    side = min(width, height)
    left, top = (width - side) // 2, (height - side) // 2
    return image.subsurface(pygame.Rect(left, top, side, side)).copy()


def center_fraction(image: pygame.Surface, fraction: float) -> pygame.Surface:
    width, height = image.get_size()
    side = max(1, int(min(width, height) * fraction))
    left, top = (width - side) // 2, (height - side) // 2
    return image.subsurface(pygame.Rect(left, top, side, side)).copy()


def main() -> int:
    pygame.init()
    manifest = json.loads((IMAGES / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest:
        source = SOURCE / entry["source"]
        target = IMAGES / entry["output"]
        if not source.is_file():
            print("تعذّر العثور على:", source)
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        image = pygame.image.load(str(source))
        if entry.get("crop_square"):
            image = center_square(image)
        if entry.get("crop_fraction"):
            image = center_fraction(image, float(entry["crop_fraction"]))
        if entry.get("rotate"):
            image = pygame.transform.rotate(image, -int(entry["rotate"]))
        if entry["cut_out"]:
            image = cut_out(image)
        pygame.image.save(fit(image, entry["size"]), str(target))
        print("حُفظ:", target.relative_to(ROOT))
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
