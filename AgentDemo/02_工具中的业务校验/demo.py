"""第 61 课：模型可以请求操作，但工具代码决定操作是否真正执行。"""

import json
import os

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI


# 这是假订单库。A1001 已经制作中，业务上不允许取消。
orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中", "取餐号": "18"},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。输入订单号，例如 A1001。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False, "原因": "订单不存在"}, ensure_ascii=False)

    # 这次实际返回：{"found": true, "状态": "制作中"}
    return json.dumps(
        {"found": True, "商品": order["商品"], "状态": order["状态"]},
        ensure_ascii=False,
    )


@tool
def cancel_order(order_id: str) -> str:
    """取消订单。只允许取消状态为“待制作”的订单。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"success": False, "原因": "订单不存在"}, ensure_ascii=False)

    # 这是最终关卡，不是提示词：即使 AI 真的请求取消，代码也会拒绝。
    # 当前 order["状态"] 的值是“制作中”，所以会直接从这里 return。
    if order["状态"] != "待制作":
        return json.dumps(
            {"success": False, "原因": f"订单当前是{order['状态']}，不能取消"},
            ensure_ascii=False,
        )

    # 只有状态确实为“待制作”，才会改动订单数据。
    order["状态"] = "已取消"
    return json.dumps({"success": True, "状态": "已取消"}, ensure_ascii=False)


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status, cancel_order]
tools_by_name = {registered_tool.name: registered_tool for registered_tool in tools}

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
).bind_tools(tools)

question = "请取消订单 A1001。"
messages = [
    SystemMessage(
        content="""
你是订单 Agent。
用户请求取消订单时，先调用 get_order_status。
拿到状态后，再调用 cancel_order 尝试取消。
拿到工具结果后，用简短中文回答用户。
不要承诺工具没有确认成功的操作。
"""
    ),
    HumanMessage(content=question),
]

# 一般需要：查状态 -> 请求取消 -> 最终回答，共 3 轮。
MAX_ROUNDS = 3

for round_number in range(1, MAX_ROUNDS + 1):
    response = model.invoke(messages)
    messages.append(response)

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
            # AI 只能请求调用；真正修改订单前，cancel_order 会再做一次状态判断。
            tool_result = selected_tool.invoke(tool_call["args"])

        print("工具结果：", tool_result)
        messages.append(
            ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
        )
else:
    print("Agent 超过 3 轮仍未完成，本次停止。")
