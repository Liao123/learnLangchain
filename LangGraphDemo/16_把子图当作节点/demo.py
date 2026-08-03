"""LangGraph 第 16 课：把支付子图当作主图的一个节点。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class OrderState(TypedDict, total=False):
    order_id: str
    amount: float
    balance: float
    payment_status: str
    reply: str


def check_balance(state: OrderState) -> dict:
    print("支付子图：检查余额。")
    if state["balance"] >= state["amount"]:
        return {"payment_status": "可以支付"}
    return {"payment_status": "余额不足"}


def deduct_balance(state: OrderState) -> dict:
    print("支付子图：扣除余额。")
    return {
        # 例：100.0 - 28.0，新的 balance 是 72.0。
        "balance": state["balance"] - state["amount"],
        "payment_status": "已支付",
    }


def build_payment_subgraph():
    payment_workflow = StateGraph(OrderState)
    payment_workflow.add_node("check_balance", check_balance)
    payment_workflow.add_node("deduct_balance", deduct_balance)
    payment_workflow.add_edge(START, "check_balance")
    payment_workflow.add_edge("check_balance", "deduct_balance")
    payment_workflow.add_edge("deduct_balance", END)
    return payment_workflow.compile()


def prepare_order(state: OrderState) -> dict:
    print("主图：准备创建订单。")
    return {}


def finish_order(state: OrderState) -> dict:
    print("主图：支付完成，创建订单。")
    return {
        "reply": f"订单 {state['order_id']} 创建成功，余额剩余 {state['balance']} 元。"
    }


# payment_subgraph 虽然内部有两个节点，但加入主图后可以当作一个节点使用。
payment_subgraph = build_payment_subgraph()

main_workflow = StateGraph(OrderState)
main_workflow.add_node("prepare_order", prepare_order)
main_workflow.add_node("payment", payment_subgraph)
main_workflow.add_node("finish_order", finish_order)
main_workflow.add_edge(START, "prepare_order")
main_workflow.add_edge("prepare_order", "payment")
main_workflow.add_edge("payment", "finish_order")
main_workflow.add_edge("finish_order", END)

order_graph = main_workflow.compile()

# 初始 state：金额 28.0，余额 100.0。
final_state = order_graph.invoke(
    {"order_id": "A1001", "amount": 28.0, "balance": 100.0}
)
print("\n最终回答：", final_state["reply"])
