"""LangGraph 第 14 课：根据商品数量，动态创建多个检查任务。"""

from operator import add
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class OrderState(TypedDict):
    items: list[dict]
    checked_items: Annotated[list[str], add]
    result: str


class ItemTaskState(TypedDict):
    # 每个动态任务只需要拿到自己的一件商品。
    # 例如：{"item": {"name": "拿铁", "quantity": 2}}
    item: dict


def split_items(state: OrderState) -> list[Send]:
    tasks = []

    # items 有几件商品，就创建几个发往 check_item 的任务。
    for item in state["items"]:
        print(f"为 {item['name']} 创建一个 check_item 任务。")
        tasks.append(Send("check_item", {"item": item}))

    return tasks


def check_item(state: ItemTaskState) -> dict:
    item = state["item"]
    print(f"正在检查：{item['name']}，数量：{item['quantity']}")
    return {"checked_items": [f"{item['name']} x {item['quantity']} 已检查"]}


def create_result(state: OrderState) -> dict:
    return {"result": "；".join(state["checked_items"])}


workflow = StateGraph(OrderState)
workflow.add_node("check_item", check_item)
workflow.add_node("create_result", create_result)

# split_items 不返回一个节点名，而是返回多个 Send 对象。
# 每个 Send 都表示“把自己的 item 交给 check_item 跑一次”。
workflow.add_conditional_edges(START, split_items, ["check_item"])
workflow.add_edge("check_item", "create_result")
workflow.add_edge("create_result", END)

order_graph = workflow.compile()

final_state = order_graph.invoke(
    {
        "items": [
            {"name": "拿铁", "quantity": 2},
            {"name": "美式", "quantity": 1},
            {"name": "蛋糕", "quantity": 1},
        ],
        "checked_items": [],
    }
)

print("\n汇总结果：", final_state["result"])
