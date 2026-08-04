"""调用带审计能力的 MCP 订单工具。"""

import asyncio
import os

from langchain_mcp_adapters.client import MultiServerMCPClient


MCP_URL = "http://127.0.0.1:8016/mcp"
TOKEN_ENV_NAME = "MCP_DEMO_TOKEN"


def readable_tool_result(tool_result: object) -> str:
    """把 MCP 工具返回的内容块列表转成普通文字。"""
    result_content = getattr(tool_result, "content", tool_result)
    if not isinstance(result_content, list):
        return str(result_content)

    text_parts = []
    for block in result_content:
        if isinstance(block, dict) and "text" in block:
            text_parts.append(str(block["text"]))
        else:
            text_parts.append(str(block))
    return "\n".join(text_parts)


async def main() -> None:
    token = os.getenv(TOKEN_ENV_NAME)
    if not token:
        raise RuntimeError(f"没有找到环境变量 {TOKEN_ENV_NAME}。请按 lesson.md 先设置教学 Token。")

    client = MultiServerMCPClient(
        {
            "audited_order_service": {
                "transport": "streamable_http",
                "url": MCP_URL,
                "headers": {"Authorization": f"Bearer {token}"},
            }
        }
    )

    try:
        tools = await client.get_tools()
    except Exception:
        print("连接 MCP 服务失败：请检查服务是否启动，以及 Token 是否有效。")
        return

    order_id = input("请输入要查询的订单号：").strip()
    if not order_id:
        raise ValueError("订单号不能为空。")

    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    tool_result = await tools_by_name["get_order_status"].ainvoke({"order_id": order_id})
    print(f"工具返回：{readable_tool_result(tool_result)}")
    print("本次工具调用已由服务端写入 输出/audit_log.jsonl。")


if __name__ == "__main__":
    asyncio.run(main())
