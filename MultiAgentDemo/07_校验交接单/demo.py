"""多 Agent 第 7 课：Python 校验模型生成的 handoff 后再分流。"""

import json
import os
from typing import Literal, TypedDict

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, ValidationError


class SupportState(TypedDict, total=False):
    question: str
    handoff: dict
    answer: str


class Handoff(BaseModel):
    # Literal 表示 route 只能是这三个值之一，不能是模型自己编出的其他文字。
    route: Literal["order", "refund", "human"]
    # human 路线可以没有单号；订单、退款路线则需要在下面额外检查单号。
    record_id: str | None = None
    task: str


orders = {"A1001": {"status": "配送中"}}
refunds = {"R2001": {"status": "处理中"}}

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
router_model = model.bind(response_format={"type": "json_object"})


def route_with_validation(state: SupportState) -> Command:
    response = router_model.invoke(
        [
            SystemMessage(
                content="""
你是客服总调度。识别业务路线、单号和任务。
订单进度、配送 -> order，订单号 A 开头，例如 A1001。
退款进度、到账 -> refund，退款单号 R 开头，例如 R2001。
无法判断 -> human。
只能返回 JSON：
{"route": "order", "record_id": "A1001", "task": "查询订单状态"}
"""
            ),
            HumanMessage(content=state["question"]),
        ]
    )

    try:
        raw_handoff = json.loads(response.content)
        handoff = Handoff.model_validate(raw_handoff)

        # “订单”或“退款”路线没有单号，也不能交给业务专员处理。
        if handoff.route in {"order", "refund"} and not handoff.record_id:
            raise ValueError("订单或退款路线缺少单号。")
    except (json.JSONDecodeError, ValidationError, ValueError) as error:
        print("交接单不合格，转人工客服：", error)
        return Command(
            update={"handoff": {"route": "human", "task": "人工核对"}},
            goto="human_service",
        )

    # model_dump() 把 Handoff 对象变回普通 dict，才能方便写进 LangGraph state。
    checked_handoff = handoff.model_dump()
    print("通过 Python 校验的交接单：", checked_handoff)

    routes = {
        "order": "order_specialist",
        "refund": "refund_specialist",
        "human": "human_service",
    }
    return Command(
        update={"handoff": checked_handoff},
        goto=routes[handoff.route],
    )


def order_specialist(state: SupportState) -> dict:
    order_id = state["handoff"]["record_id"]
    order = orders.get(order_id)
    if order is None:
        return {"answer": f"订单专员：没有找到订单 {order_id}。"}
    return {"answer": f"订单专员：订单 {order_id} 当前{order['status']}。"}


def refund_specialist(state: SupportState) -> dict:
    refund_id = state["handoff"]["record_id"]
    refund = refunds.get(refund_id)
    if refund is None:
        return {"answer": f"退款专员：没有找到退款单 {refund_id}。"}
    return {"answer": f"退款专员：退款单 {refund_id} 当前{refund['status']}。"}


def human_service(state: SupportState) -> dict:
    return {"answer": "人工客服：请补充正确的订单号或退款单号。"}


workflow = StateGraph(SupportState)
workflow.add_node("router", route_with_validation)
workflow.add_node("order_specialist", order_specialist)
workflow.add_node("refund_specialist", refund_specialist)
workflow.add_node("human_service", human_service)
workflow.add_edge(START, "router")
workflow.add_edge("order_specialist", END)
workflow.add_edge("refund_specialist", END)
workflow.add_edge("human_service", END)

support_graph = workflow.compile()

question = input("请输入带单号的问题：").strip()
if not question:
    raise RuntimeError("没有输入问题。")

final_state = support_graph.invoke({"question": question})
print("最终回答：", final_state["answer"])
