"""ثوابت اللعبة: الدقة وحجم البلاطة وسرعة الإطارات والألوان."""

WIDTH = 960
HEIGHT = 576  # 18 بلاطة × 32 بكسل
TILE_SIZE = 32
FPS = 60
STEP = 1.0 / 60.0  # خطوة المنطق الثابتة بالثواني
MAX_FRAME_TIME = 0.25  # أقصى زمن إطار يُحتسب، لمنع «الموت الطيفي» بعد توقف طويل
MAX_STEPS_PER_FRAME = 5  # أقصى عدد خطوات منطق في الإطار الواحد
MOVE_SECONDS_PER_TILE = 0.15  # زمن عبور البلاطة الواحدة (9 خطوات منطق)

TITLE = "حارس النيل: رحلة الأمين"

FONT_FILE = "Tajawal-Regular.ttf"  # خط عربي مفتوح الترخيص يُوضع في assets/fonts/
TEXT_CACHE_SIZE = 256
DIALOGUE_BOX = (40, 376, 880, 176)  # x, y, width, height
DIALOGUE_TEXT_SIZE = 28
DIALOGUE_SPEAKER_SIZE = 30
BOX_COLOR = (14, 20, 30)

BG_COLOR = (24, 32, 44)
TEXT_COLOR = (235, 240, 245)
ACCENT_COLOR = (240, 200, 90)
