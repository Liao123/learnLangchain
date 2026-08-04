"""拒绝“同一幂等键、不同订单参数”的 MCP 写操作。"""

import json
import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8022
MCP_URL = f"http://{HOST}:{PORT}/mcp"
DATABASE_PATH = Path(__file__).resolve().parent / "输出" / "idempotency_conflict.sqlite"

mcp = FastMCP("星光咖啡幂等冲突服务", host=HOST, port=PORT)


def setup_database() -> None:
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
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL
            )
            """
        )
        connection.execute("INSERT OR IGNORE INTO orders VALUES ('A1001', '制作中', 0)")
        connection.execute("INSERT OR IGNORE INTO orders VALUES ('A1002', '制作中', 0)")


@mcp.tool()
def cancel_order(order_id: str, idempotency_key: str) -> dict:
    """取消订单。同一幂等键只能搭配第一次使用时的 order_id。"""
    # 本次请求的业务参数被固定成 JSON 文字。A1001 时：'{"order_id": "A1001"}'。
    request_json = json.dumps({"order_id": order_id}, ensure_ascii=False, sort_keys=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
        existing_row = connection.execute(
            """
            SELECT request_json, response_json
            FROM idempotency_requests
            WHERE idempotency_key = ?
            """,
            (idempotency_key,),
        ).fetchone()

        if existing_row is not None:
            saved_request_json, saved_response_json = existing_row
            if saved_request_json != request_json:
                # 例如保存的是 {"order_id": "A1001"}，新请求却是 {"order_id": "A1002"}。
                # 服务端拒绝，既不泄漏旧结果，也不取消新订单。
                return {
                    "ok": False,
                    "error": "idempotency_key_conflict",
                    "message": "该幂等键已经用于另一组请求参数，不能复用。",
                }

            # 键和参数都相同：这是安全的重试，直接复用第一次结果。
            return {
                **json.loads(saved_response_json),
                "idempotency_replayed": True,
            }

        order = connection.execute(
            "SELECT cancelled_count FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if order is None:
            response = {"ok": False, "error": "order_not_found"}
        else:
            new_cancelled_count = order[0] + 1
            connection.execute(
                "UPDATE orders SET status = '已取消', cancelled_count = ? WHERE order_id = ?",
                (new_cancelled_count, order_id),
            )
            response = {
                "ok": True,
                "order_id": order_id,
                "status": "已取消",
                "cancelled_count": new_cancelled_count,
            }

        # 第一次请求的参数和结果一起保存，之后同键请求都要和 request_json 对比。
        connection.execute(
            """
            INSERT INTO idempotency_requests (idempotency_key, request_json, response_json)
            VALUES (?, ?, ?)
            """,
            (idempotency_key, request_json, json.dumps(response, ensure_ascii=False)),
        )

    return {
        **response,
        "idempotency_replayed": False,
    }


if __name__ == "__main__":
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    setup_database()
    print(f"幂等键参数冲突 MCP 服务已启动：{MCP_URL}")
    mcp.run(transport="streamable-http")
