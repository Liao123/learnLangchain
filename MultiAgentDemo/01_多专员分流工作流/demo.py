"""多 Agent 第 1 课：总调度把问题交给对应的专员子图。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    question: str
    specialist: str
    answer: str


def route_question(state: SupportState) -> Command:
    # 这节课先用简单规则模拟“总调度”的判断。
    # 下一步接入模型后，这里可以由 AI 理解更自然的用户问题。
    if "退款" in state["question"]:
        print("总调度：交给退款专员。")
        return Command(
            update={"specialist": "退款专员"},
            goto="refund_specialist",
        )

    print("总调度：交给订单专员。")
    return Command(
        update={"specialist": "订单专员"},
        goto="order_specialist",
    )


def answer_order_question(state: SupportState) -> dict:
    print("订单专员子图：回答订单问题。")
    return {"answer": "订单 A1001 正在配送中，预计今天送达。"}


def answer_refund_question(state: SupportState) -> dict:
    print("退款专员子图：回答退款问题。")
    return {"answer": "退款申请提交后，通常会在 1 到 3 个工作日原路退回。"}


# 订单专员自己的小图。
order_workflow = StateGraph(SupportState)
order_workflow.add_node("answer_order_question", answer_order_question)
order_workflow.add_edge(START, "answer_order_question")
order_workflow.add_edge("answer_order_question", END)
order_specialist_graph = order_workflow.compile()

# 退款专员自己的小图。
refund_workflow = StateGraph(SupportState)
refund_workflow.add_node("answer_refund_question", answer_refund_question)
refund_workflow.add_edge(START, "answer_refund_question")
refund_workflow.add_edge("answer_refund_question", END)
refund_specialist_graph = refund_workflow.compile()


# 总图不负责回答业务问题，只负责分流到对应专员子图。
workflow = StateGraph(SupportState)
workflow.add_node("router", route_question)
workflow.add_node("order_specialist", order_specialist_graph)
workflow.add_node("refund_specialist", refund_specialist_graph)
workflow.add_edge(START, "router")
workflow.add_edge("order_specialist", END)
workflow.add_edge("refund_specialist", END)

support_graph = workflow.compile()

order_result = support_graph.invoke({"question": "订单 A1001 到哪里了？"})
print("最终回答：", order_result["answer"])

print()

refund_result = support_graph.invoke({"question": "我想申请退款。"})
print("最终回答：", refund_result["answer"])
