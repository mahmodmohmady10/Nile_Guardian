"""ترقية الحيوان في مستشفى المدينة: دائمة، مرة واحدة، عند 10 خبرة (بلا pygame)."""

from __future__ import annotations

from src.core.game_state import GameState
from src.logic.models import UPGRADE_PRICE, UPGRADE_XP_REQUIRED, AnimalInstance, upgraded_template


def try_upgrade(state: GameState, animal: AnimalInstance) -> str:
    """يُرجع رسالة النتيجة للعرض. ينجح فقط إن استوفى الشروط وتوفر المال."""
    if animal.upgraded:
        return f"تمت ترقية {animal.name_ar} من قبل."
    if animal.xp < UPGRADE_XP_REQUIRED:
        return f"{animal.name_ar} يحتاج {UPGRADE_XP_REQUIRED - animal.xp} نقطة خبرة للترقية."
    if not state.spend(UPGRADE_PRICE):
        return "النقود غير كافية للترقية."
    animal.template = upgraded_template(animal.template)
    animal.upgraded = True
    return f"تمت ترقية {animal.name_ar}: صحته وهجومه ودفاعه زادت."
