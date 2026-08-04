"""客户端通过 headers 发送 X-App-ID，自定义中间件决定是否放行。"""

import asyncio
import json
import os
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "custom_header_result.json"
MCP_URL = "http://127.0.0.1:8013/mcp"
APP_ID_ENV_NAME = "MCP_DEMO_APP_ID"


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
    app_id = os.getenv(APP_ID_ENV_NAME)
    if not app_id:
        raise RuntimeError(f"没有找到环境变量 {APP_ID_ENV_NAME}。请按 lesson.md 先设置教学 App ID。")

    # 这一次发送的是自定义头，不是标准 Bearer 鉴权头。
    # HTTP 请求会带：X-App-ID: coffee-customer-agent。
    client = MultiServerMCPClient(
        {
            "app_id_protected_service": {
                "transport": "streamable_http",
                "url": MCP_URL,
                "headers": {"X-App-ID": app_id},
            }
        }
    )

    # 服务端中间件在 get_tools() 前就会检查 X-App-ID。
    try:
        tools = await client.get_tools()
    except Exception:
        print("服务端拒绝了这个 App ID。")
        print("请检查：服务端是否启动、MCP_DEMO_APP_ID 是否是 coffee-customer-agent。")
        return

    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    tool_result = await tools_by_name["get_order_status"].ainvoke({"order_id": "A1001"})
    result_text = readable_tool_result(tool_result)

    print(f"App ID 已通过服务端检查，拿到的工具：{list(tools_by_name)}")
    print(f"订单查询结果：{result_text}")

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "mcp_url": MCP_URL,
                "app_id": app_id,
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
