"""مكدس المشاهد: push و pop و replace، بلا pygame."""

from src.core.scene import Scene


class EmptySceneStackError(RuntimeError):
    """محاولة قراءة أو إزالة مشهد من مكدس فارغ."""


class SceneStack:
    def __init__(self) -> None:
        self._scenes: list[Scene] = []

    def __len__(self) -> int:
        return len(self._scenes)

    @property
    def is_empty(self) -> bool:
        return not self._scenes

    @property
    def top(self) -> Scene:
        if not self._scenes:
            raise EmptySceneStackError("المكدس فارغ")
        return self._scenes[-1]

    def push(self, scene: Scene) -> None:
        """يدفع مشهداً فوق الحالي، والحالي يُوقف مؤقتاً ولا يُدمَّر."""
        if self._scenes:
            self._scenes[-1].on_pause()
        self._scenes.append(scene)
        scene.on_enter()

    def pop(self) -> Scene:
        """يزيل القمة، ويستأنف المشهد الذي تحتها."""
        removed = self._remove_top()
        if self._scenes:
            self._scenes[-1].on_resume()
        return removed

    def replace(self, scene: Scene) -> Scene:
        """يستبدل القمة بمشهد جديد دون استئناف ما تحتها."""
        old = self._remove_top()
        self._scenes.append(scene)
        scene.on_enter()
        return old

    def update(self, dt: float) -> None:
        if self._scenes:
            self._scenes[-1].update(dt)

    def dispatch_action(self, action: str) -> None:
        if self._scenes:
            self._scenes[-1].handle_action(action)

    def set_held(self, held: tuple[str, ...]) -> None:
        if self._scenes:
            self._scenes[-1].set_held(held)

    def visible(self) -> list[Scene]:
        """المشاهد التي تُرسم، من الأسفل إلى الأعلى، بدءاً من آخر مشهد معتم."""
        start = 0
        for index in range(len(self._scenes) - 1, -1, -1):
            if self._scenes[index].opaque:
                start = index
                break
        return self._scenes[start:]

    def _remove_top(self) -> Scene:
        if not self._scenes:
            raise EmptySceneStackError("لا يمكن الإزالة من مكدس فارغ")
        removed = self._scenes.pop()
        removed.on_exit()
        return removed
