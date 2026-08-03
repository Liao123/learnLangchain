"""多 Agent 第 8 课：用 recursion_limit 防止专员循环永远不结束。"""

from typing import TypedDict

from langgraph.errors import GraphRecursionError
from langgraph.graph import START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    rounds: int


def supervisor(state: SupportState) -> Command:
    rounds = state.get("rounds", 0) + 1
    print(f"第 {rounds} 次：总调度交给专员。")

    # 故意没有写“结束”的条件，演示错误流程。
    return Command(update={"rounds": rounds}, goto="specialist")


def specialist(state: SupportState) -> Command:
    print("专员处理完后，又回到总调度。")

    # 这里也故意不结束，于是形成 supervisor <-> specialist 循环。
    return Command(goto="supervisor")


workflow = StateGraph(SupportState)
workflow.add_node("supervisor", supervisor)
workflow.add_node("specialist", specialist)
workflow.add_edge(START, "supervisor")

support_graph = workflow.compile()

try:
    support_graph.invoke(
        {"rounds": 0},
        # 这是 LangGraph 运行配置，不是 state 字段。
        # 最多执行 4 个图步骤；到第 4 步仍未 END，就强制停止。
        config={"recursion_limit": 4},
    )
except GraphRecursionError:
    print("\n已停止：多 Agent 循环达到 recursion_limit=4，但仍没有走到 END。")
