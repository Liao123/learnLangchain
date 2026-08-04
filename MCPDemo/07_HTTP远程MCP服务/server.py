"""独立运行的 HTTP MCP 服务，模拟第三方订单系统。"""

from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8011
MCP_URL = f"http://{HOST}:{PORT}/mcp"

# 这次服务不使用 stdio，而是自己监听 HTTP 地址。
mcp = FastMCP("星光咖啡远程订单服务", host=HOST, port=PORT)

ORDERS = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天送达"},
    "A1002": {"status": "已完成", "estimated_arrival": "已送达"},
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单状态。参数示例：order_id='A1001'。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "message": f"没有找到订单 {order_id}"}

    return {"found": True, "order_id": order_id, **order}


if __name__ == "__main__":
    # 这一句能正常 print，因为 HTTP 服务不是用标准输出传递 MCP 协议。
    print(f"HTTP MCP 服务已启动：{MCP_URL}")
    print("请保持这个终端运行，再在另一个终端启动 client.py。")
    mcp.run(transport="streamable-http")
