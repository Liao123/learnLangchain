"""第 68 课：测试 Agent 是否选对工具，并提取出正确的参数。"""

import os

from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from openai import APIConnectionError


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。参数 order_id 是订单号，例如 A1001。"""
    return "本课不执行工具。"


@tool
def get_member_points(member_id: str) -> str:
    """查询会员积分。参数 member_id 是会员 ID，例如 M1001。"""
    return "本课不执行工具。"


@tool
def get_store_hours() -> str:
    """查询门店营业时间。不需要参数。"""
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

# expected_args 是 Python 字典。它就是我们希望 AI 生成的 tool_call["args"] 值。
test_cases = [
    {
        "question": "订单 A1001 现在什么状态？",
        "expected_tool": "get_order_status",
        "expected_args": {"order_id": "A1001"},
    },
    {
        "question": "金卡会员 M1001 现在有多少积分？",
        "expected_tool": "get_member_points",
        "expected_args": {"member_id": "M1001"},
    },
    {
        "question": "门店今晚几点打烊？",
        "expected_tool": "get_store_hours",
        "expected_args": {},
    },
]

system_message = SystemMessage(
    content="""
你是星光咖啡店客服 Agent。
根据用户问题，选择且只选择一个最合适的工具。
工具参数必须使用用户问题中提供的真实 ID。
本轮只请求工具，不要直接回答用户，也不要调用多个工具。
"""
)

passed_count = 0

for case in test_cases:
    messages = [system_message, HumanMessage(content=case["question"])]

    try:
        response = model.invoke(messages)
    except APIConnectionError:
        print(f"[连接失败] {case['question']}")
        continue

    if response.tool_calls:
        # LangChain 已把模型传来的 JSON 参数转换成 Python 字典。
        # 例如：{"order_id": "A1001"}，不用自己 json.loads。
        actual_tool = response.tool_calls[0]["name"]
        actual_args = response.tool_calls[0]["args"]
    else:
        actual_tool = None
        actual_args = None

    # 两项都相等才通过。工具名对但参数错，is_passed 仍然是 False。
    is_passed = (
        actual_tool == case["expected_tool"]
        and actual_args == case["expected_args"]
    )

    if is_passed:
        passed_count += 1
        status = "通过"
    else:
        status = "失败"

    print(f"[{status}] 问题：{case['question']}")
    print("  期望工具：", case["expected_tool"])
    print("  实际工具：", actual_tool)
    print("  期望参数：", case["expected_args"])
    print("  实际参数：", actual_args)

print(f"\n工具参数测试：{passed_count} / {len(test_cases)} 通过")
