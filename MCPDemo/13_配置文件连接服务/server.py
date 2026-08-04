"""一个独立运行的 HTTP MCP 服务，供配置文件中的 URL 连接。"""

from mcp.server.fastmcp import FastMCP


HOST = "127.0.0.1"
PORT = 8017
MCP_URL = f"http://{HOST}:{PORT}/mcp"

mcp = FastMCP(
    "星光咖啡订单平台",
    host=HOST,
    port=PORT,
    instructions="提供订单状态查询工具。",
)

ORDERS = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天送达"},
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单状态。参数示例：order_id='A1001'。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "message": f"没有找到订单 {order_id}"}

    return {"found": True, "order_id": order_id, **order}


if __name__ == "__main__":
    print(f"订单 MCP 服务已启动：{MCP_URL}")
    mcp.run(transport="streamable-http")
