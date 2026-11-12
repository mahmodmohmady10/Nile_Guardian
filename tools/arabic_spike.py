"""Spike M0: compare two ways to render Arabic text in pygame-ce.

Method A: arabic-reshaper + python-bidi, then a normal font.render.
Method B: pygame-ce built-in text shaping (Font.set_direction / set_script),
          which needs an SDL_ttf build with HarfBuzz support.

Output: PNG files, a side-by-side comparison sheet, and timing numbers.
The visual check (joined letters, right-to-left order, diacritics placement)
must be done by a human opening spike_output/comparison.png.

Usage (from the project root):
    python tools/arabic_spike.py --font assets/fonts/Tajawal-Regular.ttf
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WHITE = (255, 255, 255)
BG = (24, 32, 44)
LABEL = (150, 200, 255)

SAMPLES = {
    "plain": "حارس النيل: رحلة الأمين",
    "diacritics": "مَرْحَباً بِكَ يَا أَمِينُ",
    "mixed": "الحيوية: 80/100 — HP",
    "long": "ابدأ رحلتك على ضفاف النيل وكن حارساً للحياة البرية في السودان",
}

SYSTEM_FONTS = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def find_font(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    fonts_dir = ROOT / "assets" / "fonts"
    for pattern in ("*.ttf", "*.otf"):
        found = sorted(fonts_dir.glob(pattern))
        if found:
            return found[0]
    for candidate in SYSTEM_FONTS:
        if Path(candidate).is_file():
            return Path(candidate)
    return None


def load_shaping():
    """Returns (reshape, get_display) or None if the libraries are missing."""
    try:
        import arabic_reshaper
    except ImportError:
        return None
    try:
        from bidi import get_display
    except ImportError:
        try:
            from bidi.algorithm import get_display
        except ImportError:
            return None
    # delete_harakat=False keeps diacritics (the default config removes them).
    reshaper = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})
    return reshaper.reshape, get_display


def make_builtin_font(path: Path, size: int):
    font = pygame.font.Font(str(path), size)
    try:
        font.set_direction(pygame.DIRECTION_RTL)
        font.set_script("Arab")
    except (AttributeError, pygame.error) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return font, None


def bench(fn, iterations: int) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    return (time.perf_counter() - start) * 1000 / iterations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--font", help="path to an Arabic-capable .ttf/.otf font")
    parser.add_argument("--size", type=int, default=28)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--out", default=str(ROOT / "spike_output"))
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    pygame.font.init()
    print(f"pygame-ce {pygame.version.ver} | SDL_ttf {pygame.font.get_sdl_ttf_version()}")

    font_path = find_font(args.font)
    if font_path is None:
        print("ERROR: no usable font. Put an Arabic .ttf in assets/fonts/ or pass --font.")
        return 2
    print(f"font: {font_path}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    shaping = load_shaping()
    font_a = pygame.font.Font(str(font_path), args.size)
    font_b, b_error = make_builtin_font(font_path, args.size)
    print(f"method A (reshaper+bidi): {'available' if shaping else 'MISSING libraries'}")
    print(f"method B (built-in)     : {'available' if font_b else 'unavailable - ' + str(b_error)}")
    if not shaping and font_b is None:
        print("ERROR: neither method is available.")
        return 1

    rows = []  # (sample_name, method_label, surface)
    print(f"\n{'sample':<12}{'method':<8}{'width_px':>9}{'ms/render':>11}")
    for name, text in SAMPLES.items():
        if shaping:
            reshape, get_display = shaping

            def render_a(text=text, reshape=reshape, get_display=get_display):
                return font_a.render(get_display(reshape(text)), True, WHITE)

            surf = render_a()
            pygame.image.save(surf, str(out_dir / f"A_{name}.png"))
            rows.append((name, "A", surf))
            ms = bench(render_a, args.iterations)
            print(f"{name:<12}{'A':<8}{surf.get_width():>9}{ms:>11.3f}")
        if font_b is not None:

            def render_b(text=text):
                return font_b.render(text, True, WHITE)

            surf = render_b()
            pygame.image.save(surf, str(out_dir / f"B_{name}.png"))
            rows.append((name, "B", surf))
            ms = bench(render_b, args.iterations)
            print(f"{name:<12}{'B':<8}{surf.get_width():>9}{ms:>11.3f}")

    label_font = pygame.font.Font(None, 20)
    line_h = args.size + 16
    width = max(s.get_width() for _, _, s in rows) + 180
    sheet = pygame.Surface((width, line_h * len(rows) + 20))
    sheet.fill(BG)
    for i, (name, method, surf) in enumerate(rows):
        y = 10 + i * line_h
        sheet.blit(label_font.render(f"{method}: {name}", True, LABEL), (10, y + 8))
        sheet.blit(surf, (width - 20 - surf.get_width(), y))
    sheet_path = out_dir / "comparison.png"
    pygame.image.save(sheet, str(sheet_path))

    print(f"\nSaved: {sheet_path}")
    print("Now inspect it by eye: letters joined, right-to-left order, diacritics placed,")
    print("'80/100' and 'HP' in the mixed line positioned correctly.")
    print("Timing is a single-machine number; record it, do not generalize it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
