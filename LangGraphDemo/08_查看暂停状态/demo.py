"""LangGraph 第 8 课：读取暂停流程当前保存的 state。"""

from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class CancelState(TypedDict, total=False):
    order_id: str
    confirmation: str
    final_reply: str


LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "checkpoints.sqlite"


def ask_for_confirmation(state: CancelState) -> dict:
    confirmation = interrupt({"问题": f"确定取消订单 {state['order_id']} 吗？"})
    return {"confirmation": confirmation}


def cancel_order(state: CancelState) -> dict:
    if state["confirmation"] == "确认":
        return {"final_reply": f"订单 {state['order_id']} 已取消。"}
    return {"final_reply": "订单没有取消。"}


def build_graph(checkpointer: SqliteSaver):
    workflow = StateGraph(CancelState)
    workflow.add_node("ask_for_confirmation", ask_for_confirmation)
    workflow.add_node("cancel_order", cancel_order)
    workflow.add_edge(START, "ask_for_confirmation")
    workflow.add_edge("ask_for_confirmation", "cancel_order")
    workflow.add_edge("cancel_order", END)
    return workflow.compile(checkpointer=checkpointer)


def show_snapshot(title: str, snapshot) -> None:
    print(f"\n{title}")
    print("当前 state：", snapshot.values)
    print("图下一步：", snapshot.next)


DATABASE_PATH.parent.mkdir(exist_ok=True)

# 每次运行生成新编号，避免上一次的状态影响这次演示。
config = {"configurable": {"thread_id": f"inspect-{uuid4()}"}}

with SqliteSaver.from_conn_string(str(DATABASE_PATH)) as checkpointer:
    checkpointer.setup()
    cancel_graph = build_graph(checkpointer)

    cancel_graph.invoke({"order_id": "A1001"}, config=config)
    paused_snapshot = cancel_graph.get_state(config)
    show_snapshot("流程暂停后", paused_snapshot)

    cancel_graph.invoke(Command(resume="确认"), config=config)
    completed_snapshot = cancel_graph.get_state(config)
    show_snapshot("流程恢复并结束后", completed_snapshot)
