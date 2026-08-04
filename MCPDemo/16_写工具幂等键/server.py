"""写操作 MCP 工具：用幂等键避免超时重试导致重复取消。"""

import threading
import time

from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8020
MCP_URL = f"http://{HOST}:{PORT}/mcp"
WRITE_DELAY_SECONDS = 2

mcp = FastMCP("星光咖啡取消订单服务", host=HOST, port=PORT)

# cancelled_count 用来观察“真正取消了几次”。正常情况下它最多从 0 变成 1。
ORDERS = {
    "A1001": {
        "status": "制作中",
        "cancelled_count": 0,
    }
}

# 每个幂等键只对应一次写操作记录。
# 例如第一次收到 cancel-A1001-001 后，值先是 {"state": "processing"}；完成后变为 completed + response。
IDEMPOTENCY_RECORDS = {}
RECORD_LOCK = threading.Lock()


@mcp.tool()
def cancel_order(order_id: str, idempotency_key: str) -> dict:
    """取消订单。相同 idempotency_key 重试时，不会重复执行取消。"""
    # 先在共享字典中登记这把幂等键。Lock 防止两个请求同时看到“还没有该键”。
    with RECORD_LOCK:
        existing_record = IDEMPOTENCY_RECORDS.get(idempotency_key)
        if existing_record is not None:
            if existing_record["state"] == "processing":
                return {
                    "ok": False,
                    "status": "processing",
                    "idempotency_replayed": True,
                    "message": "相同幂等键的取消请求仍在处理中，请稍后用同一个键查询。",
                }

            # 已经完成时直接返回第一次保存的结果，不再改订单状态或增加 cancelled_count。
            return {
                **existing_record["response"],
                "idempotency_replayed": True,
            }

        IDEMPOTENCY_RECORDS[idempotency_key] = {"state": "processing"}

    # 模拟取消订单要请求慢业务系统。即使客户端 1 秒就超时，这个服务端工作仍可能继续完成。
    time.sleep(WRITE_DELAY_SECONDS)

    order = ORDERS.get(order_id)
    if order is None:
        response = {"ok": False, "error": "order_not_found", "message": "没有找到该订单。"}
    else:
        # 真正产生副作用的代码只有第一次拿到这把幂等键时才会到达。
        order["status"] = "已取消"
        order["cancelled_count"] += 1
        response = {
            "ok": True,
            "order_id": order_id,
            "status": order["status"],
            "cancelled_count": order["cancelled_count"],
        }

    with RECORD_LOCK:
        IDEMPOTENCY_RECORDS[idempotency_key] = {
            "state": "completed",
            "response": response,
        }

    return {
        **response,
        "idempotency_replayed": False,
    }


if __name__ == "__main__":
    print(f"带幂等键的取消订单 MCP 服务已启动：{MCP_URL}")
    print(f"每次首次取消固定耗时 {WRITE_DELAY_SECONDS} 秒。")
    mcp.run(transport="streamable-http")
