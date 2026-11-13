"""حالة الحوار: الصفحة الحالية والتقدم. بلا pygame."""

from __future__ import annotations

from collections.abc import Sequence


class DialogueState:
    def __init__(self, speaker: str, lines: Sequence[str]) -> None:
        if not lines:
            raise ValueError("الحوار يحتاج سطراً واحداً على الأقل")
        self.speaker = speaker
        self._lines = tuple(lines)
        self._index = 0

    @property
    def current(self) -> str:
        return self._lines[self._index]

    @property
    def index(self) -> int:
        return self._index

    @property
    def total(self) -> int:
        return len(self._lines)

    def advance(self) -> bool:
        """يتقدم صفحة. يُرجع True إذا انتهى الحوار."""
        if self._index < len(self._lines) - 1:
            self._index += 1
            return False
        return True
