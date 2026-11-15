"""تحويل أحداث المعركة إلى جمل عربية للسجل. الأرقام الداخلية ÷ 10 للعرض. بلا pygame."""

from __future__ import annotations

from src.logic.battle_engine import (
    KIND_ATTACK,
    KIND_AUTO_SWITCH,
    KIND_CAPTURE_FAILED,
    KIND_CAPTURED,
    KIND_COUNTER,
    KIND_ENEMY_FLED,
    KIND_FAINT,
    KIND_FLEE,
    KIND_HEAL,
    KIND_ITEM_DEFENSE,
    KIND_ITEM_HEAL,
    KIND_ITEM_POWER,
    KIND_LAST_STAND,
    KIND_NO_EFFECT,
    KIND_SWITCH,
    BattleEvent,
)


def _display(value: int) -> str:
    return f"{value / 10:g}"


def describe_event(event: BattleEvent) -> str:
    kind = event.kind
    if kind == KIND_FLEE:
        return f"{event.actor_name} انسحب من المعركة."
    if kind == KIND_ENEMY_FLED:
        return f"{event.actor_name} انسحب من المعركة، وفزت بها!"
    if kind == KIND_FAINT:
        return f"{event.target_name} تراجع عن المعركة."
    if kind == KIND_NO_EFFECT:
        return f"{event.actor_name} استخدم {event.move_name} فلم يؤثر في {event.target_name}."
    if kind == KIND_COUNTER:
        return (
            f"{event.actor_name} تضرر بـ {_display(event.amount)} من الحيوية "
            f"لأن هجومه أضعف من دفاع {event.target_name}."
        )
    if kind == KIND_HEAL:
        return (
            f"{event.actor_name} استعاد {_display(event.amount)} "
            f"من الحيوية بـ {event.move_name}."
        )
    if kind == KIND_LAST_STAND:
        return f"{event.actor_name} استجمع قوته واستعاد {_display(event.amount)} من الحيوية!"
    if kind == KIND_ITEM_HEAL:
        return f"{event.actor_name} استعاد {_display(event.amount)} من الحيوية بالشفاء."
    if kind == KIND_ITEM_POWER:
        return f"{event.actor_name} استعد لضربة قوية واحدة."
    if kind == KIND_ITEM_DEFENSE:
        return f"ارتفع دفاع {event.actor_name} حتى نهاية المعركة."
    if kind == KIND_SWITCH:
        return f"{event.actor_name} دخل المعركة بدلاً من الحيوان السابق."
    if kind == KIND_AUTO_SWITCH:
        return f"{event.actor_name} دخل المعركة بعد تراجع الحيوان السابق."
    if kind == KIND_CAPTURED:
        return f"اصطدت {event.target_name}! انضم إلى الفريق بصحة كاملة."
    if kind == KIND_CAPTURE_FAILED:
        return "فشلت محاولة الاصطياد."
    if kind == KIND_ATTACK:
        prefix = "ضربة حرجة! " if event.critical else ""
        return (
            f"{prefix}{event.actor_name} استخدم {event.move_name} "
            f"فأصاب {event.target_name} بـ {_display(event.amount)} من الحيوية."
        )
    return ""
