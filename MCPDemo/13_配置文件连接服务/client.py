"""从 mcp_servers.json 读取服务配置，再连接 MCP 服务。"""

import asyncio
import json
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
CONFIG_PATH = LESSON_DIR / "mcp_servers.json"
RESULT_PATH = LESSON_DIR / "输出" / "configured_mcp_result.json"


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
    # read_text() 读取文件，得到一整段字符串：
    # '{\n  "mcpServers": {\n    "coffee_order_remote": {...}\n  }\n}'。
    config_text = CONFIG_PATH.read_text(encoding="utf-8")

    # json.loads() 把 JSON 字符串变成 Python 字典。
    # config 的值大致是：{"mcpServers": {"coffee_order_remote": {"transport": "streamable_http", ...}}}。
    config = json.loads(config_text)

    # connections 的值就是：
    # {"coffee_order_remote": {"transport": "streamable_http", "url": "http://127.0.0.1:8017/mcp"}}
    connections = config["mcpServers"]
    client = MultiServerMCPClient(connections)

    try:
        tools = await client.get_tools()
    except Exception:
        print("连接配置中的 MCP 服务失败。请检查 server.py 是否正在运行，以及 JSON 里的 URL 是否正确。")
        return

    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    tool_result = await tools_by_name["get_order_status"].ainvoke({"order_id": "A1001"})
    result_text = readable_tool_result(tool_result)

    print(f"配置文件里的服务名称：{list(connections)}")
    print(f"通过配置拿到的工具：{list(tools_by_name)}")
    print(f"订单查询结果：{result_text}")

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "config_path": str(CONFIG_PATH),
                "configured_server_names": list(connections),
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
