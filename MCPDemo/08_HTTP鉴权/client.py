"""带 Authorization 请求头连接受保护的 HTTP MCP 服务。"""

import asyncio
import json
import os
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "authenticated_mcp_result.json"
MCP_URL = "http://127.0.0.1:8012/mcp"
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
        raise RuntimeError(f"没有找到环境变量 {TOKEN_ENV_NAME}。请按 lesson.md 的命令先设置教学 Token。")

    # headers 会附加到每次 HTTP MCP 请求。
    # 这里实际发送的是：Authorization: Bearer coffee-demo-token。
    # 注意：代码只使用 token，不 print 它，也不把它写入 JSON 文件。
    client = MultiServerMCPClient(
        {
            "protected_order_service": {
                "transport": "streamable_http",
                "url": MCP_URL,
                "headers": {"Authorization": f"Bearer {token}"},
            }
        }
    )

    # 如果 Token 缺失、错误或权限不足，服务端会在这一步拒绝连接。
    # 这里把底层 HTTP 异常换成便于学习时判断的提示，不打印一大段库内部调用栈。
    try:
        tools = await client.get_tools()
    except Exception:
        print("连接受保护的 MCP 服务失败。")
        print("请检查：服务端是否正在运行、MCP_DEMO_TOKEN 是否是 coffee-demo-token、Token 是否有 orders:read 权限。")
        return
    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    tool_result = await tools_by_name["get_order_status"].ainvoke({"order_id": "A1001"})
    result_text = readable_tool_result(tool_result)

    print(f"鉴权通过，拿到的工具：{list(tools_by_name)}")
    print(f"订单查询结果：{result_text}")

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "mcp_url": MCP_URL,
                "authenticated": True,
                "token_environment_variable": TOKEN_ENV_NAME,
                "loaded_tool_names": list(tools_by_name),
                "call": {
                    "tool_name": "get_order_status",
                    "args": {"order_id": "A1001"},
                    "result": result_text,
                },
            },
            result_file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"完整结果已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
