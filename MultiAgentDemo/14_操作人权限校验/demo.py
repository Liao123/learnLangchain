"""多 Agent 第 14 课：退款专员根据运行 config 校验操作人权限。"""

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class RefundState(TypedDict, total=False):
    order_id: str
    refund_amount: float
    refund_result: str
    final_reply: str


def refund_agent(state: RefundState, config: RunnableConfig) -> Command:
    # 角色来自运行配置，而不是用户问题或模型输出。
    operator_name = config["configurable"]["operator_name"]
    operator_role = config["configurable"]["operator_role"]
    print(f"退款子图：当前操作人是 {operator_name}，角色是 {operator_role}。")

    if operator_role != "refund_approver":
        refund_result = f"{operator_name} 没有退款审批权限，退款没有提交。"
    else:
        refund_result = (
            f"{operator_name} 已批准订单 {state['order_id']} 的 "
            f"{state['refund_amount']} 元退款。"
        )

    return Command(
        update={"refund_result": refund_result},
        goto="final_reply",
        graph=Command.PARENT,
    )


refund_workflow = StateGraph(RefundState)
refund_workflow.add_node("refund_agent", refund_agent)
refund_workflow.add_edge(START, "refund_agent")
refund_subgraph = refund_workflow.compile()


def route_to_refund(state: RefundState) -> Command:
    return Command(goto="refund_team")


def final_reply(state: RefundState) -> dict:
    return {"final_reply": f"客服回复：{state['refund_result']}"}


parent_workflow = StateGraph(RefundState)
parent_workflow.add_node("router", route_to_refund)
parent_workflow.add_node("refund_team", refund_subgraph)
parent_workflow.add_node("final_reply", final_reply)
parent_workflow.add_edge(START, "router")
parent_workflow.add_edge("final_reply", END)
support_graph = parent_workflow.compile()


def run_refund(operator_name: str, operator_role: str) -> None:
    final_state = support_graph.invoke(
        {"order_id": "A1001", "refund_amount": 28.0},
        config={
            "configurable": {
                "operator_name": operator_name,
                "operator_role": operator_role,
            }
        },
    )
    print(final_state["final_reply"])


run_refund("小李", "customer_service")
print()
run_refund("小周", "refund_approver")
