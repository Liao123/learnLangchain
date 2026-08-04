"""会员 MCP 服务：它只知道会员数据，只公开会员工具。"""

import logging

from mcp.server.fastmcp import FastMCP


logging.getLogger("mcp").setLevel(logging.WARNING)
mcp = FastMCP("星光咖啡会员服务")

# 这是另一份服务自己的数据，和 order_server.py 中的 ORDERS 分开。
MEMBERS = {
    "M1001": {"level": "金卡会员", "points": 1280},
    "M1002": {"level": "普通会员", "points": 320},
}


@mcp.tool()
def get_member_points(member_id: str) -> dict:
    """根据会员号查询会员等级和当前积分。参数示例：member_id='M1001'。"""
    member = MEMBERS.get(member_id)
    if member is None:
        return {"found": False, "message": f"没有找到会员 {member_id}"}

    # M1001 的返回值大致是：{"found": True, "member_id": "M1001", "level": "金卡会员", "points": 1280}
    return {"found": True, "member_id": member_id, **member}


if __name__ == "__main__":
    mcp.run(transport="stdio")
