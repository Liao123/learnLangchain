"""第 66 课：把预料中的业务失败作为工具结果交回给 Agent。"""

import json
import os

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from openai import APIConnectionError


orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中"},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。用户提供订单号并询问订单进度时使用。"""
    order = orders.get(order_id)

    if order is None:
        # 这不是 Python 报错，而是一次正常的查询结果：没有找到订单。
        # 本题 order_id 的值是 A9999，所以工具实际返回下面这份 JSON。
        return json.dumps(
            {
                "success": False,
                "data": None,
                "error": {
                    "code": "ORDER_NOT_FOUND",
                    "message": f"未找到订单 {order_id}",
                },
            },
            ensure_ascii=False,
        )

    # 成功和失败都使用同一种外层格式，AI 和前端更容易统一处理。
    return json.dumps(
        {"success": True, "data": order, "error": None},
        ensure_ascii=False,
    )


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status]
tools_by_name = {registered_tool.name: registered_tool for registered_tool in tools}

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
    max_retries=3,
    timeout=60,
).bind_tools(tools)

question = "请查询订单 A9999 的状态。"
messages = [
    SystemMessage(
        content="""
你是订单客服 Agent。
订单状态必须调用工具查询，不能自行编造。
工具结果中 success 为 false 时，向用户说明 error.message，不要编造订单资料。
"""
    ),
    HumanMessage(content=question),
]

# 预期：第 1 轮查订单，第 2 轮根据 success=false 回答用户。
MAX_ROUNDS = 3

for round_number in range(1, MAX_ROUNDS + 1):
    try:
        response = model.invoke(messages)
    except APIConnectionError:
        print("无法连接 DeepSeek，本次没有执行任何工具。请直接重新运行一次。")
        break

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
            tool_result = selected_tool.invoke(tool_call["args"])

        print("工具结果：", tool_result)
        # success=false 的 JSON 也会放进 ToolMessage，继续交给下一轮 AI。
        messages.append(
            ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
        )
else:
    print("Agent 超过 3 轮仍未完成，本次停止。")
