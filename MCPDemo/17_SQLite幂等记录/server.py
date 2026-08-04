"""将幂等记录保存到 SQLite，使其在 MCP 服务重启后仍然存在。"""

import json
import sqlite3
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8021
MCP_URL = f"http://{HOST}:{PORT}/mcp"
WRITE_DELAY_SECONDS = 2
LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "idempotency.sqlite"

mcp = FastMCP("星光咖啡持久化取消订单服务", host=HOST, port=PORT)


def setup_database() -> None:
    """首次启动时创建订单表和幂等记录表。"""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                cancelled_count INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_requests (
                idempotency_key TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                state TEXT NOT NULL,
                response_json TEXT
            )
            """
        )
        # 第一次启动时插入 A1001；之后服务重启不会覆盖已经取消的状态。
        connection.execute(
            """
            INSERT OR IGNORE INTO orders (order_id, status, cancelled_count)
            VALUES ('A1001', '制作中', 0)
            """
        )


def get_existing_request(idempotency_key: str) -> dict | None:
    """从 SQLite 查这把幂等键以前是否出现过。"""
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            """
            SELECT state, response_json
            FROM idempotency_requests
            WHERE idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()

    if row is None:
        return None

    state, response_json = row
    if state == "completed":
        # response_json 的值是第一次完成时保存的 JSON 字符串，json.loads() 再还原成字典。
        return {"state": "completed", "response": json.loads(response_json)}
    return {"state": "processing"}


def reserve_idempotency_key(idempotency_key: str, order_id: str) -> bool:
    """尝试把一把新键登记为 processing；成功返回 True。"""
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.execute(
                """
                INSERT INTO idempotency_requests (idempotency_key, order_id, state, response_json)
                VALUES (?, ?, 'processing', NULL)
                """,
                (idempotency_key, order_id),
            )
        return True
    except sqlite3.IntegrityError:
        # 主键重复说明另一个请求已经登记了这把键。
        return False


@mcp.tool()
def cancel_order(order_id: str, idempotency_key: str) -> dict:
    """取消订单。相同幂等键在服务重启后重试也不会重复取消。"""
    existing_request = get_existing_request(idempotency_key)
    if existing_request is not None:
        if existing_request["state"] == "processing":
            return {
                "ok": False,
                "status": "processing",
                "idempotency_replayed": True,
                "message": "相同幂等键的取消请求仍在处理中。",
            }
        return {
            **existing_request["response"],
            "idempotency_replayed": True,
        }

    # 这里写入 SQLite 的新行是关键：服务进程重启了，idempotency.sqlite 里仍保留这把键。
    if not reserve_idempotency_key(idempotency_key, order_id):
        # 两个请求刚好同时进来时，未抢到 INSERT 主键的请求重新读取已有记录。
        existing_request = get_existing_request(idempotency_key)
        return {
            "ok": False,
            "status": existing_request["state"],
            "idempotency_replayed": True,
            "message": "相同幂等键已被另一个请求登记。",
        }

    # 模拟耗时的写操作。客户端即使 1 秒超时，SQLite 里的 processing 记录已先落盘。
    time.sleep(WRITE_DELAY_SECONDS)

    with sqlite3.connect(DATABASE_PATH) as connection:
        order = connection.execute(
            "SELECT status, cancelled_count FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()

        if order is None:
            response = {"ok": False, "error": "order_not_found", "message": "没有找到该订单。"}
        else:
            _, cancelled_count = order
            new_cancelled_count = cancelled_count + 1
            connection.execute(
                """
                UPDATE orders
                SET status = '已取消', cancelled_count = ?
                WHERE order_id = ?
                """,
                (new_cancelled_count, order_id),
            )
            response = {
                "ok": True,
                "order_id": order_id,
                "status": "已取消",
                "cancelled_count": new_cancelled_count,
            }

        connection.execute(
            """
            UPDATE idempotency_requests
            SET state = 'completed', response_json = ?
            WHERE idempotency_key = ?
            """,
            (json.dumps(response, ensure_ascii=False), idempotency_key),
        )

    return {
        **response,
        "idempotency_replayed": False,
    }


if __name__ == "__main__":
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    setup_database()
    print(f"SQLite 幂等 MCP 服务已启动：{MCP_URL}")
    print(f"数据库文件：{DATABASE_PATH}")
    mcp.run(transport="streamable-http")
