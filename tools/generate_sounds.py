"""توليد أصوات بسيطة (مؤثرات وموسيقى حلقية) بمكتبات بايثون القياسية فقط.

الصيغة: WAV بعينات 8 بت، تردد 11025 هرتز، أحادي: ملفات صغيرة وتعمل مع pygame مباشرة.
كل الأصوات بدائية (أمواج مربعة ومثلثة) وقابلة للاستبدال لاحقاً بملفات مرخّصة بالاسم نفسه.

الاستخدام من جذر المشروع:
    python tools/generate_sounds.py
"""

from __future__ import annotations

import math
import random
import struct
from pathlib import Path

RATE = 11025
ROOT = Path(__file__).resolve().parents[1]
SFX_DIR = ROOT / "data" / "audio" / "sfx"
MUSIC_DIR = ROOT / "data" / "audio" / "music"


def write_wav(path: Path, samples: list[float]) -> None:
    """يكتب عينات بين -1 و1 كملف WAV (8 بت، أحادي) بترويسة يدوية."""
    data = bytes(int(max(-1.0, min(1.0, value)) * 127 + 128) for value in samples)
    header = (
        b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVE"
        + b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, RATE, RATE, 1, 8)
        + b"data" + struct.pack("<I", len(data))
    )
    path.write_bytes(header + data)


def wave_value(kind: str, phase: float) -> float:
    if kind == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if kind == "triangle":
        return 2.0 / math.pi * math.asin(math.sin(phase))
    return math.sin(phase)


def tone(freq: float, seconds: float, kind: str = "square", volume: float = 0.4) -> list[float]:
    count = int(RATE * seconds)
    out = []
    for i in range(count):
        envelope = 1.0 - i / count  # تلاشٍ بسيط في نهاية كل نغمة
        out.append(wave_value(kind, 2 * math.pi * freq * i / RATE) * volume * envelope)
    return out


def sweep(start: float, end: float, seconds: float, kind: str = "square",
          volume: float = 0.4) -> list[float]:
    count = int(RATE * seconds)
    out, phase = [], 0.0
    for i in range(count):
        freq = start + (end - start) * i / count
        phase += 2 * math.pi * freq / RATE
        out.append(wave_value(kind, phase) * volume * (1.0 - i / count))
    return out


def noise(seconds: float, volume: float = 0.4, seed: int = 1) -> list[float]:
    rng = random.Random(seed)
    count = int(RATE * seconds)
    return [(rng.random() * 2 - 1) * volume * (1.0 - i / count) for i in range(count)]


def mix(*tracks: list[float]) -> list[float]:
    length = max(len(track) for track in tracks)
    out = [0.0] * length
    for track in tracks:
        for i, value in enumerate(track):
            out[i] += value
    return out


def chain(*parts: list[float]) -> list[float]:
    out: list[float] = []
    for part in parts:
        out.extend(part)
    return out


def note_freq(name: str) -> float:
    """اسم النغمة مثل C4 أو A#5 إلى تردد بالهرتز. R تعني صمتاً."""
    if name == "R":
        return 0.0
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
             "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    octave = int(name[-1])
    semitone = names[name[:-1]]
    midi = (octave + 1) * 12 + semitone
    return 440.0 * 2 ** ((midi - 69) / 12)


def sequence(notes: list[tuple[str, float]], kind: str, volume: float) -> list[float]:
    parts = []
    for name, beats in notes:
        seconds = beats
        if name == "R":
            parts.append([0.0] * int(RATE * seconds))
        else:
            parts.append(tone(note_freq(name), seconds, kind, volume))
    return chain(*parts)


def loop(melody: list[tuple[str, float]], bass: list[tuple[str, float]]) -> list[float]:
    """يكرر اللحن مرتين لتطول الحلقة قليلاً دون زيادة كبيرة في الحجم."""
    return mix(sequence(melody * 2, "square", 0.12), sequence(bass * 2, "triangle", 0.18))


SFX = {
    "click": lambda: tone(880, 0.04, "square", 0.25),
    "hit": lambda: mix(noise(0.15, 0.35, seed=3), sweep(320, 120, 0.15, "square", 0.25)),
    "crit": lambda: chain(
        mix(noise(0.12, 0.4, seed=5), sweep(360, 120, 0.12, "square", 0.3)),
        sequence([("C6", 0.05), ("G6", 0.08)], "square", 0.25),
    ),
    "heal": lambda: sequence([("C5", 0.06), ("E5", 0.06), ("G5", 0.06), ("C6", 0.12)],
                             "triangle", 0.3),
    "buy": lambda: sequence([("B5", 0.05), ("E6", 0.1)], "square", 0.25),
    "upgrade": lambda: chain(
        sweep(400, 1200, 0.35, "square", 0.25),
        sequence([("C6", 0.08), ("E6", 0.08), ("G6", 0.08), ("C7", 0.15)], "triangle", 0.3),
    ),
    "item": lambda: sweep(600, 900, 0.08, "triangle", 0.3),
    "capture": lambda: sweep(300, 900, 0.35, "triangle", 0.3),
    "victory": lambda: sequence([("C5", 0.1), ("E5", 0.1), ("G5", 0.1), ("C6", 0.25)],
                                "square", 0.25),
    "defeat": lambda: sweep(392, 98, 0.6, "triangle", 0.35),
}

MUSIC = {
    "menu": (
        [("C5", 0.5), ("E5", 0.5), ("G5", 0.5), ("E5", 0.5), ("A5", 0.5), ("G5", 0.5),
         ("E5", 0.5), ("R", 0.5)],
        [("C3", 1.0), ("G3", 1.0), ("A3", 1.0), ("F3", 1.0)],
    ),
    "village": (
        [("E5", 0.5), ("G5", 0.5), ("A5", 0.5), ("G5", 0.5), ("E5", 0.5), ("D5", 0.5),
         ("C5", 0.5), ("R", 0.5)],
        [("C3", 1.0), ("A2", 1.0), ("F2", 1.0), ("G2", 1.0)],
    ),
    "dinder": (
        [("D5", 0.5), ("E5", 0.5), ("G5", 0.5), ("A5", 0.5), ("G5", 0.5), ("E5", 0.5),
         ("D5", 0.5), ("R", 0.5)],
        [("D3", 1.0), ("G2", 1.0), ("A2", 1.0), ("D3", 1.0)],
    ),
    "battle": (
        [("A4", 0.25), ("C5", 0.25), ("E5", 0.25), ("A5", 0.25), ("G5", 0.25), ("E5", 0.25),
         ("C5", 0.25), ("E5", 0.25)],
        [("A2", 0.5), ("A2", 0.5), ("F2", 0.5), ("G2", 0.5)],
    ),
}


def main() -> int:
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    for name, make in SFX.items():
        write_wav(SFX_DIR / f"{name}.wav", make())
    for name, (melody, bass) in MUSIC.items():
        write_wav(MUSIC_DIR / f"{name}.wav", loop(melody, bass))
    print("أصوات المؤثرات:", ", ".join(SFX))
    print("الموسيقى:", ", ".join(MUSIC))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
