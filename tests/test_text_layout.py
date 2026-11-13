"""اختبارات تقسيم النص العربي واللاتيني وتقطيع الأسطر (بلا pygame)."""

from __future__ import annotations

from src.core.text_layout import AR, LTR, Run, is_arabic, split_runs, wrap_words


def test_pure_arabic_is_one_run() -> None:
    assert split_runs("حارس النيل") == [Run(AR, "حارس النيل")]


def test_neutrals_stay_with_previous_run() -> None:
    assert split_runs("الحيوية: 80/100 — HP") == [
        Run(AR, "الحيوية: "),
        Run(LTR, "80/100 — HP"),
    ]


def test_digit_inside_arabic_splits_runs() -> None:
    assert split_runs("ابدأ 3 مرات") == [Run(AR, "ابدأ "), Run(LTR, "3 "), Run(AR, "مرات")]


def test_leading_neutral_takes_next_strong_kind() -> None:
    assert split_runs(": نص") == [Run(AR, ": نص")]


def test_empty_text_has_no_runs() -> None:
    assert split_runs("") == []


def test_all_neutral_text_is_ltr() -> None:
    assert split_runs("  ") == [Run(LTR, "  ")]


def test_arabic_detection_covers_presentation_forms() -> None:
    assert is_arabic("ﻻ")  # U+FEFB، شكل عرض مستخدم في الخط
    assert not is_arabic("A")


def test_wrap_breaks_between_words() -> None:
    assert wrap_words("a bb ccc", len, 5) == ["a bb", "ccc"]


def test_wrap_keeps_long_word_alone() -> None:
    assert wrap_words("abcdefgh x", len, 4) == ["abcdefgh", "x"]


def test_wrap_empty_text() -> None:
    assert wrap_words("   ", len, 10) == []
