"""LangGraph 第 6 课：节点发生临时连接错误时，自动重试。"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy


class MemberState(TypedDict, total=False):
    member_id: str
    points: int
    final_reply: str


# 这只是为了演示“第几次请求”。真实项目里这里通常是 HTTP 请求次数，不会手写全局变量。
request_attempt_count = 0


def fetch_member_points(state: MemberState) -> dict:
    """模拟调用会员接口：前两次临时断开，第 3 次成功。"""
    global request_attempt_count
    request_attempt_count += 1

    print(f"查会员接口，第 {request_attempt_count} 次尝试")

    if request_attempt_count < 3:
        # ConnectionError 表示临时连接问题。抛出它后，LangGraph 会按 retry_policy 重试本节点。
        raise ConnectionError("会员接口临时不可用")

    # 第 3 次成功。节点只返回本次新得到的 state 字段。
    return {"points": 860}


def write_reply(state: MemberState) -> dict:
    """接口成功后，使用 state 中的 points 生成最终文字。"""
    return {"final_reply": f"会员 {state['member_id']} 当前有 {state['points']} 积分。"}


# max_attempts=3 包含第一次尝试：第 1、2 次失败后，还能再试第 3 次。
# retry_on=ConnectionError 表示只对连接错误重试，不会把任何异常都盲目重试。
# 0.1 秒间隔只为让课程快速运行；生产中通常等待更久，并采用退避策略。
retry_policy = RetryPolicy(
    initial_interval=0.1,
    backoff_factor=1.0,
    max_interval=0.1,
    max_attempts=3,
    jitter=False,
    retry_on=ConnectionError,
)

workflow = StateGraph(MemberState)
workflow.add_node(
    "fetch_member_points",
    fetch_member_points,
    retry_policy=retry_policy,
)
workflow.add_node("write_reply", write_reply)
workflow.add_edge(START, "fetch_member_points")
workflow.add_edge("fetch_member_points", "write_reply")
workflow.add_edge("write_reply", END)

member_graph = workflow.compile()

final_state = member_graph.invoke({"member_id": "M1001"})
print("\n最终答复：", final_state["final_reply"])
