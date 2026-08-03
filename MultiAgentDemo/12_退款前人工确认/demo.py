"""多 Agent 第 12 课：退款子图暂停，人工确认后交回父图。"""

import sys
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class SupportState(TypedDict, total=False):
    order_id: str
    refund_amount: float
    confirmation: str
    refund_result: str
    final_reply: str


LESSON_DIR = Path(__file__).resolve().parent
DATABASE_PATH = LESSON_DIR / "输出" / "checkpoints.sqlite"
THREAD_ID = "refund-confirm-A1001"


def refund_agent(state: SupportState) -> Command:
    # 运行 start 时，流程停在这里，等待外部的 Command(resume="确认")。
    confirmation = interrupt(
        {
            "类型": "退款人工确认",
            "订单号": state["order_id"],
            "退款金额": state["refund_amount"],
            "问题": f"确认给订单 {state['order_id']} 退款 {state['refund_amount']} 元吗？",
        }
    )

    if confirmation == "确认":
        refund_result = f"订单 {state['order_id']} 已提交 {state['refund_amount']} 元退款。"
    else:
        refund_result = "未收到“确认”，退款没有提交。"

    # 退款子图处理结束，带着结果跳回父图的 final_reply。
    return Command(
        update={"confirmation": confirmation, "refund_result": refund_result},
        goto="final_reply",
        graph=Command.PARENT,
    )


def build_graph(checkpointer: SqliteSaver):
    refund_workflow = StateGraph(SupportState)
    refund_workflow.add_node("refund_agent", refund_agent)
    refund_workflow.add_edge(START, "refund_agent")
    refund_subgraph = refund_workflow.compile()

    def route_to_refund(state: SupportState) -> Command:
        return Command(goto="refund_team")

    def final_reply(state: SupportState) -> dict:
        return {"final_reply": f"客服回复：{state['refund_result']}"}

    parent_workflow = StateGraph(SupportState)
    parent_workflow.add_node("router", route_to_refund)
    parent_workflow.add_node("refund_team", refund_subgraph)
    parent_workflow.add_node("final_reply", final_reply)
    parent_workflow.add_edge(START, "router")
    parent_workflow.add_edge("final_reply", END)
    return parent_workflow.compile(checkpointer=checkpointer)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) >= 2 else ""
    confirmation = sys.argv[2] if len(sys.argv) >= 3 else ""

    if mode not in {"start", "resume"}:
        print("用法：py demo.py start")
        print("或：py demo.py resume 确认")
        return

    DATABASE_PATH.parent.mkdir(exist_ok=True)
    config = {"configurable": {"thread_id": THREAD_ID}}

    with SqliteSaver.from_conn_string(str(DATABASE_PATH)) as checkpointer:
        checkpointer.setup()
        support_graph = build_graph(checkpointer)

        if mode == "start":
            result = support_graph.invoke(
                {"order_id": "A1001", "refund_amount": 28.0},
                config=config,
            )
            if "__interrupt__" in result:
                print("退款子图已暂停，确认点已写入 SQLite。")
                print("现在运行：py demo.py resume 确认")
            return

        final_state = support_graph.invoke(Command(resume=confirmation), config=config)
        print(final_state["final_reply"])


if __name__ == "__main__":
    main()
