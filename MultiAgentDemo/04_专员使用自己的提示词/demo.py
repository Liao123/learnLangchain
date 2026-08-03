"""多 Agent 第 4 课：模型路由后，由对应专员模型生成回答。"""

import json
import os
from typing import TypedDict

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    question: str
    specialist: str
    answer: str


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

# 只有一个基础模型对象。不同专员靠不同系统提示词获得不同工作职责。
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
你是客服总调度。把用户问题分给订单专员或退款专员。
订单进度、配送、修改订单 -> order
退款、退货、退款到账 -> refund
无法判断 -> human
只能返回 JSON，例如：{"route": "refund"}
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
    print(f"总调度 AI 选择：{specialist}。")
    return Command(update={"specialist": specialist}, goto=next_node)


def order_specialist(state: SupportState) -> dict:
    response = model.invoke(
        [
            SystemMessage(
                content="""
你是订单专员。
只处理订单进度、配送和修改订单的问题。
已知资料：订单 A1001 正在配送中，预计今天送达。
用一句简短中文回答；资料不足时明确说需要订单号。
"""
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    return {"answer": f"订单专员：{response.content}"}


def refund_specialist(state: SupportState) -> dict:
    response = model.invoke(
        [
            SystemMessage(
                content="""
你是退款专员。
只处理退款、退货和退款到账问题。
已知资料：退款申请提交后，通常会在 1 到 3 个工作日原路退回。
用一句简短中文回答；不要承诺资料中没有的退款金额或到账时间。
"""
            ),
            HumanMessage(content=state["question"]),
        ]
    )
    return {"answer": f"退款专员：{response.content}"}


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
