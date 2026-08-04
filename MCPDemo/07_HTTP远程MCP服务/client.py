"""通过 HTTP URL 连接独立 MCP 服务，而不是启动本地子进程。"""

import asyncio
import json
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "http_mcp_result.json"
MCP_URL = "http://127.0.0.1:8011/mcp"


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
    # 和以前 stdio 配置的区别在这里：
    # 没有 command、args；只有第三方 MCP 服务提供的网络地址 MCP_URL。
    client = MultiServerMCPClient(
        {
            "remote_order_service": {
                "transport": "streamable_http",
                "url": MCP_URL,
            }
        }
    )

    # 客户端发 HTTP 请求到 http://127.0.0.1:8011/mcp，读取服务公开的工具。
    tools = await client.get_tools()
    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    print(f"通过 HTTP 拿到的工具：{list(tools_by_name)}")

    # 本课先由 Python 指定调用，参数值就是 {"order_id": "A1001"}。
    tool_result = await tools_by_name["get_order_status"].ainvoke({"order_id": "A1001"})
    result_text = readable_tool_result(tool_result)
    print(f"HTTP 工具返回：{result_text}")

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "mcp_url": MCP_URL,
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
