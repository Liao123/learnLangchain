"""仅用于教学：删除本课 SQLite 文件，恢复下一次演示所需的空数据状态。"""

from pathlib import Path


LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "idempotency.sqlite"


if DATABASE_PATH.exists():
    DATABASE_PATH.unlink()
    print(f"已删除旧教学数据库：{DATABASE_PATH}")
else:
    print("没有旧教学数据库，下一次启动服务时会自动创建。")
