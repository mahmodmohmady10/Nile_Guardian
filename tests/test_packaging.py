"""اختبارات التغليف: الملفات المطلوبة موجودة، وإعداد PyInstaller يضمّن البيانات."""

from __future__ import annotations

from src.utils.paths import ROOT, resource_path


def test_entry_script_exists_and_calls_main() -> None:
    text = (ROOT / "run_game.py").read_text(encoding="utf-8")
    assert "from src.main import main" in text


def test_spec_bundles_data_and_assets() -> None:
    spec = (ROOT / "nile_guardian.spec").read_text(encoding="utf-8")
    assert '("data", "data")' in spec and '("assets", "assets")' in spec
    assert 'name="NileGuardian"' in spec


def test_resource_path_points_inside_project_in_development() -> None:
    assert resource_path("data", "animals.json").exists()
