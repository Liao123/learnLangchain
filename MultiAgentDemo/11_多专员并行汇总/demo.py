"""多 Agent 第 11 课：多个专员并行处理，再由父图汇总结果。"""

from operator import add
from time import perf_counter, sleep
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class SupportState(TypedDict, total=False):
    order_id: str
    refund_id: str
    # 两位专员都写 results；add 让两份列表累加，而不是互相覆盖。
    results: Annotated[list[str], add]
    summary: str


def dispatch_parallel(state: SupportState) -> list[Send]:
    # 两张 Send 任务会分别交给两个专员。
    # 订单专员只拿 order_id；退款专员只拿 refund_id。
    return [
        Send("order_agent", {"order_id": state["order_id"]}),
        Send("refund_agent", {"refund_id": state["refund_id"]}),
    ]


def order_agent(state: SupportState) -> dict:
    print("订单专员：开始查询订单。")
    sleep(1)
    print("订单专员：查询完成。")
    return {"results": [f"订单 {state['order_id']}：配送中"]}


def refund_agent(state: SupportState) -> dict:
    print("退款专员：开始查询退款。")
    sleep(1)
    print("退款专员：查询完成。")
    return {"results": [f"退款单 {state['refund_id']}：处理中"]}


def summarize(state: SupportState) -> dict:
    # 运行到这里时，results 已经是两位专员返回值的合并结果。
    # 例如：["订单 A1001：配送中", "退款单 R2001：处理中"]
    print("父图汇总：两位专员都已完成。")
    return {"summary": "；".join(state["results"])}


workflow = StateGraph(SupportState)
workflow.add_node("order_agent", order_agent)
workflow.add_node("refund_agent", refund_agent)
workflow.add_node("summarize", summarize)

# 根据实际任务创建两条专员任务。
workflow.add_conditional_edges(START, dispatch_parallel)

# 固定等待订单、退款两位专员都完成，才运行 summarize。
workflow.add_edge(["order_agent", "refund_agent"], "summarize")
workflow.add_edge("summarize", END)

support_graph = workflow.compile()

started_at = perf_counter()
final_state = support_graph.invoke(
    {"order_id": "A1001", "refund_id": "R2001", "results": []}
)
elapsed_seconds = perf_counter() - started_at

print("\n最终汇总：", final_state["summary"])
print(f"总耗时约：{elapsed_seconds:.1f} 秒")
