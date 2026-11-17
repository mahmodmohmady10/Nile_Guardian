"""اختبارات الصور بالبكسل والمؤثرات البصرية للمعركة."""

from __future__ import annotations

from typing import Any

import pytest
from src.core.effects import (
    FLASH_LIFE,
    FLOAT_LIFE,
    SHAKE_LIFE,
    SIDE_ENEMY,
    SIDE_PLAYER,
    EffectsState,
)
from src.utils.data_loader import MapValidationError, load_catalog
from src.utils.paths import resource_path
from src.utils.sprites import SPRITE_SIZE, check_sprites_cover, load_sprites_file, validate_sprites


def valid_sprite() -> dict[str, Any]:
    return {"palette": {"K": [0, 0, 0]}, "rows": ["K" * SPRITE_SIZE] * SPRITE_SIZE}


def error_for(data: Any) -> MapValidationError:
    with pytest.raises(MapValidationError) as info:
        validate_sprites(data, "sprites.json")
    return info.value


def test_real_sprites_cover_every_animal() -> None:
    sprites = load_sprites_file(resource_path("data", "sprites", "animals.json"))
    catalog = load_catalog(
        resource_path("data", "animals.json"), resource_path("data", "moves.json")
    )
    check_sprites_cover(set(catalog.animals), sprites, "animals.json")
    assert len(sprites) == 6


def test_valid_sprite_loads() -> None:
    sprite = validate_sprites({"dot": valid_sprite()}, "sprites.json")["dot"]
    assert len(sprite.rows) == SPRITE_SIZE and sprite.palette["K"] == (0, 0, 0)


def test_wrong_row_count_is_named() -> None:
    data = {"dot": valid_sprite()}
    data["dot"]["rows"] = data["dot"]["rows"][:-1]
    assert error_for(data).field == "dot.rows"


def test_wrong_row_length_is_named() -> None:
    data = {"dot": valid_sprite()}
    data["dot"]["rows"][3] = "K" * (SPRITE_SIZE + 1)
    assert error_for(data).field == "dot.rows[3]"


def test_unknown_symbol_is_named() -> None:
    data = {"dot": valid_sprite()}
    data["dot"]["rows"][0] = "Z" + "K" * (SPRITE_SIZE - 1)
    assert error_for(data).field == "dot.rows[0]"


def test_missing_animal_sprite_is_reported() -> None:
    with pytest.raises(MapValidationError) as info:
        check_sprites_cover({"dragon"}, {}, "sprites.json")
    assert info.value.field == "dragon"


def test_damage_text_shows_display_units_and_critical_mark() -> None:
    effects = EffectsState()
    effects.add_damage(SIDE_ENEMY, 150, critical=True)
    assert effects.texts[0].text == "!-15"


def test_floating_text_disappears_after_its_life() -> None:
    effects = EffectsState()
    effects.add_heal(SIDE_PLAYER, 30)
    effects.update(FLOAT_LIFE / 2)
    assert len(effects.texts) == 1
    effects.update(FLOAT_LIFE)
    assert effects.texts == []


def test_flash_lasts_briefly_on_the_hit_side_only() -> None:
    effects = EffectsState()
    effects.add_damage(SIDE_ENEMY, 20)
    assert effects.is_flashing(SIDE_ENEMY) and not effects.is_flashing(SIDE_PLAYER)
    effects.update(FLASH_LIFE + 0.01)
    assert not effects.is_flashing(SIDE_ENEMY)


def test_shake_only_while_active_and_moves_horizontally() -> None:
    effects = EffectsState()
    assert effects.shake_offset() == (0, 0)
    effects.add_shake()
    dx, dy = effects.shake_offset()
    assert dx != 0 and dy == 0
    effects.update(SHAKE_LIFE + 0.01)
    assert effects.shake_offset() == (0, 0)


def test_floating_numbers_take_different_columns() -> None:
    effects = EffectsState()
    for _ in range(3):
        effects.add_damage(SIDE_ENEMY, 10)
    assert [text.column for text in effects.texts] == [0, 1, 2]


def test_columns_wrap_around_after_three() -> None:
    effects = EffectsState()
    for _ in range(4):
        effects.add_damage(SIDE_ENEMY, 10)
    assert effects.texts[3].column == 0


def test_columns_are_per_side() -> None:
    effects = EffectsState()
    effects.add_damage(SIDE_ENEMY, 10)
    effects.add_damage(SIDE_PLAYER, 10)
    assert [text.column for text in effects.texts] == [0, 0]
