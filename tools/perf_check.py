"""قياس أداء يدوي: زمن تحديث ورسم المشهد لكل إطار، وذروة الذاكرة في بايثون.

يعمل بلا نافذة ظاهرة. التشغيل من جذر المشروع:
    python tools/perf_check.py

ملاحظة: الرقم الحقيقي للذاكرة في Windows يُقرأ من مدير المهام (عمود Memory) أثناء التشغيل،
فهذه الأداة تقيس كومة بايثون فقط، وتعطي مؤشراً تقريبياً.
"""

from __future__ import annotations

import os
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402
from src.config import HEIGHT, STEP, WIDTH  # noqa: E402
from src.core.game_state import GameState  # noqa: E402
from src.scenes.world_scene import WorldScene  # noqa: E402
from src.utils.data_loader import load_map_file  # noqa: E402

FRAMES = 1200


def main() -> int:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    spec = load_map_file(ROOT / "data" / "maps" / "village_01.json")
    state = GameState(player_name="الأمين", map_id="village_01")
    state.grid_x, state.grid_y = spec.spawn
    scene = WorldScene(
        state=state,
        load_map=lambda _map_id: spec,
        on_back=lambda: None,
        open_dialogue=lambda _id, _done: None,
        open_battle=lambda _id, _end: None,
        rng=random.Random(0),
    )
    scene.set_held(("right",))
    tracemalloc.start()
    frame_ms: list[float] = []
    for frame in range(FRAMES):
        if frame % 40 == 0:
            scene.set_held(("right",) if (frame // 40) % 2 == 0 else ("left",))
        started = time.perf_counter()
        scene.update(STEP)
        scene.draw(screen)
        frame_ms.append((time.perf_counter() - started) * 1000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    pygame.quit()

    print(f"frames: {FRAMES}")
    print(f"avg update+draw: {statistics.fmean(frame_ms):.3f} ms  (هدف: أقل من 16.6 ms)")
    print(f"p95:            {sorted(frame_ms)[int(FRAMES * 0.95)]:.3f} ms")
    print(f"max:            {max(frame_ms):.3f} ms")
    print(f"python heap peak: {peak / (1024 * 1024):.2f} MB  (هدف: أقل من 150 MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
