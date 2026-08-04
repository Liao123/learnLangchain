"""MCP 服务端：公开两份可读取的客服规则资料。"""

import logging

from mcp.server.fastmcp import FastMCP


logging.getLogger("mcp").setLevel(logging.WARNING)
mcp = FastMCP("星光咖啡知识服务")


@mcp.resource(
    "coffee://knowledge/member-points",
    name="会员积分规则",
    description="星光咖啡会员积分获得规则。",
    mime_type="text/markdown",
)
def member_points_policy() -> str:
    """返回会员积分规则这一份固定资料。"""
    # 资源返回的是资料正文，不是“帮用户完成动作”的函数结果。
    return """# 会员积分规则

- 普通会员：每消费 1 元获得 1 积分。
- 金卡会员：每消费 1 元获得 1.5 积分。
- 积分将在订单完成后 24 小时内到账。
"""


@mcp.resource(
    "coffee://knowledge/refund-policy",
    name="退款规则",
    description="星光咖啡退款到账规则。",
    mime_type="text/markdown",
)
def refund_policy() -> str:
    """返回退款规则这一份固定资料。"""
    return """# 退款规则

- 退款申请提交后，状态会显示为“退款处理中”。
- 原路退款通常在 1 到 3 个工作日内到账。
- 实际到账时间受支付渠道处理速度影响。
"""


if __name__ == "__main__":
    # stdio 中不要 print 普通日志，避免破坏 MCP 协议通信。
    mcp.run(transport="stdio")
