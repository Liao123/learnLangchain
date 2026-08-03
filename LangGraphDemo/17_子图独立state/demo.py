"""LangGraph 第 17 课：主图和子图使用各自的 state 格式。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class OrderState(TypedDict, total=False):
    order_id: str
    product_name: str
    amount: float
    balance: float
    payment_status: str
    reply: str


class PaymentState(TypedDict, total=False):
    # 支付子图只认识金额、余额和支付状态，不认识订单号、商品名等主图字段。
    amount: float
    balance: float
    payment_status: str


def deduct_balance(state: PaymentState) -> dict:
    print("支付子图收到：", state)
    return {
        # 子图自己的输入是 amount=28.0、balance=100.0，扣完后是 72.0。
        "balance": state["balance"] - state["amount"],
        "payment_status": "已支付",
    }


payment_workflow = StateGraph(PaymentState)
payment_workflow.add_node("deduct_balance", deduct_balance)
payment_workflow.add_edge(START, "deduct_balance")
payment_workflow.add_edge("deduct_balance", END)
payment_subgraph = payment_workflow.compile()


def run_payment_subgraph(state: OrderState) -> dict:
    # 主图 state 很多字段；这里只挑支付子图真正需要的两个字段。
    payment_input = {
        "amount": state["amount"],
        "balance": state["balance"],
    }
    print("\n主图交给支付子图：", payment_input)

    payment_output = payment_subgraph.invoke(payment_input)
    print("支付子图返回：", payment_output)

    # 主图也只接收自己需要的结果，不把子图整个 state 直接塞回来。
    return {
        "balance": payment_output["balance"],
        "payment_status": payment_output["payment_status"],
    }


def finish_order(state: OrderState) -> dict:
    return {
        "reply": (
            f"订单 {state['order_id']} 的 {state['product_name']} 已支付，"
            f"余额剩余 {state['balance']} 元。"
        )
    }


main_workflow = StateGraph(OrderState)
main_workflow.add_node("payment", run_payment_subgraph)
main_workflow.add_node("finish_order", finish_order)
main_workflow.add_edge(START, "payment")
main_workflow.add_edge("payment", "finish_order")
main_workflow.add_edge("finish_order", END)

order_graph = main_workflow.compile()

final_state = order_graph.invoke(
    {
        "order_id": "A1001",
        "product_name": "咖啡豆礼盒",
        "amount": 28.0,
        "balance": 100.0,
    }
)
print("\n最终回答：", final_state["reply"])
