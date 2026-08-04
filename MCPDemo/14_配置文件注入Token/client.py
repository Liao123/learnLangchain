"""读取 MCP 配置文件，并用环境变量替换 Token 占位文字。"""

import asyncio
import json
import os
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


LESSON_DIR = Path(__file__).resolve().parent
CONFIG_PATH = LESSON_DIR / "mcp_servers.json"
RESULT_PATH = LESSON_DIR / "输出" / "configured_auth_result.json"
TOKEN_PLACEHOLDER = "${MCP_DEMO_TOKEN}"
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
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    connections = config["mcpServers"]

    # template 的值来自 JSON："Bearer ${MCP_DEMO_TOKEN}"。
    # token 的值来自当前终端环境变量："coffee-demo-token"。
    token = os.getenv(TOKEN_ENV_NAME)
    if not token:
        raise RuntimeError(f"没有找到环境变量 {TOKEN_ENV_NAME}。请按 lesson.md 先设置教学 Token。")

    template = connections["protected_order_service"]["headers"]["Authorization"]
    # replace 后，内存中的 Authorization 值变成 "Bearer coffee-demo-token"。
    # JSON 文件本身没有被修改，因此里面仍是 ${MCP_DEMO_TOKEN}，不会保存真实 Token。
    connections["protected_order_service"]["headers"]["Authorization"] = template.replace(TOKEN_PLACEHOLDER, token)

    client = MultiServerMCPClient(connections)
    try:
        tools = await client.get_tools()
    except Exception:
        print("连接受保护的 MCP 服务失败。请检查服务是否启动，以及环境变量 Token 是否正确。")
        return

    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    tool_result = await tools_by_name["get_order_status"].ainvoke({"order_id": "A1001"})
    result_text = readable_tool_result(tool_result)

    print(f"已用环境变量替换配置中的 {TOKEN_PLACEHOLDER}。")
    print(f"鉴权通过，拿到工具：{list(tools_by_name)}")
    print(f"订单查询结果：{result_text}")

    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(
            {
                "config_path": str(CONFIG_PATH),
                "authorization_template": template,
                "token_environment_variable": TOKEN_ENV_NAME,
                "loaded_tool_names": list(tools_by_name),
                "result": result_text,
            },
            result_file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"完整结果已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
