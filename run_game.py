"""نقطة تشغيل للتغليف: تستدعي src.main مباشرة، فيعمل الملف التنفيذي دون python -m."""

from src.main import main

if __name__ == "__main__":
    raise SystemExit(main())
