"""多 Agent 第 5 课：不同专员绑定不同工具，形成权限边界。"""

import json
import os
from typing import TypedDict

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    question: str
    specialist: str
    answer: str


orders = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天"},
}
refunds = {
    "R2001": {"status": "处理中", "estimated_arrival": "2 个工作日内"},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。输入订单号，例如 A1001。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False}, ensure_ascii=False)
    return json.dumps({"found": True, **order}, ensure_ascii=False)


@tool
def get_refund_status(refund_id: str) -> str:
    """查询退款进度。输入退款单号，例如 R2001。"""
    refund = refunds.get(refund_id)
    if refund is None:
        return json.dumps({"found": False}, ensure_ascii=False)
    return json.dumps({"found": True, **refund}, ensure_ascii=False)


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
router_model = model.bind(response_format={"type": "json_object"})


def route_with_model(state: SupportState) -> Command:
    response = router_model.invoke(
        [
            SystemMessage(
                content="""
你是客服总调度。
订单进度、配送 -> order
退款进度、退款到账 -> refund
无法判断 -> human
只能返回 JSON，例如：{"route": "order"}
"""
            ),
            HumanMessage(content=state["question"]),
        ]
    )

    try:
        route = json.loads(response.content).get("route")
    except json.JSONDecodeError:
        route = "human"

    routes = {
        "order": ("订单专员", "order_specialist"),
        "refund": ("退款专员", "refund_specialist"),
        "human": ("人工客服", "human_service"),
    }
    specialist, next_node = routes.get(route, routes["human"])
    print(f"总调度：交给{specialist}。")
    return Command(update={"specialist": specialist}, goto=next_node)


def run_tool_agent(question: str, system_prompt: str, tools: list) -> str:
    # tools 是当前专员的工具白名单。
    # 订单专员传入 [get_order_status]；退款专员传入 [get_refund_status]。
    tool_model = model.bind_tools(tools)
    tools_by_name = {item.name: item for item in tools}
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=question)]

    # 最多 3 轮：模型请求工具 -> Python 执行 -> 模型生成最终回答。
    for _ in range(3):
        response = tool_model.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:
            selected_tool = tools_by_name.get(tool_call["name"])
            if selected_tool is None:
                tool_result = "该专员没有这个工具的权限。"
            else:
                print(f"专员调用工具：{tool_call['name']}，参数：{tool_call['args']}")
                tool_result = selected_tool.invoke(tool_call["args"])

            messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"],
                )
            )

    return "专员连续调用工具过多，本次停止。"


def order_specialist(state: SupportState) -> dict:
    answer = run_tool_agent(
        state["question"],
        """
你是订单专员。
必须先调用 get_order_status 查询订单，不能猜测状态。
只能根据工具结果，用简短中文回答。
""",
        [get_order_status],
    )
    return {"answer": f"订单专员：{answer}"}


def refund_specialist(state: SupportState) -> dict:
    answer = run_tool_agent(
        state["question"],
        """
你是退款专员。
必须先调用 get_refund_status 查询退款进度，不能猜测状态。
只能根据工具结果，用简短中文回答。
""",
        [get_refund_status],
    )
    return {"answer": f"退款专员：{answer}"}


def human_service(state: SupportState) -> dict:
    return {"answer": "人工客服：这个问题需要进一步确认。"}


workflow = StateGraph(SupportState)
workflow.add_node("router", route_with_model)
workflow.add_node("order_specialist", order_specialist)
workflow.add_node("refund_specialist", refund_specialist)
workflow.add_node("human_service", human_service)
workflow.add_edge(START, "router")
workflow.add_edge("order_specialist", END)
workflow.add_edge("refund_specialist", END)
workflow.add_edge("human_service", END)

support_graph = workflow.compile()

question = input("请输入订单或退款问题：").strip()
if not question:
    raise RuntimeError("没有输入问题。")

final_state = support_graph.invoke({"question": question})
print("最终回答：", final_state["answer"])
