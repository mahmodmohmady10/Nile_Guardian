"""كل صورة تشير إليها الخرائط والحوارات يجب أن تكون معرّفة في ملف التجهيز manifest.json."""

from __future__ import annotations

import json

from src.utils.data_loader import load_dialogues_file, load_map_file
from src.utils.paths import resource_path

IMAGES = resource_path("data", "images")


def manifest_outputs() -> set[str]:
    entries = json.loads((IMAGES / "manifest.json").read_text(encoding="utf-8"))
    return {entry["output"] for entry in entries}


def referenced_images() -> set[str]:
    references: set[str] = set()
    for map_file in (resource_path("data", "maps")).glob("*.json"):
        spec = load_map_file(map_file)
        for tile in spec.legend.values():
            for path in (tile.image, tile.overlay):
                if path:
                    references.add(path)
        for obj in spec.objects:
            references.add(obj.image)
    for dialogue in load_dialogues_file(resource_path("data", "dialogues.json")).values():
        if dialogue.portrait:
            references.add(dialogue.portrait)
    return references


def test_every_referenced_image_is_in_the_manifest() -> None:
    missing = referenced_images() - manifest_outputs()
    assert not missing, f"صور غير معرّفة في manifest.json: {sorted(missing)}"


def test_source_files_exist_for_every_manifest_entry() -> None:
    entries = json.loads((IMAGES / "manifest.json").read_text(encoding="utf-8"))
    for entry in entries:
        assert (IMAGES / "_source" / entry["source"]).is_file(), entry["source"]
