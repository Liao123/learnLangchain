"""多 Agent 第 10 课：两个专员子图通过父图总调度接力。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    question: str
    order_status: str
    refund_result: str
    final_reply: str


def order_agent(state: SupportState) -> Command:
    print("订单子图：查到订单 A1001 已签收。")
    return Command(
        update={"order_status": "已签收"},
        # 订单专员不直接去退款子图，而是先交回父图总调度。
        goto="supervisor",
        graph=Command.PARENT,
    )


order_workflow = StateGraph(SupportState)
order_workflow.add_node("order_agent", order_agent)
order_workflow.add_edge(START, "order_agent")
order_subgraph = order_workflow.compile()


def refund_agent(state: SupportState) -> Command:
    # 这里能读到订单子图先前写进共同 state 的 order_status。
    print(f"退款子图：确认订单状态是“{state['order_status']}”，提交退款。")
    return Command(
        update={"refund_result": "退款申请已提交。"},
        goto="final_reply",
        graph=Command.PARENT,
    )


refund_workflow = StateGraph(SupportState)
refund_workflow.add_node("refund_agent", refund_agent)
refund_workflow.add_edge(START, "refund_agent")
refund_subgraph = refund_workflow.compile()


def supervisor(state: SupportState) -> Command:
    # 第一次进入父图时，没有订单状态，先派订单子图。
    if "order_status" not in state:
        print("父图总调度：先进入订单子图。")
        return Command(goto="order_team")

    # 订单子图交回 order_status 后，再派退款子图。
    print("父图总调度：订单状态已返回，现在进入退款子图。")
    return Command(goto="refund_team")


def final_reply(state: SupportState) -> dict:
    print("父图：收到退款子图结果，统一生成最终回复。")
    return {
        "final_reply": (
            f"客服回复：订单状态为{state['order_status']}，{state['refund_result']}"
        )
    }


parent_workflow = StateGraph(SupportState)
parent_workflow.add_node("supervisor", supervisor)
parent_workflow.add_node("order_team", order_subgraph)
parent_workflow.add_node("refund_team", refund_subgraph)
parent_workflow.add_node("final_reply", final_reply)
parent_workflow.add_edge(START, "supervisor")
parent_workflow.add_edge("final_reply", END)

# order_team、refund_team 的下一步由各自子图中的 Command.PARENT 决定。
support_graph = parent_workflow.compile()

final_state = support_graph.invoke({"question": "我想退订单 A1001。"})
print("\n最终回答：", final_state["final_reply"])
