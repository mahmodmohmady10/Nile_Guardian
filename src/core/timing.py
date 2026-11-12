"""الخطوة الثابتة للمنطق (Fixed Timestep) بمجمّع زمني، بلا pygame."""


class FixedStepClock:
    """يحوّل زمن الإطار المتغير إلى عدد صحيح من خطوات المنطق الثابتة."""

    def __init__(self, step: float, max_frame: float, max_steps: int) -> None:
        if step <= 0:
            raise ValueError("step يجب أن يكون موجباً")
        if max_steps < 1:
            raise ValueError("max_steps يجب أن يكون 1 على الأقل")
        self.step = step
        self.max_frame = max_frame
        self.max_steps = max_steps
        self._accumulator = 0.0

    @property
    def alpha(self) -> float:
        """نسبة الخطوة الجزئية (0 إلى 1)، للرسم بين حالتين إن احتاج ذلك."""
        return self._accumulator / self.step

    def advance(self, frame_dt: float) -> int:
        """يُرجع عدد خطوات المنطق المطلوب تنفيذها لهذا الإطار."""
        if frame_dt < 0:
            raise ValueError("frame_dt لا يمكن أن يكون سالباً")
        self._accumulator += min(frame_dt, self.max_frame)
        steps = int(self._accumulator // self.step)
        if steps > self.max_steps:
            # تخلّف كبير: نُسقط الفائض بدل تنفيذ مئات الخطوات دفعة واحدة.
            self._accumulator = 0.0
            return self.max_steps
        self._accumulator -= steps * self.step
        if self._accumulator < 0.0:
            self._accumulator = 0.0
        return steps

    def reset(self) -> None:
        self._accumulator = 0.0
