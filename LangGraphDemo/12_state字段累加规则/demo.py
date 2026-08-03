"""LangGraph 第 12 课：让多个节点累加同一个 state 字段。"""

from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class OrderState(TypedDict):
    order_id: str

    # add 是这个字段的合并规则。
    # 第一个节点返回 ["已校验地址"]，第二个返回 ["已检查库存"]。
    # LangGraph 用 add 合并后，steps 会变成两个列表相加的结果。
    steps: Annotated[list[str], add]


def check_address(state: OrderState) -> dict:
    return {"steps": ["已校验地址"]}


def check_stock(state: OrderState) -> dict:
    return {"steps": ["已检查库存"]}


workflow = StateGraph(OrderState)
workflow.add_node("check_address", check_address)
workflow.add_node("check_stock", check_stock)
workflow.add_edge(START, "check_address")
workflow.add_edge("check_address", "check_stock")
workflow.add_edge("check_stock", END)

order_graph = workflow.compile()

# 初始 steps 是空列表 []。
# 节点依次写入后，最终会是 ["已校验地址", "已检查库存"]。
final_state = order_graph.invoke({"order_id": "A1001", "steps": []})
print("最终 state：", final_state)
