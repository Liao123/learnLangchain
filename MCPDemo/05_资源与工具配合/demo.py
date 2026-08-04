"""先读取 MCP 规则资源，再让模型按需调用 MCP 订单工具。"""

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
RESULT_PATH = LESSON_DIR / "输出" / "resource_and_tool_result.json"
POLICY_URI = "coffee://knowledge/member-points"
MAX_ROUNDS = 3


def readable_tool_result(tool_result: object) -> str:
    """把 MCP 工具结果转换为可放进 ToolMessage 的字符串。"""
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

    client = MultiServerMCPClient(
        {
            "coffee_service": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
            }
        }
    )

    # 1. Python 主动读取固定资源。它不是模型工具，模型不会自行调用它。
    # resources 的值只有一个 Blob，metadata["uri"] 是 coffee://knowledge/member-points。
    resources = await client.get_resources(
        server_name="coffee_service",
        uris=POLICY_URI,
    )
    policy_resource = resources[0]
    policy_text = policy_resource.as_string()
    print(f"已加载回答资料：{policy_resource.metadata['uri']}")

    # 2. 订单状态是实时数据，所以作为可被模型选择的 MCP 工具。
    tools = await client.get_tools(server_name="coffee_service")
    tools_by_name = {}
    for tool in tools:
        tools_by_name[tool.name] = tool
    print(f"模型可调用的实时工具：{list(tools_by_name)}")

    model = ChatOpenAI(
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
        api_key=api_key,
    )
    model_with_tools = model.bind_tools(tools)

    question = input("请输入会员积分或订单问题：").strip()
    if not question:
        raise ValueError("问题不能为空。")

    # messages 第一次的真实结构是：
    # [SystemMessage(规则 + 会员资料), HumanMessage(用户问题)]。
    # 所以问“金卡每消费 1 元几积分”时，模型可直接从 policy_text 回答，无需查工具。
    messages = [
        SystemMessage(
            content=f"""
你是星光咖啡客服。
会员积分问题只能根据 <会员积分规则> 回答。
订单状态问题必须调用 get_order_status 查询实时结果。
不能编造资料或订单状态。

<会员积分规则>
{policy_text}
</会员积分规则>
"""
        ),
        HumanMessage(content=question),
    ]

    call_records = []
    final_answer = "模型没有在限定轮次内给出最终回答。"

    # 3. 只有模型真的请求 get_order_status 时，才会进入这一段工具循环。
    for round_number in range(1, MAX_ROUNDS + 1):
        response = await model_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            final_answer = str(response.content)
            print(f"第 {round_number} 轮：模型根据已加载资料直接回答。")
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"第 {round_number} 轮：模型请求实时工具 {tool_name}，参数是 {tool_args}")

            selected_tool = tools_by_name.get(tool_name)
            if selected_tool is None:
                tool_text = f"工具 {tool_name} 不存在。"
            else:
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
            messages.append(ToolMessage(content=tool_text, tool_call_id=tool_call["id"]))

    report = {
        "question": question,
        "loaded_resource": {
            "uri": str(policy_resource.metadata["uri"]),
            "content": policy_text,
        },
        "tool_calls": call_records,
        "final_answer": final_answer,
    }
    with RESULT_PATH.open("w", encoding="utf-8") as result_file:
        json.dump(report, result_file, ensure_ascii=False, indent=2)

    print(f"\n最终回答：{final_answer}")
    print(f"完整过程已写入：{RESULT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
