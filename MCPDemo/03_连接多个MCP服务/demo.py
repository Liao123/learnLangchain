"""一个 Agent 同时使用订单服务和会员服务提供的 MCP 工具。"""

import asyncio
import json
import os
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI


LESSON_DIR = Path(__file__).resolve().parent
RESULT_PATH = LESSON_DIR / "输出" / "multi_server_result.json"
MAX_ROUNDS = 3

# 这张表只用于终端展示“模型选中的工具来自哪个服务”。
# 例如：模型请求 get_member_points 时，会显示“来自 member_service”。
TOOL_SOURCE = {
    "get_order_status": "order_service",
    "get_member_points": "member_service",
}


def readable_tool_result(tool_result: object) -> str:
    """把 MCP 返回的内容块列表变成工具结果文字。"""
    # tool_result 的实际值可能是：
    # [{"type": "text", "text": "{\"found\": true, ...}", "id": "lc_..."}]。
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
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY，请先在终端或 PyCharm 运行配置中设置它。")

    # 本课新增的核心：一个 MultiServerMCPClient 配置了两个服务。
    # 它会分别启动：
    # 1. order_server.py 进程，拿到 get_order_status；
    # 2. member_server.py 进程，拿到 get_member_points。
    client = MultiServerMCPClient(
        {
            "order_service": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(LESSON_DIR / "order_server.py")],
            },
            "member_service": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(LESSON_DIR / "member_server.py")],
            },
        }
    )

    # tools 的值大致是两个工具对象：
    # [StructuredTool(name="get_order_status"), StructuredTool(name="get_member_points")]
    tools = await client.get_tools()
    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    print(f"两个 MCP 服务提供的工具：{list(tools_by_name)}")

    model = ChatOpenAI(
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
        api_key=api_key,
    )
    # 模型不会区分工具代码在哪个 Python 文件；它只会看到两份工具说明书。
    model_with_tools = model.bind_tools(tools)

    question = input("请输入订单或会员问题：").strip()
    if not question:
        raise ValueError("问题不能为空。")

    messages = [
        SystemMessage(
            content=(
                "你是星光咖啡客服。查询订单必须调用 get_order_status；"
                "查询会员等级或积分必须调用 get_member_points。"
                "只能根据工具返回的数据回答，不能编造。"
            )
        ),
        HumanMessage(content=question),
    ]
    call_records = []
    final_answer = "模型没有在限定轮次内给出最终回答。"

    # 和上一课完全相同的 Agent 循环：模型选工具，Python 执行，再把结果交回模型。
    for round_number in range(1, MAX_ROUNDS + 1):
        response = await model_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            final_answer = str(response.content)
            print(f"第 {round_number} 轮：模型直接给出最终回答。")
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            source = TOOL_SOURCE.get(tool_name, "未知服务")
            print(f"第 {round_number} 轮：模型请求 {tool_name}，来自 {source}，参数是 {tool_args}")

            selected_tool = tools_by_name.get(tool_name)
            if selected_tool is None:
                tool_text = f"工具 {tool_name} 不在两个 MCP 服务提供的工具列表中。"
            else:
                # 这一行会实际请求对应的 MCP 服务，不是调用 demo.py 内的本地函数。
                tool_result = await selected_tool.ainvoke(tool_args)
                tool_text = readable_tool_result(tool_result)

            print(f"工具返回：{tool_text}")
            call_records.append(
                {
                    "round": round_number,
                    "tool_name": tool_name,
                    "source_server": source,
                    "args": tool_args,
                    "result": tool_text,
                }
            )
            messages.append(ToolMessage(content=tool_text, tool_call_id=tool_call["id"]))

    report = {
        "question": question,
        "loaded_tools": list(tools_by_name),
        "tool_calls": call_records,
        "final_answer": final_answer,
    }
    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(report, result_file, ensure_ascii=False, indent=2)

    print(f"\n最终回答：{final_answer}")
    print(f"完整过程已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
