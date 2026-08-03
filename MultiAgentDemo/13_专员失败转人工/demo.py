"""多 Agent 第 13 课：专员系统调用失败后，交回父图转人工客服。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    order_id: str
    order_status: str
    failure_reason: str
    final_reply: str


def query_order_system(order_id: str) -> str:
    if order_id == "A5000":
        # 模拟订单系统暂时连不上。
        raise ConnectionError("订单系统暂时不可用。")
    return "配送中"


def order_agent(state: SupportState) -> Command:
    try:
        order_status = query_order_system(state["order_id"])
    except ConnectionError as error:
        print("订单子图：查订单失败，交回父图转人工客服。")
        return Command(
            update={"failure_reason": str(error)},
            goto="human_service",
            graph=Command.PARENT,
        )

    print(f"订单子图：查到订单 {state['order_id']} 状态是“{order_status}”。")
    return Command(
        update={"order_status": order_status},
        goto="final_reply",
        graph=Command.PARENT,
    )


order_workflow = StateGraph(SupportState)
order_workflow.add_node("order_agent", order_agent)
order_workflow.add_edge(START, "order_agent")
order_subgraph = order_workflow.compile()


def route_to_order(state: SupportState) -> Command:
    return Command(goto="order_team")


def final_reply(state: SupportState) -> dict:
    return {"final_reply": f"订单 {state['order_id']} 当前{state['order_status']}。"}


def human_service(state: SupportState) -> dict:
    return {
        "final_reply": (
            f"订单 {state['order_id']} 暂时无法查询，已转人工客服处理。"
        )
    }


parent_workflow = StateGraph(SupportState)
parent_workflow.add_node("router", route_to_order)
parent_workflow.add_node("order_team", order_subgraph)
parent_workflow.add_node("final_reply", final_reply)
parent_workflow.add_node("human_service", human_service)
parent_workflow.add_edge(START, "router")
parent_workflow.add_edge("final_reply", END)
parent_workflow.add_edge("human_service", END)
support_graph = parent_workflow.compile()

success_state = support_graph.invoke({"order_id": "A1001"})
print("正常订单：", success_state["final_reply"])

print()

failed_state = support_graph.invoke({"order_id": "A5000"})
print("失败订单：", failed_state["final_reply"])
