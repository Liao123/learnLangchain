"""第 64 课：一个模型回复可以同时包含多个工具调用请求。"""

import json
import os

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from openai import APIConnectionError


orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中"},
}
members = {
    "M1001": {"等级": "金卡", "积分": 860},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。用户提供订单号并询问订单进度时使用。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False, "原因": "订单不存在"}, ensure_ascii=False)
    return json.dumps({"found": True, **order}, ensure_ascii=False)


@tool
def get_member_points(member_id: str) -> str:
    """查询会员等级和积分。用户提供会员 ID 并询问积分时使用。"""
    member = members.get(member_id)
    if member is None:
        return json.dumps({"found": False, "原因": "会员不存在"}, ensure_ascii=False)
    return json.dumps({"found": True, **member}, ensure_ascii=False)


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status, get_member_points]
tools_by_name = {registered_tool.name: registered_tool for registered_tool in tools}

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
    max_retries=3,
    timeout=60,
).bind_tools(tools)

question = "请告诉我订单 A1001 的状态，以及会员 M1001 的积分。"
messages = [
    SystemMessage(
        content="""
你是星光咖啡店客服 Agent。
订单状态和会员积分都必须调用工具查询，不能自行编造。
当用户同时需要两份互不依赖的资料时，可以在同一轮请求两个工具。
拿到所有需要的工具结果后，再用简短中文回答。
"""
    ),
    HumanMessage(content=question),
]

# 这题通常是：第 1 轮请求两个工具，第 2 轮回答。
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

    # 这里的值可能是 2：同一个 response 里同时有“查订单”和“查积分”两个请求。
    print(f"第 {round_number} 轮：AI 本轮请求 {len(response.tool_calls)} 个工具")

    for tool_call in response.tool_calls:
        print("工具名称：", tool_call["name"])
        print("工具参数：", tool_call["args"])

        selected_tool = tools_by_name.get(tool_call["name"])
        if selected_tool is None:
            tool_result = "这个工具没有登记，不能执行。"
        else:
            # 例如先执行 get_order_status({"order_id": "A1001"})，
            # 再执行 get_member_points({"member_id": "M1001"})。
            # Python 这里仍按顺序执行；“同时请求”是指 AI 一次回复给出两个请求。
            tool_result = selected_tool.invoke(tool_call["args"])

        print("工具结果：", tool_result)
        messages.append(
            # 每个工具请求都有自己的 id，结果必须用同一个 id 对应回去。
            ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
        )
else:
    print("Agent 超过 3 轮仍未完成，本次停止。")
