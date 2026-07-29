"""LangGraph 第 3 课：暂停取消订单流程，得到人工确认后再继续。"""

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


# 这是图在运行时共享的数据结构。total=False 表示节点可以只更新其中一部分字段。
class CancelState(TypedDict, total=False):
    order_id: str
    order_status: str
    confirmation: str
    final_reply: str


orders = {
    # 本题开始时的值是“待制作”。确认后才会改成“已取消”。
    "A1001": {"商品": "冰拿铁", "状态": "待制作"},
}


def check_order(state: CancelState) -> dict:
    """第一个节点：读取订单状态。"""
    order_id = state["order_id"]  # 本题值是 A1001。
    order = orders.get(order_id)

    if order is None:
        return {"final_reply": f"没有找到订单 {order_id}。"}

    return {"order_status": order["状态"]}


def ask_for_confirmation(state: CancelState) -> dict:
    """第二个节点：暂停图，等待外部的确认结果。"""
    order_id = state["order_id"]

    # 第一次运行到这里时，interrupt 会立刻暂停整张图并把这个字典交给终端或前端。
    # 图恢复后，interrupt(...) 的返回值就是 Command(resume=...) 传回来的值。
    # 例如用户输入“确认”后，confirmation 的值就是字符串“确认”。
    confirmation = interrupt(
        {
            "类型": "取消订单确认",
            "订单号": order_id,
            "问题": f"确定取消订单 {order_id} 吗？",
        }
    )
    return {"confirmation": confirmation}


def cancel_order(state: CancelState) -> dict:
    """第三个节点：只有得到准确确认，才改动订单数据。"""
    order_id = state["order_id"]
    order = orders.get(order_id)

    if state["confirmation"] != "确认":
        return {"final_reply": "未收到“确认”，订单没有取消。"}

    # 即使用户确认了，业务代码仍然要自己检查状态，不能只相信流程走到了这里。
    if order is None or order["状态"] != "待制作":
        return {"final_reply": "订单当前状态不能取消。"}

    order["状态"] = "已取消"
    return {"final_reply": f"订单 {order_id} 已取消。"}


# 这张图没有 AI 节点，专门聚焦“暂停 -> 人工确认 -> 恢复”。
workflow = StateGraph(CancelState)
workflow.add_node("check_order", check_order)
workflow.add_node("ask_for_confirmation", ask_for_confirmation)
workflow.add_node("cancel_order", cancel_order)

workflow.add_edge(START, "check_order")
workflow.add_edge("check_order", "ask_for_confirmation")
workflow.add_edge("ask_for_confirmation", "cancel_order")
workflow.add_edge("cancel_order", END)

# 图必须有 checkpointer，才能记住暂停前的 state，并在 resume 时从原位置继续。
memory = MemorySaver()
cancel_graph = workflow.compile(checkpointer=memory)

# 同一个 thread_id 代表同一次“取消订单”流程。
config = {"configurable": {"thread_id": "cancel-A1001"}}

print("订单当前状态：", orders["A1001"]["状态"])
print("图运行到人工确认节点后暂停。")

# 第一次 invoke 会停在 interrupt(...) 处，不会继续执行 cancel_order。
paused_result = cancel_graph.invoke({"order_id": "A1001"}, config=config)

if "__interrupt__" in paused_result:
    confirmation = input("确定取消订单 A1001 吗？输入 确认 才会取消：").strip()

    # Command(resume=...) 把用户输入交回 interrupt，并从暂停的 ask_for_confirmation 节点继续。
    final_state = cancel_graph.invoke(Command(resume=confirmation), config=config)
    print(final_state["final_reply"])
    print("订单现在状态：", orders["A1001"]["状态"])
else:
    print("流程没有进入确认暂停点。")
