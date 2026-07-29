"""LangGraph 第 5 课：用 stream 实时看到节点执行和 state 更新。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class CancelState(TypedDict, total=False):
    order_id: str
    order_status: str
    final_reply: str


orders = {
    "A1001": {"状态": "待制作"},
    "A1002": {"状态": "制作中"},
}


def check_order(state: CancelState) -> dict:
    """节点 1：查状态，并只返回这次新得到的字段。"""
    order = orders.get(state["order_id"])
    if order is None:
        return {"order_status": "不存在"}
    return {"order_status": order["状态"]}


def choose_route(state: CancelState) -> str:
    """条件边：根据刚刚写进 state 的 order_status 选路。"""
    if state["order_status"] == "待制作":
        return "cancel_order"
    return "reject_cancellation"


def cancel_order(state: CancelState) -> dict:
    """节点 2A：允许取消的路线。"""
    return {"final_reply": f"订单 {state['order_id']} 已取消。"}


def reject_cancellation(state: CancelState) -> dict:
    """节点 2B：拒绝取消的路线。"""
    return {"final_reply": f"订单 {state['order_id']} 当前是{state['order_status']}，不能取消。"}


workflow = StateGraph(CancelState)
workflow.add_node("check_order", check_order)
workflow.add_node("cancel_order", cancel_order)
workflow.add_node("reject_cancellation", reject_cancellation)
workflow.add_edge(START, "check_order")
workflow.add_conditional_edges(
    "check_order",
    choose_route,
    {
        "cancel_order": "cancel_order",
        "reject_cancellation": "reject_cancellation",
    },
)
workflow.add_edge("cancel_order", END)
workflow.add_edge("reject_cancellation", END)
cancel_graph = workflow.compile()


def run_with_stream(order_id: str) -> None:
    """不等最终结果，节点每完成一次就打印一次 event。"""
    print(f"\n运行订单 {order_id}：")

    # stream_mode="updates" 表示 event 只给“本节点这一次更新了什么”，不重复给完整 state。
    # event 大致是：{"check_order": {"order_status": "待制作"}}
    for event in cancel_graph.stream(
        {"order_id": order_id},
        stream_mode="updates",
    ):
        # event 的键是刚完成的节点名，例如 check_order。
        for node_name, update in event.items():
            print("刚完成节点：", node_name)
            print("本次更新 state：", update)


run_with_stream("A1001")
run_with_stream("A1002")
