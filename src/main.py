"""نقطة الدخول: python -m src.main"""

from __future__ import annotations

import sys

import pygame

from src.config import HEIGHT, TITLE, WIDTH
from src.core.scene import Scene
from src.core.scene_stack import SceneStack
from src.engine.game import Game
from src.scenes.menu_scene import MenuScene
from src.scenes.world_scene import WorldScene
from src.utils.data_loader import MapSpec, MapValidationError, load_map_file
from src.utils.paths import resource_path

VILLAGE_MAP = ("data", "maps", "village_01.json")


def make_menu(stack: SceneStack, spec: MapSpec) -> MenuScene:
    def start_world() -> Scene:
        return WorldScene(spec, on_back=lambda: stack.replace(make_menu(stack, spec)))

    return MenuScene(stack, start_world)


def main() -> int:
    try:
        spec = load_map_file(resource_path(*VILLAGE_MAP))
    except MapValidationError as exc:
        print(f"خطأ في بيانات الخريطة: {exc}", file=sys.stderr)
        return 1
    pygame.init()
    try:
        pygame.display.set_caption(TITLE)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        stack = SceneStack()
        stack.push(make_menu(stack, spec))
        Game(stack, screen).run()
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
