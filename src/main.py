"""نقطة الدخول: python -m src.main"""

from __future__ import annotations

import sys

import pygame

from src.config import FONT_FILE, HEIGHT, TEXT_CACHE_SIZE, TITLE, WIDTH
from src.core.scene import Scene
from src.core.scene_stack import SceneStack
from src.engine.game import Game
from src.engine.text_renderer import TextRenderer
from src.scenes.dialogue_scene import DialogueScene
from src.scenes.menu_scene import MenuScene
from src.scenes.world_scene import WorldScene
from src.utils.data_loader import (
    Dialogue,
    MapSpec,
    MapValidationError,
    check_npc_dialogues,
    load_dialogues_file,
    load_map_file,
)
from src.utils.paths import resource_path

VILLAGE_MAP = ("data", "maps", "village_01.json")
DIALOGUES = ("data", "dialogues.json")
VILLAGE_NAME = "village_01.json"


def make_menu(
    stack: SceneStack,
    spec: MapSpec,
    dialogues: dict[str, Dialogue],
    renderer: TextRenderer,
) -> MenuScene:
    def open_dialogue(dialogue_id: str) -> None:
        stack.push(
            DialogueScene(dialogues[dialogue_id], renderer, on_finish=lambda: stack.pop())
        )

    def start_world() -> Scene:
        return WorldScene(
            spec,
            on_back=lambda: stack.replace(make_menu(stack, spec, dialogues, renderer)),
            open_dialogue=open_dialogue,
        )

    return MenuScene(stack, start_world)


def main() -> int:
    try:
        spec = load_map_file(resource_path(*VILLAGE_MAP))
        dialogues = load_dialogues_file(resource_path(*DIALOGUES))
        check_npc_dialogues(spec, dialogues, VILLAGE_NAME)
    except MapValidationError as exc:
        print(f"خطأ في بيانات اللعبة: {exc}", file=sys.stderr)
        return 1

    font_path = resource_path("assets", "fonts", FONT_FILE)
    if not font_path.is_file():
        print(f"الخط العربي مفقود: ضع {FONT_FILE} في assets/fonts/", file=sys.stderr)
        return 1

    pygame.init()
    try:
        pygame.display.set_caption(TITLE)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        renderer = TextRenderer(font_path, TEXT_CACHE_SIZE)
        stack = SceneStack()
        stack.push(make_menu(stack, spec, dialogues, renderer))
        Game(stack, screen).run()
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
