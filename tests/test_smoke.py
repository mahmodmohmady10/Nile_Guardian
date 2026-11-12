"""اختبارات M0: سلامة الهيكل وحارس عزل pygame عن حزم المنطق (NFR-03)."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PURE_PACKAGES = ("core", "logic", "world")
ALL_PACKAGES = ("core", "logic", "world", "engine", "scenes", "utils")


def imported_roots(path: Path) -> Iterator[str]:
    """يُرجع أسماء الوحدات الجذرية المستوردة في ملف بايثون (استيراد مطلق فقط)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module.split(".")[0]


def test_all_packages_have_init() -> None:
    assert (SRC / "__init__.py").is_file()
    for pkg in ALL_PACKAGES:
        assert (SRC / pkg / "__init__.py").is_file(), f"src/{pkg}/__init__.py مفقود"


def test_pure_packages_do_not_import_pygame() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for pkg in PURE_PACKAGES
        for path in (SRC / pkg).rglob("*.py")
        if "pygame" in set(imported_roots(path))
    ]
    assert not offenders, f"ملفات منطق تستورد pygame: {offenders}"


def test_import_guard_detects_pygame(tmp_path: Path) -> None:
    """يتأكد أن الحارس نفسه يعمل، حتى لا يكون الاختبار السابق فارغ المعنى."""
    sample = tmp_path / "bad.py"
    sample.write_text("import pygame.font\nfrom os import path\n", encoding="utf-8")
    assert "pygame" in set(imported_roots(sample))
    assert "os" in set(imported_roots(sample))
