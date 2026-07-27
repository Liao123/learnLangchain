"""第 63 课：记录 Agent 每轮的工具调用和最终答复。"""

import json
import os

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI


orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中"},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单商品和当前状态。用户问订单进度时使用。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False, "原因": "订单不存在"}, ensure_ascii=False)
    return json.dumps({"found": True, **order}, ensure_ascii=False)


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status]
tools_by_name = {registered_tool.name: registered_tool for registered_tool in tools}

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
).bind_tools(tools)

question = "订单 A1001 现在什么状态？"
messages = [
    SystemMessage(
        content="""
你是订单客服 Agent。
订单状态必须调用工具查询，不能自行编造。
拿到工具结果后，用简短中文回答。
"""
    ),
    HumanMessage(content=question),
]

# trace 是运行日志，不会放进 messages，也不会交给 AI。
# 最终大致会长成：
# [{"轮次": 1, "事件": "请求工具", ...}, {"轮次": 1, "事件": "工具结果", ...}, ...]
trace = []
MAX_ROUNDS = 3

for round_number in range(1, MAX_ROUNDS + 1):
    response = model.invoke(messages)
    messages.append(response)

    if not response.tool_calls:
        trace.append(
            {
                "轮次": round_number,
                "事件": "最终答复",
                "内容": response.content,
            }
        )
        print("\nAgent 最终答复：")
        print(response.content)
        break

    for tool_call in response.tool_calls:
        # 这里记录的是 AI 的选择。例如 name 是 get_order_status，args 是 {"order_id": "A1001"}。
        trace.append(
            {
                "轮次": round_number,
                "事件": "请求工具",
                "工具": tool_call["name"],
                "参数": tool_call["args"],
            }
        )

        selected_tool = tools_by_name.get(tool_call["name"])
        if selected_tool is None:
            tool_result = "这个工具没有登记，不能执行。"
        else:
            tool_result = selected_tool.invoke(tool_call["args"])

        # 工具真实返回什么，也要记录。例如：{"found": true, "状态": "制作中"}。
        trace.append(
            {
                "轮次": round_number,
                "事件": "工具结果",
                "工具": tool_call["name"],
                "内容": tool_result,
            }
        )
        messages.append(
            ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
        )
else:
    trace.append({"轮次": MAX_ROUNDS, "事件": "强制停止"})
    print("Agent 超过 3 轮仍未完成，本次停止。")

print("\n本次执行轨迹：")
print(json.dumps(trace, ensure_ascii=False, indent=2))
