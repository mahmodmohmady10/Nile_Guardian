"""الأصوات المستخدمة في الكود يجب أن تكون موجودة وصغيرة الحجم وبترويسة WAV صحيحة."""

from __future__ import annotations

from src.utils.paths import resource_path

SFX_NAMES = ["hit", "crit", "heal", "item", "buy", "upgrade", "victory", "defeat", "capture"]
MUSIC_NAMES = ["menu", "village", "dinder", "battle"]
MAX_BYTES = 200_000


def check_file(path) -> None:
    assert path.is_file(), path
    data = path.read_bytes()
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE", path
    assert len(data) <= MAX_BYTES, path


def test_every_sound_effect_exists_and_is_small() -> None:
    for name in SFX_NAMES:
        check_file(resource_path("data", "audio", "sfx", f"{name}.wav"))


def test_every_music_track_exists_and_is_small() -> None:
    for name in MUSIC_NAMES:
        check_file(resource_path("data", "audio", "music", f"{name}.wav"))
