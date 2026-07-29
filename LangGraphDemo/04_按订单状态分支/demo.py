"""LangGraph 第 4 课：根据订单状态，让图走不同路线。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# 这不是一份真正的数据，而是说明图运行时的 state 最多会有哪些字段。
# 每个节点拿到的 state 都像：{"order_id": "A1001", "order_status": "待制作", ...}
class CancelState(TypedDict, total=False):
    order_id: str
    order_status: str
    final_reply: str


orders = {
    "A1001": {"商品": "冰拿铁", "状态": "待制作"},
    "A1002": {"商品": "美式咖啡", "状态": "制作中"},
}


def check_order(state: CancelState) -> dict:
    """节点 1：查询订单，并把订单状态写进 state。"""
    order_id = state["order_id"]
    order = orders.get(order_id)

    if order is None:
        return {"order_status": "不存在", "final_reply": f"未找到订单 {order_id}。"}

    # 对 A1001，这次返回 {"order_status": "待制作"}。
    # LangGraph 会把这个结果合并回共享 state。
    return {"order_status": order["状态"]}


def choose_cancellation_route(state: CancelState) -> str:
    """条件边：只看 state["order_status"]，返回下一站的节点名。"""
    if state["order_status"] == "待制作":
        return "cancel_order"
    return "reject_cancellation"


def cancel_order(state: CancelState) -> dict:
    """节点 2A：允许取消时，才真正修改订单。"""
    order_id = state["order_id"]
    orders[order_id]["状态"] = "已取消"
    return {"final_reply": f"订单 {order_id} 已取消。"}


def reject_cancellation(state: CancelState) -> dict:
    """节点 2B：不允许取消时，给出拒绝原因。"""
    order_id = state["order_id"]
    status = state["order_status"]
    return {"final_reply": f"订单 {order_id} 当前是{status}，不能取消。"}


workflow = StateGraph(CancelState)
workflow.add_node("check_order", check_order)
workflow.add_node("cancel_order", cancel_order)
workflow.add_node("reject_cancellation", reject_cancellation)

workflow.add_edge(START, "check_order")

# check_order 跑完后，不固定去某一站，而是执行 choose_cancellation_route 决定分支。
workflow.add_conditional_edges(
    "check_order",
    choose_cancellation_route,
    {
        "cancel_order": "cancel_order",
        "reject_cancellation": "reject_cancellation",
    },
)
workflow.add_edge("cancel_order", END)
workflow.add_edge("reject_cancellation", END)

cancel_graph = workflow.compile()


def run_case(order_id: str) -> None:
    """启动一次新的图运行，并打印这一单最终 state 里的答复。"""
    print(f"\n取消订单 {order_id}：")
    final_state = cancel_graph.invoke({"order_id": order_id})
    print(final_state["final_reply"])


# 用两张状态不同的订单，直接看出同一张图会走不同路线。
run_case("A1001")
run_case("A1002")
