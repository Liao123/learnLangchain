"""MCP 客户端：启动本地订单 MCP 服务，读取工具后直接调用。"""

import asyncio
import json
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
SERVER_PATH = LESSON_DIR / "server.py"
RESULT_PATH = LESSON_DIR / "输出" / "mcp_result.json"


async def main() -> None:
    # client 是 MCP 客户端。coffee_order 是客户端给这个服务端起的连接名称。
    # sys.executable 是当前 Python 的完整路径，确保子进程也能找到已安装的 mcp 包。
    client = MultiServerMCPClient(
        {
            "coffee_order": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
            }
        }
    )

    # 这一步会：启动 server.py 子进程 -> 按 MCP 协议连接 -> 读取服务端公开的工具。
    tools = await client.get_tools()

    tool_names = []
    for tool in tools:
        tool_names.append(tool.name)

    # 本课服务端只公开一个工具，所以 tools[0] 就是 get_order_status。
    # 它已经被适配成 LangChain Tool，可以直接使用 ainvoke() 调用。
    order_status_tool = tools[0]
    tool_result = await order_status_tool.ainvoke({"order_id": "A1001"})

    # MCP 适配器通常返回 ToolMessage；它的 content 可能是“内容块列表”。
    # 当前值大致是：[{"type": "text", "text": "{...订单 JSON...}", "id": "lc_..."}]。
    result_content = getattr(tool_result, "content", tool_result)
    if isinstance(result_content, list) and result_content:
        # 第一块是文本块，取出 text 后终端就直接显示订单 JSON，不显示协议包装。
        display_result = result_content[0]["text"]
    else:
        display_result = str(result_content)

    report = {
        "server_name": "coffee_order",
        "loaded_tool_names": tool_names,
        "call": {
            "tool_name": order_status_tool.name,
            "args": {"order_id": "A1001"},
            "result": display_result,
        },
    }
    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(report, result_file, ensure_ascii=False, indent=2)

    print(f"客户端拿到的工具：{tool_names}")
    print(f"调用 {order_status_tool.name} 后的结果：{display_result}")
    print(f"完整结果已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
