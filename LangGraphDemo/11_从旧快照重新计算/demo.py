"""LangGraph 第 11 课：从旧快照修改数据，再重新运行后续节点。"""

from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class PriceState(TypedDict, total=False):
    order_id: str
    quantity: int
    unit_price: float
    total: float
    receipt: str


LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "checkpoints.sqlite"


def calculate_total(state: PriceState) -> dict:
    return {"total": state["quantity"] * state["unit_price"]}


def create_receipt(state: PriceState) -> dict:
    return {
        "receipt": f"订单 {state['order_id']}：总价 {state['total']} 元。"
    }


def build_graph(checkpointer: SqliteSaver):
    workflow = StateGraph(PriceState)
    workflow.add_node("calculate_total", calculate_total)
    workflow.add_node("create_receipt", create_receipt)
    workflow.add_edge(START, "calculate_total")
    workflow.add_edge("calculate_total", "create_receipt")
    workflow.add_edge("create_receipt", END)
    return workflow.compile(checkpointer=checkpointer)


def find_snapshot_before_calculation(history):
    # history 里的某个快照会显示 next = ("calculate_total",)。
    # 这表示当时已收到 quantity 和 unit_price，但还没有开始计算总价。
    for snapshot in history:
        if snapshot.next == ("calculate_total",):
            return snapshot
    raise RuntimeError("没有找到计算总价之前的快照。")


DATABASE_PATH.parent.mkdir(exist_ok=True)
original_config = {"configurable": {"thread_id": f"recalculate-{uuid4()}"}}

with SqliteSaver.from_conn_string(str(DATABASE_PATH)) as checkpointer:
    checkpointer.setup()
    price_graph = build_graph(checkpointer)

    # 第一次按 quantity=2 运行：2 * 12.5，结果是 total=25.0。
    original_final_state = price_graph.invoke(
        {"order_id": "A1001", "quantity": 2, "unit_price": 12.5},
        config=original_config,
    )
    print("原来的结果：", original_final_state["receipt"])

    history = list(price_graph.get_state_history(original_config))
    before_calculation = find_snapshot_before_calculation(history)

    # 从旧快照分出新记录：quantity 从 2 改为 3。
    # as_node="__start__" 表示“把这次人工修正当成新的流程输入”。
    corrected_config = price_graph.update_state(
        before_calculation.config,
        {"quantity": 3},
        as_node="__start__",
    )

    # None 表示不提交新输入，直接从 corrected_config 指向的保存点继续运行。
    corrected_final_state = price_graph.invoke(None, config=corrected_config)
    print("从旧快照改数量后重新计算：", corrected_final_state["receipt"])
