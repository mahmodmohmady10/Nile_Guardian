"""نقطة الدخول: python -m src.main"""

from __future__ import annotations

import random
import sys
from collections.abc import Callable
from dataclasses import dataclass

import pygame

from src.config import FONT_FILE, HEIGHT, TEXT_CACHE_SIZE, TITLE, WIDTH
from src.core.game_state import GameState
from src.core.scene_stack import SceneStack
from src.engine.game import Game
from src.engine.text_renderer import TextRenderer
from src.logic.battle_engine import OUTCOME_LOST, BattleEngine
from src.logic.models import AnimalInstance
from src.scenes.battle_scene import BattleScene
from src.scenes.dialogue_scene import DialogueScene
from src.scenes.menu_scene import MenuScene
from src.scenes.world_scene import WorldScene
from src.utils.data_loader import (
    Catalog,
    Dialogue,
    MapSpec,
    MapValidationError,
    NewGameSpec,
    check_animal_refs,
    check_event_dialogues,
    check_npc_dialogues,
    check_party_refs,
    check_teleport_refs,
    load_catalog,
    load_dialogues_file,
    load_map_file,
    load_new_game_file,
)
from src.utils.paths import resource_path

MAP_FILES = {"village_01": "village_01.json", "dinder_01": "dinder_01.json"}
DIALOGUES = ("data", "dialogues.json")
NEW_GAME = ("data", "new_game.json")
ANIMALS = ("data", "animals.json")
MOVES = ("data", "moves.json")
NEW_GAME_NAME = "new_game.json"
START_MAP = "village_01"


@dataclass
class Session:
    stack: SceneStack
    maps: dict[str, MapSpec]
    state: GameState
    dialogues: dict[str, Dialogue]
    catalog: Catalog
    renderer: TextRenderer
    rng: random.Random


def make_menu(session: Session) -> MenuScene:
    return MenuScene(session.stack, lambda: make_world(session))


def make_world(session: Session) -> WorldScene:
    return WorldScene(
        session.state,
        load_map=lambda map_id: session.maps[map_id],
        on_back=lambda: session.stack.replace(make_menu(session)),
        open_dialogue=lambda dialogue_id, on_done: open_dialogue(session, dialogue_id, on_done),
        open_battle=lambda enemy_id, on_end: open_battle(session, enemy_id, on_end),
        rng=session.rng,
    )


def open_dialogue(session: Session, dialogue_id: str, on_done: Callable[[], None]) -> None:
    def finish() -> None:
        session.stack.pop()
        on_done()

    scene = DialogueScene(session.dialogues[dialogue_id], session.renderer, on_finish=finish)
    session.stack.push(scene)


def open_battle(session: Session, enemy_id: str, on_end: Callable[[str], None]) -> None:
    lead = session.state.lead()
    if lead is None:
        return
    enemy = AnimalInstance.fresh(session.catalog.animals[enemy_id])
    engine = BattleEngine(lead, enemy, session.catalog.moves, session.rng)

    def finish(outcome: str) -> None:
        if outcome == OUTCOME_LOST:
            session.state.heal_party()
        session.stack.pop()
        on_end(outcome)

    session.stack.push(BattleScene(engine, session.renderer, on_finish=finish))


def load_everything() -> tuple[dict[str, MapSpec], dict[str, Dialogue], Catalog, NewGameSpec]:
    maps = {
        map_id: load_map_file(resource_path("data", "maps", filename))
        for map_id, filename in MAP_FILES.items()
    }
    dialogues = load_dialogues_file(resource_path(*DIALOGUES))
    catalog = load_catalog(resource_path(*ANIMALS), resource_path(*MOVES))
    new_game = load_new_game_file(resource_path(*NEW_GAME))
    for map_id, spec in maps.items():
        source = MAP_FILES[map_id]
        check_npc_dialogues(spec, dialogues, source)
        check_event_dialogues(spec, dialogues, source)
        check_animal_refs(spec, catalog, source)
        check_teleport_refs(spec, maps, source)
    check_party_refs(new_game, catalog, NEW_GAME_NAME)
    if new_game.map_id not in maps:
        raise MapValidationError(NEW_GAME_NAME, "map_id", f"خريطة غير معروفة: {new_game.map_id}")
    return maps, dialogues, catalog, new_game


def main() -> int:
    try:
        maps, dialogues, catalog, new_game = load_everything()
    except MapValidationError as exc:
        print(f"خطأ في بيانات اللعبة: {exc}", file=sys.stderr)
        return 1

    font_path = resource_path("assets", "fonts", FONT_FILE)
    if not font_path.is_file():
        print(f"الخط العربي مفقود: ضع {FONT_FILE} في assets/fonts/", file=sys.stderr)
        return 1

    state = GameState(
        player_name=new_game.player_name,
        map_id=new_game.map_id,
        templates=catalog.animals,
        grid_x=maps[new_game.map_id].spawn[0],
        grid_y=maps[new_game.map_id].spawn[1],
    )
    for animal_id in new_game.party:
        state.give_animal(animal_id)

    pygame.init()
    try:
        pygame.display.set_caption(TITLE)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        stack = SceneStack()
        session = Session(
            stack=stack,
            maps=maps,
            state=state,
            dialogues=dialogues,
            catalog=catalog,
            renderer=TextRenderer(font_path, TEXT_CACHE_SIZE),
            rng=random.Random(),
        )
        stack.push(make_menu(session))
        Game(stack, screen).run()
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
