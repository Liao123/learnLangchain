"""客户端同时发送 Bearer Token 和 X-App-ID。"""

import asyncio
import json
import os
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "verified_client_result.json"
MCP_URL = "http://127.0.0.1:8014/mcp"
TOKEN_ENV_NAME = "MCP_DEMO_TOKEN"
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
    token = os.getenv(TOKEN_ENV_NAME)
    app_id = os.getenv(APP_ID_ENV_NAME)
    if not token or not app_id:
        raise RuntimeError(f"请同时设置 {TOKEN_ENV_NAME} 和 {APP_ID_ENV_NAME}。")

    # 这一次每次 HTTP MCP 请求都会同时带两项：
    # Authorization: Bearer customer-agent-token
    # X-App-ID: coffee-customer-agent
    client = MultiServerMCPClient(
        {
            "verified_order_service": {
                "transport": "streamable_http",
                "url": MCP_URL,
                "headers": {
                    "Authorization": f"Bearer {token}",
                    "X-App-ID": app_id,
                },
            }
        }
    )

    try:
        tools = await client.get_tools()
    except Exception:
        print("服务端拒绝请求。")
        print("请检查：服务端是否启动、Token 是否有效、App ID 是否与 Token 对应、Token 是否有 orders:read。")
        return

    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    tool_result = await tools_by_name["get_order_status"].ainvoke({"order_id": "A1001"})
    result_text = readable_tool_result(tool_result)

    print(f"Token、App ID、orders:read 都已验证，拿到的工具：{list(tools_by_name)}")
    print(f"订单查询结果：{result_text}")

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "mcp_url": MCP_URL,
                "token_environment_variable": TOKEN_ENV_NAME,
                "app_id": app_id,
                "required_scope": "orders:read",
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
