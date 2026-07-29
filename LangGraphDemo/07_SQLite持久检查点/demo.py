"""LangGraph 第 7 课：用 SQLite 保存暂停状态，并在新进程中恢复。"""

import sys
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class CancelState(TypedDict, total=False):
    order_id: str
    confirmation: str
    final_reply: str


orders = {
    # 每次重新启动 Python，这份演示数据都会从“待制作”重新开始。
    "A1001": {"状态": "待制作"},
}

# __file__ 是当前 demo.py 的路径。数据库只放在本课自己的 输出 文件夹。
LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "checkpoints.sqlite"
THREAD_ID = "cancel-A1001"


def ask_for_confirmation(state: CancelState) -> dict:
    """暂停点：第一次到这里时停止；resume 后才得到 confirmation 的值。"""
    confirmation = interrupt(
        {
            "类型": "取消订单确认",
            "订单号": state["order_id"],
            "问题": f"确定取消订单 {state['order_id']} 吗？",
        }
    )
    return {"confirmation": confirmation}


def cancel_order(state: CancelState) -> dict:
    """恢复后运行：只有 resume 传回的值恰好是“确认”，才修改订单。"""
    if state["confirmation"] != "确认":
        return {"final_reply": "未收到“确认”，订单没有取消。"}

    orders[state["order_id"]]["状态"] = "已取消"
    return {"final_reply": f"订单 {state['order_id']} 已取消。"}


def build_graph(checkpointer: SqliteSaver):
    """每个 Python 进程都重新搭建同一张图，但它们共用同一个 SQLite 文件。"""
    workflow = StateGraph(CancelState)
    workflow.add_node("ask_for_confirmation", ask_for_confirmation)
    workflow.add_node("cancel_order", cancel_order)
    workflow.add_edge(START, "ask_for_confirmation")
    workflow.add_edge("ask_for_confirmation", "cancel_order")
    workflow.add_edge("cancel_order", END)
    return workflow.compile(checkpointer=checkpointer)


def main() -> None:
    # 命令格式：py demo.py start 或 py demo.py resume 确认。
    mode = sys.argv[1] if len(sys.argv) >= 2 else ""
    confirmation = sys.argv[2] if len(sys.argv) >= 3 else ""

    if mode not in {"start", "resume"}:
        print("用法：py demo.py start")
        print("或：py demo.py resume 确认")
        return

    DATABASE_PATH.parent.mkdir(exist_ok=True)
    config = {"configurable": {"thread_id": THREAD_ID}}

    # from_conn_string 会打开本课的 checkpoints.sqlite；with 结束时会关闭文件连接。
    with SqliteSaver.from_conn_string(str(DATABASE_PATH)) as checkpointer:
        checkpointer.setup()  # 第一次运行时自动创建 SQLite 表。
        cancel_graph = build_graph(checkpointer)

        if mode == "start":
            # 图会停在 interrupt(...)。暂停前的 state 已经写进 checkpoints.sqlite。
            result = cancel_graph.invoke({"order_id": "A1001"}, config=config)
            if "__interrupt__" in result:
                print("流程已暂停，确认点已写入 SQLite。")
                print("现在可以运行：py demo.py resume 确认")
            return

        # 这是全新的 Python 进程，但 thread_id 相同，SqliteSaver 能读回上一条暂停检查点。
        if not DATABASE_PATH.exists():
            print("还没有 SQLite 记录，请先运行：py demo.py start")
            return

        final_state = cancel_graph.invoke(Command(resume=confirmation), config=config)
        print(final_state["final_reply"])
        print("本进程中的订单状态：", orders["A1001"]["状态"])


if __name__ == "__main__":
    main()
