"""MCP 服务端：公开一套可复用的退款客服消息模板。"""

import logging

from mcp.server.fastmcp import FastMCP


logging.getLogger("mcp").setLevel(logging.WARNING)
mcp = FastMCP("星光咖啡客服话术服务")


@mcp.prompt(
    name="draft_refund_response",
    title="退款客服回复模板",
    description="根据订单号和退款原因生成一条交给客服模型处理的标准用户消息。",
)
def draft_refund_response(order_id: str, refund_reason: str) -> list[dict]:
    """把传入的订单号、退款原因填进标准处理话术。"""
    # 调用时传入：order_id="A1001", refund_reason="饮品洒漏"。
    # 返回的是一条“给模型看的用户消息”，不是最终给顾客的答案。
    return [
        {
            "role": "user",
            "content": f"""
请按星光咖啡退款客服规范处理这条请求。

订单号：{order_id}
退款原因：{refund_reason}

回复需要说明：已收到申请、退款通常在 1 到 3 个工作日内原路退回。
不要承诺具体到账时刻，也不要编造订单状态。
""".strip(),
        }
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")
