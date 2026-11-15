"""ملفات الحفظ: المجلد، والقراءة، والكتابة الذرية (بلا pygame)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.core.save import SaveError

SLOT_IDS = ("slot1", "slot2", "slot3")
AUTOSAVE_ID = "autosave"


def default_saves_dir() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home())
    return base / "NileGuardian" / "saves"


def slot_path(directory: Path, slot: str) -> Path:
    return directory / f"{slot}.json"


def read_save(directory: Path, slot: str) -> dict[str, Any] | None:
    path = slot_path(directory, slot)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SaveError(slot, f"ملف تالف: {exc}") from exc
    if not isinstance(data, dict):
        raise SaveError(slot, "ملف غير صالح")
    return data


def write_save(directory: Path, slot: str, data: dict[str, Any]) -> None:
    """يكتب في ملف مؤقت ثم يستبدل الأصل، فلا يضيع الحفظ القديم إن انقطع التشغيل."""
    directory.mkdir(parents=True, exist_ok=True)
    path = slot_path(directory, slot)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
