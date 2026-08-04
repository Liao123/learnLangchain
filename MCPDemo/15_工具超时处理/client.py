"""给 MCP 工具调用设置客户端等待上限。"""

import asyncio
import json
import os
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "tool_timeout_result.json"
MCP_URL = "http://127.0.0.1:8019/mcp"
TIMEOUT_ENV_NAME = "MCP_TOOL_TIMEOUT_SECONDS"


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
    # 默认值是 1.0，表示客户端最多等 1 秒。
    # 终端设置 MCP_TOOL_TIMEOUT_SECONDS=3 后，timeout_seconds 的值就是 3.0。
    timeout_seconds = float(os.getenv(TIMEOUT_ENV_NAME, "1"))

    client = MultiServerMCPClient(
        {
            "slow_order_service": {
                "transport": "streamable_http",
                "url": MCP_URL,
            }
        }
    )

    try:
        tools = await client.get_tools()
    except Exception:
        print("连接 MCP 服务失败：请检查 server.py 是否正在运行。")
        return

    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    try:
        # wait_for 的含义：调用已经开始，但超过 timeout_seconds 还没有结果就停止等待。
        # 默认这次是：工具要 2 秒，客户端只等 1 秒，因此会进入 except TimeoutError。
        tool_result = await asyncio.wait_for(
            tools_by_name["get_slow_order_status"].ainvoke({"order_id": "A1001"}),
            timeout=timeout_seconds,
        )
        result = {
            "outcome": "success",
            "result": readable_tool_result(tool_result),
        }
        print(f"工具在 {timeout_seconds} 秒内返回：{result['result']}")
    except TimeoutError:
        result = {
            "outcome": "timed_out",
            "message": f"等待 {timeout_seconds} 秒后仍未拿到工具结果。",
        }
        print(result["message"])

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "tool_name": "get_slow_order_status",
                "client_timeout_seconds": timeout_seconds,
                "result": result,
            },
            result_file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"完整结果已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
