"""第 65 课：让同一轮中互不依赖的工具并行执行。"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from openai import APIConnectionError


orders = {"A1001": {"商品": "冰拿铁", "状态": "制作中"}}
members = {"M1001": {"等级": "金卡", "积分": 860}}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。用户问订单进度时使用。"""
    # 模拟真实数据库或 HTTP 接口需要 1 秒。这个 sleep 只为看出并行效果。
    time.sleep(1)
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False, "原因": "订单不存在"}, ensure_ascii=False)
    return json.dumps({"found": True, **order}, ensure_ascii=False)


@tool
def get_member_points(member_id: str) -> str:
    """查询会员等级和积分。用户问会员积分时使用。"""
    # 这也是 1 秒，但会和上面的查订单同时开始。
    time.sleep(1)
    member = members.get(member_id)
    if member is None:
        return json.dumps({"found": False, "原因": "会员不存在"}, ensure_ascii=False)
    return json.dumps({"found": True, **member}, ensure_ascii=False)


def invoke_one_tool(tool_call: dict, tools_by_name: dict) -> tuple[dict, str]:
    """在线程里执行一个工具，并把“原请求 + 结果”一起带回来。"""
    selected_tool = tools_by_name.get(tool_call["name"])
    if selected_tool is None:
        return tool_call, "这个工具没有登记，不能执行。"

    # 例如 tool_call 是：{"name": "get_member_points", "args": {"member_id": "M1001"}}
    return tool_call, selected_tool.invoke(tool_call["args"])


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
订单状态和会员积分必须调用工具查询。
这两份资料互不依赖时，可以在同一轮请求两个工具。
拿到所有工具结果后，用简短中文回答。
"""
    ),
    HumanMessage(content=question),
]

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

    print(f"第 {round_number} 轮：AI 本轮请求 {len(response.tool_calls)} 个工具")
    started_at = time.perf_counter()

    # max_workers=2 表示最多同时跑两个线程；这里相当于前端 Promise.all。
    # 只把“本轮的工具请求”提交进去，for 不会等第一个工具结束才提交第二个。
    with ThreadPoolExecutor(max_workers=len(response.tool_calls)) as executor:
        futures = [
            executor.submit(invoke_one_tool, tool_call, tools_by_name)
            for tool_call in response.tool_calls
        ]

        # as_completed 会在“任意一个工具先完成”时，立刻取回它的结果。
        for future in as_completed(futures):
            tool_call, tool_result = future.result()
            print("工具完成：", tool_call["name"])
            print("工具结果：", tool_result)

            # 虽然结果可能先后顺序不同，但 tool_call_id 会让模型知道它对应哪个请求。
            messages.append(
                ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
            )

    elapsed_seconds = time.perf_counter() - started_at
    print(f"本轮工具执行耗时：{elapsed_seconds:.2f} 秒")
else:
    print("Agent 超过 3 轮仍未完成，本次停止。")
