"""仅用于教学：删除本课 SQLite 文件，让三次调用从初始状态开始。"""

from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parent / "输出" / "idempotency_conflict.sqlite"

if DATABASE_PATH.exists():
    DATABASE_PATH.unlink()
    print(f"已删除旧教学数据库：{DATABASE_PATH}")
else:
    print("没有旧教学数据库，下一次启动服务时会自动创建。")
