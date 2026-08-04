"""连续调用三次取消工具，观察首次、重试和参数冲突的区别。"""

import asyncio
import json
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "idempotency_conflict_result.json"
MCP_URL = "http://127.0.0.1:8022/mcp"
IDEMPOTENCY_KEY = "cancel-request-001"


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
    client = MultiServerMCPClient(
        {
            "idempotency_conflict_service": {
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

    # 三次调用的 idempotency_key 都是 cancel-request-001。
    # 只有最后一次把 order_id 从 A1001 改成 A1002，用来制造参数冲突。
    test_calls = [
        {"label": "首次取消 A1001", "args": {"order_id": "A1001", "idempotency_key": IDEMPOTENCY_KEY}},
        {"label": "同键同参数重试 A1001", "args": {"order_id": "A1001", "idempotency_key": IDEMPOTENCY_KEY}},
        {"label": "同键但换成 A1002", "args": {"order_id": "A1002", "idempotency_key": IDEMPOTENCY_KEY}},
    ]

    results = []
    for test_call in test_calls:
        tool_result = await tools_by_name["cancel_order"].ainvoke(test_call["args"])
        result_text = readable_tool_result(tool_result)
        results.append({"label": test_call["label"], "args": test_call["args"], "result": result_text})
        print(f"\n{test_call['label']}")
        print(result_text)

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump({"idempotency_key": IDEMPOTENCY_KEY, "results": results}, result_file, ensure_ascii=False, indent=2)

    print(f"\n完整结果已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
