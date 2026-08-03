"""LangGraph 第 15 课：节点用 Command 同时更新 state 和决定下一步。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class OrderState(TypedDict, total=False):
    order_id: str
    quantity: int
    available: int
    stock_status: str
    reply: str


def check_stock(state: OrderState) -> Command:
    if state["quantity"] <= state["available"]:
        print(f"{state['order_id']}：库存充足，去 create_order。")
        return Command(
            # 把本节点的检查结果写进 state。
            update={"stock_status": "库存充足"},
            # 不需要 add_conditional_edges，直接指定下一节点。
            goto="create_order",
        )

    print(f"{state['order_id']}：库存不足，去 reject_order。")
    return Command(
        update={"stock_status": "库存不足"},
        goto="reject_order",
    )


def create_order(state: OrderState) -> dict:
    return {"reply": f"订单 {state['order_id']} 已创建。"}


def reject_order(state: OrderState) -> dict:
    return {"reply": f"订单 {state['order_id']} 库存不足，无法创建。"}


workflow = StateGraph(OrderState)
workflow.add_node("check_stock", check_stock)
workflow.add_node("create_order", create_order)
workflow.add_node("reject_order", reject_order)
workflow.add_edge(START, "check_stock")
workflow.add_edge("create_order", END)
workflow.add_edge("reject_order", END)

order_graph = workflow.compile()

# A1001：quantity=2，小于 available=5，所以会去 create_order。
enough_stock = order_graph.invoke(
    {"order_id": "A1001", "quantity": 2, "available": 5}
)
print("最终回答：", enough_stock["reply"])

# A1002：quantity=4，大于 available=1，所以会去 reject_order。
not_enough_stock = order_graph.invoke(
    {"order_id": "A1002", "quantity": 4, "available": 1}
)
print("最终回答：", not_enough_stock["reply"])
