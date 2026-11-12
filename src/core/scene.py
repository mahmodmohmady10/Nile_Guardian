"""واجهة المشهد (Scene). بلا pygame، لتبقى قابلة للاختبار."""

from typing import Any


class Scene:
    """قاعدة المشاهد. المشهد الفرعي يعيد تعريف ما يحتاجه فقط."""

    # إن كان False يُرسم المشهد الذي تحته أيضاً (مثل نافذة حوار فوق الخريطة).
    opaque: bool = True

    def on_enter(self) -> None:
        """يُستدعى عند دخول المكدس."""

    def on_exit(self) -> None:
        """يُستدعى عند الخروج من المكدس نهائياً."""

    def on_pause(self) -> None:
        """يُستدعى عندما يُدفع مشهد جديد فوقه."""

    def on_resume(self) -> None:
        """يُستدعى عندما يعود إلى القمة بعد إزالة ما فوقه."""

    def update(self, dt: float) -> None:
        """منطق خطوة ثابتة مدتها STEP. لا يُستدعى إلا للمشهد الأعلى."""

    def handle_action(self, action: str) -> None:
        """يستقبل فعلاً مجرداً مثل up أو confirm، لا رمز مفتاح."""

    def set_held(self, held: tuple[str, ...]) -> None:
        """الأفعال المضغوطة الآن، بترتيب الضغط والأحدث في النهاية."""

    def draw(self, surface: Any) -> None:
        """رسم المشهد. يُستدعى لكل المشاهد المرئية."""
