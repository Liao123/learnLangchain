"""故意较慢的 HTTP MCP 工具，用于观察客户端超时行为。"""

import asyncio

from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8019
MCP_URL = f"http://{HOST}:{PORT}/mcp"
SERVICE_DELAY_SECONDS = 2

mcp = FastMCP("星光咖啡慢订单服务", host=HOST, port=PORT)


@mcp.tool()
async def get_slow_order_status(order_id: str) -> dict:
    """模拟需要 2 秒才能返回的订单查询。"""
    # 真实情况可能是数据库慢、第三方支付平台慢、网络慢。
    # 本课固定等 2 秒，保证可以稳定测试客户端的 1 秒超时。
    await asyncio.sleep(SERVICE_DELAY_SECONDS)

    if order_id != "A1001":
        return {"found": False, "message": "没有找到该订单。"}
    return {
        "found": True,
        "order_id": "A1001",
        "status": "配送中",
        "estimated_arrival": "今天送达",
    }


if __name__ == "__main__":
    print(f"慢 MCP 服务已启动：{MCP_URL}")
    print(f"get_slow_order_status 每次固定等待 {SERVICE_DELAY_SECONDS} 秒。")
    mcp.run(transport="streamable-http")
