"""تحويل مفاتيح pygame إلى أفعال مجردة، بالرمز الفيزيائي (scancode).

الرمز الفيزيائي يبقى ثابتاً مع تبديل لغة لوحة المفاتيح، فتعمل WASD كذلك
على لوحة عربية.
"""

from __future__ import annotations

import pygame

ACTION_BY_SCANCODE: dict[int, str] = {
    pygame.KSCAN_UP: "up",
    pygame.KSCAN_W: "up",
    pygame.KSCAN_DOWN: "down",
    pygame.KSCAN_S: "down",
    pygame.KSCAN_LEFT: "left",
    pygame.KSCAN_A: "left",
    pygame.KSCAN_RIGHT: "right",
    pygame.KSCAN_D: "right",
    pygame.KSCAN_RETURN: "confirm",
    pygame.KSCAN_SPACE: "confirm",
    pygame.KSCAN_ESCAPE: "cancel",
}

DIRECTION_ACTIONS = frozenset({"up", "down", "left", "right"})


def action_for_event(event: pygame.event.Event) -> str | None:
    return ACTION_BY_SCANCODE.get(getattr(event, "scancode", -1))
