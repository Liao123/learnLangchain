"""LangGraph 第 10 课：暂停后人工修正 state，再恢复流程。"""

from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class DeliveryState(TypedDict, total=False):
    order_id: str
    address: str
    confirmation: str
    shipping_label: str


LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "checkpoints.sqlite"


def ask_for_confirmation(state: DeliveryState) -> dict:
    confirmation = interrupt(
        {"问题": f"订单 {state['order_id']} 要发往：{state['address']}，确认发货吗？"}
    )
    return {"confirmation": confirmation}


def create_shipping_label(state: DeliveryState) -> dict:
    return {
        "shipping_label": f"发货单：订单 {state['order_id']}，寄往 {state['address']}。"
    }


def build_graph(checkpointer: SqliteSaver):
    workflow = StateGraph(DeliveryState)
    workflow.add_node("ask_for_confirmation", ask_for_confirmation)
    workflow.add_node("create_shipping_label", create_shipping_label)
    workflow.add_edge(START, "ask_for_confirmation")
    workflow.add_edge("ask_for_confirmation", "create_shipping_label")
    workflow.add_edge("create_shipping_label", END)
    return workflow.compile(checkpointer=checkpointer)


DATABASE_PATH.parent.mkdir(exist_ok=True)
config = {"configurable": {"thread_id": f"correct-address-{uuid4()}"}}

with SqliteSaver.from_conn_string(str(DATABASE_PATH)) as checkpointer:
    checkpointer.setup()
    delivery_graph = build_graph(checkpointer)

    # 流程先暂停。此时 state 的 address 是“北京市朝阳区 1 号”。
    delivery_graph.invoke(
        {"order_id": "A1001", "address": "北京市朝阳区 1 号"},
        config=config,
    )
    print("暂停时的 state：", delivery_graph.get_state(config).values)

    # 人工只提交要改的字段，不用重传 order_id 等其他 state。
    # 更新前：address = "北京市朝阳区 1 号"
    # 更新后：address = "上海市浦东新区 2 号"
    delivery_graph.update_state(config, {"address": "上海市浦东新区 2 号"})
    print("人工改地址后的 state：", delivery_graph.get_state(config).values)

    final_state = delivery_graph.invoke(Command(resume="确认"), config=config)
    print("恢复后的发货单：", final_state["shipping_label"])
