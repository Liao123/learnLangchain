"""多 Agent 第 2 课：让模型判断问题应该交给哪个专员。"""

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

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)

# router_model 还是同一个 DeepSeek，只是额外要求它返回 JSON。
router_model = model.bind(response_format={"type": "json_object"})


def route_with_model(state: SupportState) -> Command:
    response = router_model.invoke(
        [
            SystemMessage(
                content="""
你是客服总调度。
判断用户问题应该交给哪个专员。

订单进度、配送、修改订单 -> order
退款、退货、退款到账 -> refund
无法判断 -> human

只能返回合法 JSON，格式必须是：
{"route": "order"}
"""
            ),
            HumanMessage(content=state["question"]),
        ]
    )

    # 例如 AI 返回：{"route": "refund"}。
    print("总调度 AI 原始返回：", response.content)

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

    print(f"总调度决定：交给{specialist}。")
    return Command(
        update={"specialist": specialist},
        goto=next_node,
    )


def answer_order_question(state: SupportState) -> dict:
    return {"answer": "订单专员：订单 A1001 正在配送中。"}


def answer_refund_question(state: SupportState) -> dict:
    return {"answer": "退款专员：退款通常会在 1 到 3 个工作日原路退回。"}


def transfer_to_human(state: SupportState) -> dict:
    return {"answer": "人工客服：这个问题需要人工进一步确认。"}


workflow = StateGraph(SupportState)
workflow.add_node("router", route_with_model)
workflow.add_node("order_specialist", answer_order_question)
workflow.add_node("refund_specialist", answer_refund_question)
workflow.add_node("human_service", transfer_to_human)
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
