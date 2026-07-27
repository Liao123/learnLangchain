"""第 62 课：模型通过工具说明，决定本次该调用哪个工具。"""

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
    # M1001 的值会作为 get_member_points 工具的真实返回资料。
    "M1001": {"等级": "金卡", "积分": 860},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单的商品和当前状态。用户问订单进度、制作状态时使用。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False, "原因": "订单不存在"}, ensure_ascii=False)
    return json.dumps({"found": True, **order}, ensure_ascii=False)


@tool
def get_member_points(member_id: str) -> str:
    """查询会员等级和当前积分。用户问会员积分、金卡权益时使用。"""
    member = members.get(member_id)
    if member is None:
        return json.dumps({"found": False, "原因": "会员不存在"}, ensure_ascii=False)
    # 本题传入 M1001，工具结果是：{"found": true, "等级": "金卡", "积分": 860}
    return json.dumps({"found": True, **member}, ensure_ascii=False)


@tool
def get_store_hours() -> str:
    """查询星光咖啡店今天的营业时间。用户问开门、打烊时间时使用。"""
    return json.dumps({"营业时间": "08:00-22:00"}, ensure_ascii=False)


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status, get_member_points, get_store_hours]
tools_by_name = {registered_tool.name: registered_tool for registered_tool in tools}

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
    # 网络偶尔中断时，LangChain 会自动再试 3 次。
    max_retries=3,
    timeout=60,
).bind_tools(tools)

# 改这一句测试其他问题。这里不写 if 判断关键词，由模型选择工具。
question = "金卡会员 M1001 现在有多少积分？"
messages = [
    SystemMessage(
        content="""
你是星光咖啡店客服 Agent。
涉及订单、会员资料或门店营业时间时，必须先调用合适的工具查询。
只能根据工具结果回答，不能自行编造资料。
"""
    ),
    HumanMessage(content=question),
]

# 正常情况是：第 1 轮选工具，第 2 轮根据工具结果回答。
MAX_ROUNDS = 3

for round_number in range(1, MAX_ROUNDS + 1):
    try:
        response = model.invoke(messages)
    except APIConnectionError:
        # 这一步还没得到模型回复，所以工具也还没有执行。
        print("无法连接 DeepSeek，本次没有执行任何工具。请直接重新运行一次。")
        print("若持续出现，请检查网络、代理或 DeepSeek 服务状态。")
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
            # 例如本题：selected_tool 是 get_member_points，参数是 {"member_id": "M1001"}。
            tool_result = selected_tool.invoke(tool_call["args"])

        print("工具结果：", tool_result)
        messages.append(
            ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
        )
else:
    print("Agent 超过 3 轮仍未完成，本次停止。")
