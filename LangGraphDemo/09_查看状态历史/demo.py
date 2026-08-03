"""LangGraph 第 9 课：查看一个 thread 保存过的全部 state。"""

from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class OrderState(TypedDict, total=False):
    order_id: str
    status: str
    reply: str


LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "checkpoints.sqlite"


def create_order(state: OrderState) -> dict:
    return {"status": "待支付"}


def pay_order(state: OrderState) -> dict:
    return {"status": "已支付"}


def finish_order(state: OrderState) -> dict:
    return {
        "status": "已完成",
        "reply": f"订单 {state['order_id']} 已完成。",
    }


def build_graph(checkpointer: SqliteSaver):
    workflow = StateGraph(OrderState)
    workflow.add_node("create_order", create_order)
    workflow.add_node("pay_order", pay_order)
    workflow.add_node("finish_order", finish_order)
    workflow.add_edge(START, "create_order")
    workflow.add_edge("create_order", "pay_order")
    workflow.add_edge("pay_order", "finish_order")
    workflow.add_edge("finish_order", END)
    return workflow.compile(checkpointer=checkpointer)


DATABASE_PATH.parent.mkdir(exist_ok=True)

# 每次用新的 thread_id，避免把之前运行的订单状态混进本次演示。
config = {"configurable": {"thread_id": f"history-{uuid4()}"}}

with SqliteSaver.from_conn_string(str(DATABASE_PATH)) as checkpointer:
    checkpointer.setup()
    order_graph = build_graph(checkpointer)

    final_state = order_graph.invoke({"order_id": "A1001"}, config=config)
    print("最后状态：", final_state)

    # history 是一个快照列表；每个 snapshot 都记录当时的 values 和下一步节点。
    history = list(order_graph.get_state_history(config))
    print(f"\n共找到 {len(history)} 个历史快照。")
    print("下面按实际执行顺序查看（最早 -> 最新）：")

    for index, snapshot in enumerate(reversed(history), start=1):
        print(f"第 {index} 个快照：")
        print("  values =", snapshot.values)
        print("  next   =", snapshot.next)
