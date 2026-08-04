"""MCP 服务端：向外部 Agent 公开订单和退款查询工具。"""

import logging

from mcp.server.fastmcp import FastMCP


# MCP 在 stdio 通信时会产生很多协议日志。本课只展示我们关心的业务结果。
logging.getLogger("mcp").setLevel(logging.WARNING)

# mcp 是这个独立服务进程的入口，不是 demo.py 里的模型。
mcp = FastMCP("星光咖啡客服服务")

# 真实项目会查数据库；本课先用两份字典模拟两张业务表。
# 例如：ORDERS["A1001"] 的值是 {"status": "配送中", "estimated_arrival": "今天送达"}。
ORDERS = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天送达"},
    "A1002": {"status": "已完成", "estimated_arrival": "已送达"},
}
REFUNDS = {
    "R2001": {"status": "退款处理中", "estimated_arrival": "1 到 3 个工作日内原路退回"},
    "R2002": {"status": "退款完成", "estimated_arrival": "已原路退回"},
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询订单配送状态。参数示例：order_id='A1001'。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "message": f"没有找到订单 {order_id}"}

    # 返回值示例：{"found": True, "order_id": "A1001", "status": "配送中", ...}
    return {"found": True, "order_id": order_id, **order}


@mcp.tool()
def get_refund_status(refund_id: str) -> dict:
    """根据退款单号查询退款进度。参数示例：refund_id='R2001'。"""
    refund = REFUNDS.get(refund_id)
    if refund is None:
        return {"found": False, "message": f"没有找到退款单 {refund_id}"}

    # 返回值示例：{"found": True, "refund_id": "R2001", "status": "退款处理中", ...}
    return {"found": True, "refund_id": refund_id, **refund}


if __name__ == "__main__":
    # stdio 表示服务端通过标准输入/输出与 demo.py 通信，不开 HTTP 端口。
    # 因此这里不要用 print() 打印普通日志，否则会干扰 MCP 协议消息。
    mcp.run(transport="stdio")
