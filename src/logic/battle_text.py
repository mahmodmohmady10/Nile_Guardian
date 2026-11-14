"""تحويل أحداث المعركة إلى جمل عربية للسجل. بلا pygame."""

from __future__ import annotations

from src.logic.battle_engine import KIND_ATTACK, KIND_FAINT, KIND_FLEE, KIND_MISS, BattleEvent


def describe_event(event: BattleEvent) -> str:
    if event.kind == KIND_FLEE:
        return f"{event.actor_name} انسحب من المعركة."
    if event.kind == KIND_FAINT:
        return f"{event.target_name} تراجع عن المعركة."
    if event.kind == KIND_MISS:
        return f"{event.actor_name} استخدم {event.move_name} فأخطأ."
    if event.kind == KIND_ATTACK:
        prefix = "ضربة حرجة! " if event.critical else ""
        return (
            f"{prefix}{event.actor_name} استخدم {event.move_name} "
            f"فأصاب {event.target_name} بـ {event.damage} من الحيوية."
        )
    return ""
