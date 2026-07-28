"""第 67 课：自动检查 Agent 面对不同问题时，是否选对第一个工具。"""

import os

from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from openai import APIConnectionError


# 这些工具的函数体本课不会执行；AI 只会读取工具名、参数和三引号说明来作选择。
@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。用户问订单进度、制作状态时使用。"""
    return "本课不执行工具。"


@tool
def get_member_points(member_id: str) -> str:
    """查询会员等级和积分。用户问会员积分、金卡权益时使用。"""
    return "本课不执行工具。"


@tool
def get_store_hours() -> str:
    """查询门店营业时间。用户问开门、打烊时间时使用。"""
    return "本课不执行工具。"


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status, get_member_points, get_store_hours]
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
    max_retries=3,
    timeout=60,
).bind_tools(tools)

# 每一项都是一条回归测试：问题是什么，期望 AI 第一步选什么工具。
test_cases = [
    {
        "question": "订单 A1001 现在什么状态？",
        "expected_tool": "get_order_status",
    },
    {
        "question": "金卡会员 M1001 现在有多少积分？",
        "expected_tool": "get_member_points",
    },
    {
        "question": "门店今晚几点打烊？",
        "expected_tool": "get_store_hours",
    },
]

system_message = SystemMessage(
    content="""
你是星光咖啡店客服 Agent。
根据用户问题，选择且只选择一个最合适的工具。
本轮只请求工具，不要直接回答用户，也不要调用多个工具。
"""
)

passed_count = 0

for case in test_cases:
    # 每一题都从同一条系统规则开始，避免上一道题的 messages 影响下一道题。
    messages = [system_message, HumanMessage(content=case["question"])]

    try:
        response = model.invoke(messages)
    except APIConnectionError:
        print(f"[连接失败] {case['question']}")
        continue

    # response.tool_calls 大致是：[{"name": "get_member_points", "args": {"member_id": "M1001"}, ...}]
    actual_tool = response.tool_calls[0]["name"] if response.tool_calls else None
    is_passed = actual_tool == case["expected_tool"]

    if is_passed:
        passed_count += 1
        status = "通过"
    else:
        status = "失败"

    print(f"[{status}] 问题：{case['question']}")
    print("  期望工具：", case["expected_tool"])
    print("  实际工具：", actual_tool)

print(f"\n工具选择测试：{passed_count} / {len(test_cases)} 通过")
