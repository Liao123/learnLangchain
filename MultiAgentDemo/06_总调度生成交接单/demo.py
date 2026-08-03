"""多 Agent 第 6 课：总调度生成结构化交接单，再交给专员。"""

import json
import os
from typing import TypedDict

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    question: str
    handoff: dict
    answer: str


orders = {
    "A1001": {"status": "配送中", "estimated_arrival": "今天"},
}
refunds = {
    "R2001": {"status": "处理中", "estimated_arrival": "2 个工作日内"},
}


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
router_model = model.bind(response_format={"type": "json_object"})


def route_with_handoff(state: SupportState) -> Command:
    response = router_model.invoke(
        [
            SystemMessage(
                content="""
你是客服总调度。识别用户问题应该交给哪个专员，以及业务单号。
订单进度、配送 -> route="order"，单号格式是 A 开头，例如 A1001。
退款进度、退款到账 -> route="refund"，单号格式是 R 开头，例如 R2001。
无法判断 -> route="human"。

只能返回合法 JSON，格式如下：
{"route": "order", "record_id": "A1001", "task": "查询配送进度"}
"""
            ),
            HumanMessage(content=state["question"]),
        ]
    )

    try:
        ai_handoff = json.loads(response.content)
    except json.JSONDecodeError:
        ai_handoff = {"route": "human"}

    route = ai_handoff.get("route")
    record_id = ai_handoff.get("record_id")
    task = ai_handoff.get("task")

    routes = {
        "order": "order_specialist",
        "refund": "refund_specialist",
        "human": "human_service",
    }
    next_node = routes.get(route, "human_service")

    # handoff 是总调度交给下一位专员的结构化工作单。
    # 例如：{"route": "order", "record_id": "A1001", "task": "查询配送进度"}
    handoff = {"route": route, "record_id": record_id, "task": task}
    print("总调度交接单：", handoff)
    return Command(update={"handoff": handoff}, goto=next_node)


def order_specialist(state: SupportState) -> dict:
    handoff = state["handoff"]
    order = orders.get(handoff["record_id"])
    if order is None:
        return {"answer": "订单专员：没有找到这张订单。"}

    return {
        "answer": (
            f"订单专员：订单 {handoff['record_id']} {order['status']}，"
            f"预计{order['estimated_arrival']}送达。"
        )
    }


def refund_specialist(state: SupportState) -> dict:
    handoff = state["handoff"]
    refund = refunds.get(handoff["record_id"])
    if refund is None:
        return {"answer": "退款专员：没有找到这笔退款。"}

    return {
        "answer": (
            f"退款专员：退款单 {handoff['record_id']} {refund['status']}，"
            f"预计{refund['estimated_arrival']}到账。"
        )
    }


def human_service(state: SupportState) -> dict:
    return {"answer": "人工客服：未能识别业务类型或单号，请补充信息。"}


workflow = StateGraph(SupportState)
workflow.add_node("router", route_with_handoff)
workflow.add_node("order_specialist", order_specialist)
workflow.add_node("refund_specialist", refund_specialist)
workflow.add_node("human_service", human_service)
workflow.add_edge(START, "router")
workflow.add_edge("order_specialist", END)
workflow.add_edge("refund_specialist", END)
workflow.add_edge("human_service", END)

support_graph = workflow.compile()

question = input("请输入带单号的订单或退款问题：").strip()
if not question:
    raise RuntimeError("没有输入问题。")

final_state = support_graph.invoke({"question": question})
print("最终回答：", final_state["answer"])
