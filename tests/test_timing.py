"""اختبارات الخطوة الثابتة: عدد الخطوات والتقطيع وحد التخلف."""

from __future__ import annotations

import pytest
from src.core.timing import FixedStepClock

STEP = 1.0 / 60.0


def make_clock() -> FixedStepClock:
    return FixedStepClock(step=STEP, max_frame=0.25, max_steps=5)


def test_one_frame_at_60fps_yields_one_step() -> None:
    assert make_clock().advance(STEP) == 1


def test_zero_frame_yields_no_steps() -> None:
    assert make_clock().advance(0.0) == 0


def test_remainder_carries_to_next_frame() -> None:
    clock = make_clock()
    assert clock.advance(STEP * 0.6) == 0
    assert clock.advance(STEP * 0.6) == 1


def test_large_frame_is_clamped_then_capped() -> None:
    clock = make_clock()
    assert clock.advance(2.0) == 5  # ضُبط إلى 0.25 ثم قُصّ إلى 5 خطوات


def test_backlog_is_dropped_after_cap() -> None:
    clock = make_clock()
    clock.advance(2.0)
    assert clock.advance(0.0) == 0


def test_alpha_is_within_unit_interval() -> None:
    clock = make_clock()
    clock.advance(STEP * 1.5)
    assert 0.0 <= clock.alpha < 1.0


def test_negative_frame_raises() -> None:
    with pytest.raises(ValueError):
        make_clock().advance(-0.1)


@pytest.mark.parametrize("step", [0.0, -1.0])
def test_invalid_step_raises(step: float) -> None:
    with pytest.raises(ValueError):
        FixedStepClock(step=step, max_frame=0.25, max_steps=5)
