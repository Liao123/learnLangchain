"""LangGraph 第 18 课：state 是流程数据，config 是本次运行配置。"""

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph


class OrderState(TypedDict):
    order_id: str
    amount: float
    reply: str


def create_reply(state: OrderState, config: RunnableConfig) -> dict:
    # state 是流程数据。本次只有订单号和金额：
    # {"order_id": "A1001", "amount": 28.0}
    print("节点收到的 state：", state)

    # config 是这一次运行时额外传入的配置，不会自动合并进 state。
    customer_name = config["configurable"]["customer_name"]
    membership = config["configurable"]["membership"]
    print("节点从 config 读到：", customer_name, membership)

    return {
        "reply": f"{customer_name}，你的 {membership}会员订单金额是 {state['amount']} 元。"
    }


workflow = StateGraph(OrderState)
workflow.add_node("create_reply", create_reply)
workflow.add_edge(START, "create_reply")
workflow.add_edge("create_reply", END)

order_graph = workflow.compile()

final_state = order_graph.invoke(
    {"order_id": "A1001", "amount": 28.0},
    config={
        "configurable": {
            "customer_name": "小王",
            "membership": "金卡",
        }
    },
)

print("\n最终 state：", final_state)
