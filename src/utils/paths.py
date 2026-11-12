"""إدارة المسارات، متوافقة مع PyInstaller (التي تضع الملفات في sys._MEIPASS)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    """يُرجع مساراً داخل مجلد الموارد، سواء في وضع التطوير أو بعد التغليف."""
    base = Path(getattr(sys, "_MEIPASS", ROOT))
    return base.joinpath(*parts)
