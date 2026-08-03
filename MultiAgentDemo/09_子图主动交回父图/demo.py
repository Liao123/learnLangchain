"""多 Agent 第 9 课：子图用 Command.PARENT 主动跳回父图节点。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class SupportState(TypedDict, total=False):
    question: str
    answer: str
    final_reply: str


def refund_agent(state: SupportState) -> Command:
    print("退款子图：处理退款问题。")

    return Command(
        # 把退款子图的处理结果写进共同 state。
        update={"answer": "退款申请已提交，预计 1 到 3 个工作日原路退回。"},
        # final_reply 是父图节点，不是退款子图内部节点。
        goto="final_reply",
        # 告诉 LangGraph：goto 要到父图里找 final_reply。
        graph=Command.PARENT,
    )


# 退款专员自己的子图只有一个处理节点。
refund_workflow = StateGraph(SupportState)
refund_workflow.add_node("refund_agent", refund_agent)
refund_workflow.add_edge(START, "refund_agent")
refund_subgraph = refund_workflow.compile()


def route_to_refund(state: SupportState) -> Command:
    print("父图总调度：进入退款子图。")
    return Command(goto="refund_team")


def final_reply(state: SupportState) -> dict:
    print("父图：收到退款子图交回的结果，生成最终回复。")
    return {"final_reply": f"客服回复：{state['answer']}"}


parent_workflow = StateGraph(SupportState)
parent_workflow.add_node("router", route_to_refund)
parent_workflow.add_node("refund_team", refund_subgraph)
parent_workflow.add_node("final_reply", final_reply)
parent_workflow.add_edge(START, "router")
parent_workflow.add_edge("final_reply", END)

# 注意：这里没有写 refund_team -> final_reply。
# 这条跳转由退款子图里的 Command.PARENT 决定。
support_graph = parent_workflow.compile()

final_state = support_graph.invoke({"question": "我想退款。"})
print("\n最终回答：", final_state["final_reply"])
