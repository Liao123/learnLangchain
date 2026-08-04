"""用同一幂等键重试取消订单，观察 SQLite 中保存的结果。"""

import asyncio
import json
import os
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "sqlite_idempotency_result.json"
MCP_URL = "http://127.0.0.1:8021/mcp"
TIMEOUT_ENV_NAME = "MCP_TOOL_TIMEOUT_SECONDS"
KEY_ENV_NAME = "MCP_IDEMPOTENCY_KEY"
DEFAULT_IDEMPOTENCY_KEY = "cancel-A1001-001"


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
    timeout_seconds = float(os.getenv(TIMEOUT_ENV_NAME, "1"))
    idempotency_key = os.getenv(KEY_ENV_NAME, DEFAULT_IDEMPOTENCY_KEY)

    client = MultiServerMCPClient(
        {
            "sqlite_cancel_service": {
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

    args = {"order_id": "A1001", "idempotency_key": idempotency_key}
    print(f"本次取消使用的幂等键：{idempotency_key}")

    try:
        tool_result = await asyncio.wait_for(
            tools_by_name["cancel_order"].ainvoke(args),
            timeout=timeout_seconds,
        )
        result = {"outcome": "response_received", "tool_result": readable_tool_result(tool_result)}
        print(f"工具返回：{result['tool_result']}")
    except TimeoutError:
        result = {
            "outcome": "client_timed_out",
            "message": f"客户端等待 {timeout_seconds} 秒后超时；SQLite 仍会保留这把幂等键。",
        }
        print(result["message"])

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "args": args,
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
