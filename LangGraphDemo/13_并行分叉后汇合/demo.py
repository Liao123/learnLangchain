"""LangGraph 第 13 课：两个检查节点并行执行，完成后再汇合。"""

from operator import add
from time import perf_counter, sleep
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class OrderState(TypedDict):
    order_id: str
    steps: Annotated[list[str], add]
    result: str


def check_address(state: OrderState) -> dict:
    print("开始检查地址...")
    sleep(1)
    print("地址检查完成。")
    return {"steps": ["已校验地址"]}


def check_stock(state: OrderState) -> dict:
    print("开始检查库存...")
    sleep(1)
    print("库存检查完成。")
    return {"steps": ["已检查库存"]}


def create_result(state: OrderState) -> dict:
    # 只有地址、库存两个节点都完成后，才会运行到这里。
    return {"result": f"订单 {state['order_id']} 可以继续处理：{state['steps']}"}


workflow = StateGraph(OrderState)
workflow.add_node("check_address", check_address)
workflow.add_node("check_stock", check_stock)
workflow.add_node("create_result", create_result)

# START 同时分叉到两个互不依赖的检查节点。
workflow.add_edge(START, "check_address")
workflow.add_edge(START, "check_stock")

# 列表表示汇合条件：两个节点都完成，才进入 create_result。
workflow.add_edge(["check_address", "check_stock"], "create_result")
workflow.add_edge("create_result", END)

order_graph = workflow.compile()

started_at = perf_counter()
final_state = order_graph.invoke({"order_id": "A1001", "steps": []})
elapsed_seconds = perf_counter() - started_at

print("\n最终结果：", final_state["result"])
print(f"总耗时约：{elapsed_seconds:.1f} 秒")
