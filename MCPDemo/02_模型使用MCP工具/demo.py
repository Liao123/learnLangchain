"""MCP 客户端：让模型从独立 MCP 服务拿工具，再自己选择调用哪个工具。"""

import asyncio
import json
import os
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI


LESSON_DIR = Path(__file__).resolve().parent
SERVER_PATH = LESSON_DIR / "server.py"
RESULT_PATH = LESSON_DIR / "输出" / "agent_mcp_result.json"
MAX_ROUNDS = 3


def readable_tool_result(tool_result: object) -> str:
    """把 MCP 工具的返回内容变成模型和终端都容易阅读的文字。"""
    # tool_result 常是 ToolMessage；它的 content 可能是列表：
    # [{"type": "text", "text": "{\"found\": true, ...}"}]。
    result_content = getattr(tool_result, "content", tool_result)

    if isinstance(result_content, list):
        text_parts = []
        for block in result_content:
            if isinstance(block, dict) and "text" in block:
                text_parts.append(str(block["text"]))
            else:
                text_parts.append(str(block))
        return "\n".join(text_parts)

    return str(result_content)


async def main() -> None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("没有找到 DEEPSEEK_API_KEY，请先在终端或 PyCharm 运行配置中设置它。")

    # 1. 先连接 MCP 服务。sys.executable 是当前 Python 的完整路径，
    #    所以客户端启动 server.py 子进程时，也会使用装有 mcp 包的同一个 Python。
    client = MultiServerMCPClient(
        {
            "coffee_service": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
            }
        }
    )
    tools = await client.get_tools()

    # tools 的值大致是：[StructuredTool(name="get_order_status"), StructuredTool(name="get_refund_status")]。
    # 字典便于后面通过模型给出的名字快速取工具，例如 tools_by_name["get_order_status"]。
    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool

    print(f"MCP 服务提供的工具：{list(tools_by_name)}")

    # 2. bind_tools 只是把“可用工具说明书”交给模型，并没有真的执行工具。
    #    模型随后可能返回 tool_calls，例如：[{"name": "get_order_status", "args": {"order_id": "A1001"}}]。
    model = ChatOpenAI(
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
        api_key=api_key,
    )
    model_with_tools = model.bind_tools(tools)

    question = input("请输入订单或退款问题：").strip()
    if not question:
        raise ValueError("问题不能为空。")

    # messages 第一次的值只有两条：系统规则 + 用户问题。
    # 后面每轮会继续追加“模型的工具请求”和“工具查询结果”。
    messages = [
        SystemMessage(
            content=(
                "你是星光咖啡客服。只能回答订单或退款状态。"
                "需要查询订单时必须调用 get_order_status；"
                "需要查询退款时必须调用 get_refund_status。"
                "必须根据工具实际返回的结果回答，不能编造。"
            )
        ),
        HumanMessage(content=question),
    ]
    call_records = []
    final_answer = "模型没有在限定轮次内给出最终回答。"

    # 3. 这就是已经学过的 Agent 工具循环：模型请求工具 -> Python 执行工具 -> 结果塞回 messages。
    for round_number in range(1, MAX_ROUNDS + 1):
        response = await model_with_tools.ainvoke(messages)
        messages.append(response)

        # 没有 tool_calls 时，说明模型这次已经是在说最终答案，可以结束循环。
        if not response.tool_calls:
            final_answer = str(response.content)
            print(f"第 {round_number} 轮：模型直接给出最终回答。")
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"第 {round_number} 轮：模型请求调用 {tool_name}，参数是 {tool_args}")

            selected_tool = tools_by_name.get(tool_name)
            if selected_tool is None:
                # 正常不该发生；保留这个分支，是为了模型写错工具名时仍能得到一条明确反馈。
                tool_text = f"工具 {tool_name} 不在 MCP 服务提供的工具列表中。"
            else:
                # 真正的 MCP 调用在这一行。它会把参数发给独立的 server.py 进程。
                tool_result = await selected_tool.ainvoke(tool_args)
                tool_text = readable_tool_result(tool_result)

            print(f"工具返回：{tool_text}")
            call_records.append(
                {
                    "round": round_number,
                    "tool_name": tool_name,
                    "args": tool_args,
                    "result": tool_text,
                }
            )

            # 把工具结果写成一条 ToolMessage，绑定本次 tool_call 的 id。
            # 下一轮模型看见这条消息，才知道刚才查询得到的是“配送中”或“退款处理中”。
            messages.append(ToolMessage(content=tool_text, tool_call_id=tool_call["id"]))

    report = {
        "question": question,
        "mcp_tool_names": list(tools_by_name),
        "tool_calls": call_records,
        "final_answer": final_answer,
    }
    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(report, result_file, ensure_ascii=False, indent=2)

    print(f"\n最终回答：{final_answer}")
    print(f"完整过程已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
