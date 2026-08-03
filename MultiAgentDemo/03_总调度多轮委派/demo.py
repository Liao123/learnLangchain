"""多 Agent 第 3 课：总调度按已有 state 依次委派多个专员。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    question: str
    order_status: str
    refund_result: str
    answer: str


def supervisor(state: SupportState) -> Command:
    # 第一次进来时，state 只有 question，还没有 order_status。
    if "order_status" not in state:
        print("总调度：先委派订单专员，确认订单是否可以退款。")
        return Command(goto="order_agent")

    # 订单专员回来后，state 会多出 order_status="已签收"。
    if "refund_result" not in state:
        print("总调度：订单状态已确认，再委派退款专员。")
        return Command(goto="refund_agent")

    # 两位专员都完成后，才生成最终答复并结束。
    print("总调度：所需结果已齐，结束流程。")
    return Command(
        update={"answer": state["refund_result"]},
        goto=END,
    )


def order_agent(state: SupportState) -> dict:
    print("订单专员：查到订单 A1001 状态是“已签收”。")
    return {"order_status": "已签收"}


def refund_agent(state: SupportState) -> dict:
    # 这里能读取 order_agent 上一轮写进同一个 state 的 order_status。
    print(f"退款专员：确认订单状态是“{state['order_status']}”，提交退款申请。")
    return {"refund_result": "退款申请已提交，通常会在 1 到 3 个工作日原路退回。"}


workflow = StateGraph(SupportState)
workflow.add_node("supervisor", supervisor)
workflow.add_node("order_agent", order_agent)
workflow.add_node("refund_agent", refund_agent)
workflow.add_edge(START, "supervisor")

# 专员完成自己的任务后，都回到总调度，由总调度决定下一步。
workflow.add_edge("order_agent", "supervisor")
workflow.add_edge("refund_agent", "supervisor")

support_graph = workflow.compile()

final_state = support_graph.invoke({"question": "我想退订单 A1001。"})
print("\n最终回答：", final_state["answer"])
