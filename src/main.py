"""نقطة الدخول: python -m src.main"""

from __future__ import annotations

import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pygame

from src.config import FONT_FILE, HEIGHT, TEXT_CACHE_SIZE, TITLE, WIDTH
from src.core.game_state import GameState
from src.core.save import SaveError, restore, snapshot
from src.core.scene_stack import SceneStack
from src.engine.game import Game
from src.engine.text_renderer import TextRenderer
from src.logic.battle_engine import (
    OUTCOME_CAPTURED,
    OUTCOME_ENEMY_FLED,
    OUTCOME_LOST,
    OUTCOME_WON,
    BattleEngine,
)
from src.logic.models import AnimalInstance, Item, xp_reward
from src.scenes.bag_scene import BagScene
from src.scenes.battle_scene import BattleScene
from src.scenes.confirm_scene import ConfirmScene
from src.scenes.dialogue_scene import DialogueScene
from src.scenes.hospital_scene import HospitalScene
from src.scenes.menu_scene import MenuItems, MenuScene
from src.scenes.shop_scene import ShopScene
from src.scenes.slot_scene import SlotScene
from src.scenes.world_scene import WorldScene
from src.utils.data_loader import (
    Catalog,
    Dialogue,
    MapSpec,
    MapValidationError,
    NewGameSpec,
    build_guide,
    check_animal_refs,
    check_event_dialogues,
    check_npc_dialogues,
    check_objectives,
    check_party_refs,
    check_teleport_refs,
    load_catalog,
    load_dialogues_file,
    load_items_file,
    load_map_file,
    load_new_game_file,
    load_objectives_file,
)
from src.utils.paths import resource_path
from src.utils.saves import AUTOSAVE_ID, SLOT_IDS, default_saves_dir, read_save, write_save
from src.world.objectives import GuideData

MAP_FILES = {"village_01": "village_01.json", "dinder_01": "dinder_01.json"}
MAP_NAMES = {"village_01": "القرية", "dinder_01": "الدندر"}
DIALOGUES = ("data", "dialogues.json")
NEW_GAME = ("data", "new_game.json")
ANIMALS = ("data", "animals.json")
MOVES = ("data", "moves.json")
OBJECTIVES = ("data", "objectives.json")
ITEMS = ("data", "items.json")
ITEMS_NAME = "items.json"
NEW_GAME_NAME = "new_game.json"
OBJECTIVES_NAME = "objectives.json"
VILLAGE_NAME = "village_01.json"


@dataclass
class Session:
    stack: SceneStack
    maps: dict[str, MapSpec]
    state: GameState
    dialogues: dict[str, Dialogue]
    catalog: Catalog
    renderer: TextRenderer
    rng: random.Random
    guide: GuideData
    new_game: NewGameSpec
    items: dict[str, Item]
    saves_dir: Path
    started: bool = False
    last_saved: dict | None = None


def build_fresh_state(
    new_game: NewGameSpec, catalog: Catalog, maps: dict[str, MapSpec]
) -> GameState:
    spawn = maps[new_game.map_id].spawn
    state = GameState(
        player_name=new_game.player_name,
        map_id=new_game.map_id,
        templates=catalog.animals,
        grid_x=spawn[0],
        grid_y=spawn[1],
    )
    for animal_id in new_game.party:
        state.give_animal(animal_id)
    return state


def has_unsaved(session: Session) -> bool:
    return session.started and session.last_saved != snapshot(session.state)


def persist(session: Session, slot: str) -> None:
    data = snapshot(session.state)
    write_save(session.saves_dir, slot, data)
    session.last_saved = data


def autosave(session: Session) -> None:
    try:
        persist(session, AUTOSAVE_ID)
    except OSError as exc:
        print(f"تعذر الحفظ التلقائي: {exc}", file=sys.stderr)


def describe_slot(session: Session, slot: str) -> str:
    try:
        data = read_save(session.saves_dir, slot)
    except SaveError:
        return "ملف تالف"
    if data is None:
        return "فارغة"
    map_name = MAP_NAMES.get(str(data.get("map_id")), "غير معروفة")
    party = data.get("party")
    count = len(party) if isinstance(party, list) else 0
    return f"{map_name} — الفريق {count}"


def start_new_game(session: Session) -> None:
    session.state = build_fresh_state(session.new_game, session.catalog, session.maps)
    session.started = True
    session.last_saved = None
    session.stack.replace(make_world(session))


def request_new_game(session: Session) -> None:
    if has_unsaved(session):
        session.stack.push(
            ConfirmScene(
                session.stack,
                session.renderer,
                "ستفقد التقدم غير المحفوظ. هل تريد المتابعة؟",
                on_yes=lambda: start_new_game(session),
            )
        )
    else:
        start_new_game(session)


def save_to(session: Session, slot: str) -> None:
    try:
        persist(session, slot)
    except OSError as exc:
        print(f"تعذر الحفظ: {exc}", file=sys.stderr)
        return
    session.stack.pop()


def load_from(session: Session, slot: str) -> None:
    try:
        data = read_save(session.saves_dir, slot)
        if data is None:
            return
        sizes = {map_id: (spec.width, spec.height) for map_id, spec in session.maps.items()}
        restored = restore(data, session.catalog.animals, sizes, item_ids=set(session.items))
    except SaveError:
        return
    session.state = restored
    session.started = True
    session.last_saved = snapshot(restored)
    session.stack.pop()
    session.stack.replace(make_world(session))


def menu_items(session: Session) -> MenuItems:
    items: MenuItems = []
    if session.started:
        items.append(("متابعة", lambda: session.stack.replace(make_world(session))))
    items.append(("لعبة جديدة", lambda: request_new_game(session)))
    if session.started:
        items.append(("حفظ", lambda: open_save(session)))
    items.append(("الحقيبة", lambda: open_bag(session)))
    items.append(("تحميل", lambda: open_load(session)))
    items.append(("خروج", lambda: session.stack.pop()))
    return items


def make_menu(session: Session) -> MenuScene:
    return MenuScene(session.stack, session.renderer, lambda: menu_items(session))


def open_bag(session: Session) -> None:
    session.stack.push(BagScene(session.stack, session.renderer, session.state, session.items))


def open_save(session: Session) -> None:
    session.stack.push(
        SlotScene(
            session.stack,
            session.renderer,
            "حفظ",
            SLOT_IDS,
            describe=lambda slot: describe_slot(session, slot),
            on_choose=lambda slot: save_to(session, slot),
        )
    )


def open_load(session: Session) -> None:
    session.stack.push(
        SlotScene(
            session.stack,
            session.renderer,
            "تحميل",
            (*SLOT_IDS, AUTOSAVE_ID),
            describe=lambda slot: describe_slot(session, slot),
            on_choose=lambda slot: load_from(session, slot),
        )
    )


def make_world(session: Session) -> WorldScene:
    return WorldScene(
        session.state,
        load_map=lambda map_id: session.maps[map_id],
        on_back=lambda: session.stack.replace(make_menu(session)),
        open_dialogue=lambda dialogue_id, on_done: open_dialogue(session, dialogue_id, on_done),
        open_battle=lambda enemy_id, on_end: open_battle(session, enemy_id, on_end),
        rng=session.rng,
        guide=session.guide,
        renderer=session.renderer,
        on_map_changed=lambda: autosave(session),
        open_shop=lambda: open_shop(session),
        open_hospital=lambda: open_hospital(session),
    )


def open_hospital(session: Session) -> None:
    session.stack.push(HospitalScene(session.stack, session.renderer, session.state))


def open_shop(session: Session) -> None:
    session.stack.push(
        ShopScene(session.stack, session.renderer, session.state, list(session.items.values()))
    )


def open_dialogue(session: Session, dialogue_id: str, on_done: Callable[[], None]) -> None:
    def finish() -> None:
        session.stack.pop()
        on_done()

    scene = DialogueScene(session.dialogues[dialogue_id], session.renderer, on_finish=finish)
    session.stack.push(scene)


def open_battle(session: Session, enemy_id: str, on_end: Callable[[str], None]) -> None:
    if session.state.lead() is None:
        return
    enemy = AnimalInstance.fresh(session.catalog.animals[enemy_id])
    engine = BattleEngine(session.state.party, enemy, session.catalog.moves, session.rng)

    def finish(outcome: str) -> None:
        if outcome == OUTCOME_LOST:
            session.state.heal_party()
        if outcome in (OUTCOME_WON, OUTCOME_ENEMY_FLED, OUTCOME_CAPTURED):
            session.state.mark_defeated(enemy_id)
            session.state.add_money(enemy.template.reward_money)
            session.state.award_xp(xp_reward(enemy.template))
        if outcome == OUTCOME_CAPTURED and not engine.needs_replacement():
            session.state.party.append(engine.captured)
        session.stack.pop()
        on_end(outcome)

    item_names = {item_id: item.name_ar for item_id, item in session.items.items()}
    session.stack.push(
        BattleScene(
            engine,
            session.renderer,
            on_finish=finish,
            bag=session.state.bag,
            item_names=item_names,
            move_names={
                move_id: move.name_ar for move_id, move in session.catalog.moves.items()
            },
        )
    )


def load_everything() -> tuple[
    dict[str, MapSpec], dict[str, Dialogue], Catalog, NewGameSpec, GuideData, dict[str, Item]
]:
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
    objectives = load_objectives_file(resource_path(*OBJECTIVES))
    check_objectives(objectives, maps, catalog, OBJECTIVES_NAME)
    items = load_items_file(resource_path(*ITEMS))
    return maps, dialogues, catalog, new_game, build_guide(maps, objectives), items


def main() -> int:
    try:
        maps, dialogues, catalog, new_game, guide, items = load_everything()
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
        stack = SceneStack()
        session = Session(
            stack=stack,
            maps=maps,
            state=build_fresh_state(new_game, catalog, maps),
            dialogues=dialogues,
            catalog=catalog,
            renderer=TextRenderer(font_path, TEXT_CACHE_SIZE),
            rng=random.Random(),
            guide=guide,
            new_game=new_game,
            items=items,
            saves_dir=default_saves_dir(),
        )
        stack.push(make_menu(session))
        Game(stack, screen).run()
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
