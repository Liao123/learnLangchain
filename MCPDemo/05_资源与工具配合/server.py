"""一个 MCP 服务同时公开固定规则资源和实时订单查询工具。"""

import logging

from mcp.server.fastmcp import FastMCP


logging.getLogger("mcp").setLevel(logging.WARNING)
mcp = FastMCP("星光咖啡客服服务")


@mcp.resource(
    "coffee://knowledge/member-points",
    name="会员积分规则",
    description="会员等级和积分获得规则。",
    mime_type="text/markdown",
)
def member_points_policy() -> str:
    """返回固定规则资料。"""
    return """# 会员积分规则

- 普通会员：每消费 1 元获得 1 积分。
- 金卡会员：每消费 1 元获得 1.5 积分。
- 积分将在订单完成后 24 小时内到账。
"""


# 真实项目这里会查订单数据库，所以查询结果是随时间变化的“实时数据”。
ORDERS = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天送达"},
    "A1002": {"status": "已完成", "estimated_arrival": "已送达"},
}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """根据订单号查询实时订单状态。参数示例：order_id='A1001'。"""
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "message": f"没有找到订单 {order_id}"}

    return {"found": True, "order_id": order_id, **order}


if __name__ == "__main__":
    mcp.run(transport="stdio")
