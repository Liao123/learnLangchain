"""MCP 服务端：向外部客户端公开一个订单查询工具。"""

import logging

from mcp.server.fastmcp import FastMCP


# 本课只展示业务结果，隐藏 MCP 库的 ListToolsRequest 等 INFO 协议日志。
logging.getLogger("mcp").setLevel(logging.WARNING)

# mcp 是服务端对象。名字会在 MCP 连接建立时告诉客户端。
mcp = FastMCP("星光咖啡订单服务")

# 这是服务端自己的假订单数据。客户端拿不到这个字典，只能调用公开的工具。
ORDERS = {
    "A1001": {
        "status": "配送中",
        "estimated_arrival": "今天送达",
    },
    "A1002": {
        "status": "已完成",
        "estimated_arrival": "已送达",
    },
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单状态。参数示例：order_id='A1001'。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {
            "found": False,
            "message": f"没有找到订单 {order_id}",
        }

    # 返回值示例：
    # {"found": True, "order_id": "A1001", "status": "配送中", "estimated_arrival": "今天送达"}
    return {
        "found": True,
        "order_id": order_id,
        **order,
    }


if __name__ == "__main__":
    # stdio 表示服务端不开放 HTTP 端口，而是通过标准输入/输出和客户端进程通信。
    # 因此这里不要 print 业务日志，否则会干扰 MCP 协议消息。
    mcp.run(transport="stdio")
