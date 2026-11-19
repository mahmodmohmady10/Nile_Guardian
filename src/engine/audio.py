"""مدير الصوت: موسيقى حلقية ومؤثرات من ملفات WAV. إن تعذّر الصوت تصمت اللعبة دون أن تتوقف."""

from __future__ import annotations

from pathlib import Path

import pygame

SFX_VOLUME = 0.6
MUSIC_VOLUME = 0.35


class AudioManager:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._sfx: dict[str, pygame.mixer.Sound] = {}
        self._music_name: str | None = None
        self.enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def play_sfx(self, name: str) -> None:
        if not self.enabled:
            return
        sound = self._sfx.get(name)
        if sound is None:
            path = self._root / "sfx" / f"{name}.wav"
            if not path.is_file():
                return
            try:
                sound = pygame.mixer.Sound(str(path))
            except pygame.error:
                return
            sound.set_volume(SFX_VOLUME)
            self._sfx[name] = sound
        sound.play()

    def play_music(self, name: str) -> None:
        if not self.enabled or name == self._music_name:
            return
        self._music_name = name
        path = self._root / "music" / f"{name}.wav"
        if not path.is_file():
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
        except pygame.error:
            return
