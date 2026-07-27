"""第 60 课：Agent 根据第一轮工具结果决定是否调用第二个工具。"""

import json
import os

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI


orders = {
    # A1001 的状态是制作中，所以 Agent 查完状态后，应该继续查取餐号。
    "A1001": {"商品": "冰拿铁", "状态": "制作中", "取餐号": "18"},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。输入订单号，例如 A1001。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False}, ensure_ascii=False)

    return json.dumps(
        {"found": True, "商品": order["商品"], "状态": order["状态"]},
        ensure_ascii=False,
    )


@tool
def get_pickup_number(order_id: str) -> str:
    """查询制作中订单的取餐号。输入订单号，例如 A1001。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False}, ensure_ascii=False)

    return json.dumps(
        {"found": True, "取餐号": order["取餐号"]},
        ensure_ascii=False,
    )


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status, get_pickup_number]
tools_by_name = {tool.name: tool for tool in tools}

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
).bind_tools(tools)

question = "订单 A1001 现在什么状态？如果正在制作，请告诉我取餐号。"
messages = [
    SystemMessage(
        content="""
你是订单 Agent。
先调用 get_order_status 查询订单状态。
只有收到“状态是制作中”的工具结果后，才调用 get_pickup_number。
拿到需要的工具结果后，用简短中文回答用户。
"""
    ),
    HumanMessage(content=question),
]

# 最多 3 轮，防止 Agent 因模型异常无限调用工具。
MAX_ROUNDS = 3

for round_number in range(1, MAX_ROUNDS + 1):
    response = model.invoke(messages)
    messages.append(response)

    # Agent 不再请求工具时，content 才是最后给用户的答复。
    if not response.tool_calls:
        print("\nAgent 最终答复：")
        print(response.content)
        break

    for tool_call in response.tool_calls:
        print(f"第 {round_number} 轮：Agent 请求 {tool_call['name']}")
        print("工具参数：", tool_call["args"])

        selected_tool = tools_by_name.get(tool_call["name"])
        if selected_tool is None:
            tool_result = "这个工具没有登记，不能执行。"
        else:
            tool_result = selected_tool.invoke(tool_call["args"])

        print("工具结果：", tool_result)
        messages.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"],
            )
        )
else:
    print("Agent 超过 3 轮仍未完成，本次停止。")
