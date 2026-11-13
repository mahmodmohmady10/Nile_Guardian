"""تقسيم النص إلى مقاطع عربية ولاتينية، وتقطيع الأسطر حسب العرض (ADR-001). بلا pygame."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

AR = "ar"
LTR = "ltr"

ARABIC_RANGES = (
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
)


@dataclass(frozen=True)
class Run:
    kind: str
    text: str


def is_arabic(char: str) -> bool:
    code = ord(char)
    return any(low <= code <= high for low, high in ARABIC_RANGES)


def _strong_kind(char: str) -> str | None:
    if is_arabic(char):
        return AR
    if char.isalnum():
        return LTR
    return None  # محايد: مسافة أو فاصلة أو رمز ترقيم


def split_runs(text: str) -> list[Run]:
    """يقسم النص إلى مقاطع متتالية من نوع واحد.

    الحياديّات (المسافات والترقيم) تتبع المقطع السابق، وإن كانت في البداية
    تتبع المقطع التالي. هكذا تبقى «الحيوية: » عربية، و«80/100 — HP» لاتينية.
    """
    resolved: list[str | None] = []
    current: str | None = None
    for char in text:
        kind = _strong_kind(char)
        if kind is not None:
            current = kind
        resolved.append(current)
    first = next((kind for kind in resolved if kind is not None), LTR)
    resolved = [first if kind is None else kind for kind in resolved]

    runs: list[Run] = []
    for char, kind in zip(text, resolved, strict=True):
        if runs and runs[-1].kind == kind:
            runs[-1] = Run(kind, runs[-1].text + char)
        else:
            runs.append(Run(kind, char))
    return runs


def wrap_words(text: str, measure: Callable[[str], int], max_width: int) -> list[str]:
    """تقطيع حسب الكلمات. كلمة أطول من العرض تبقى وحدها في سطرها."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    line = words[0]
    for word in words[1:]:
        candidate = f"{line} {word}"
        if measure(candidate) <= max_width:
            line = candidate
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines
