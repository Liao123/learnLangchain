"""订单 MCP 服务：它只知道订单数据，只公开订单工具。"""

import logging

from mcp.server.fastmcp import FastMCP


logging.getLogger("mcp").setLevel(logging.WARNING)
mcp = FastMCP("星光咖啡订单服务")

# 订单服务自己的数据。会员服务文件不能直接读取这个字典。
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

    # A1001 的返回值大致是：{"found": True, "order_id": "A1001", "status": "配送中", ...}
    return {"found": True, "order_id": order_id, **order}


if __name__ == "__main__":
    mcp.run(transport="stdio")
