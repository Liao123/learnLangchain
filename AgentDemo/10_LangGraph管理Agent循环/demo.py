"""第 69 课：用 LangGraph 管理“模型 -> 工具 -> 模型”的循环。"""

import json
import os

from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from openai import APIConnectionError


orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中", "取餐号": "18"},
}


@tool
def get_order_status(order_id: str) -> str:
    """查询订单状态。用户问订单进度时使用。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False, "原因": "订单不存在"}, ensure_ascii=False)
    # 本题 A1001 的结果是：{"found": true, "商品": "冰拿铁", "状态": "制作中"}
    return json.dumps(
        {"found": True, "商品": order["商品"], "状态": order["状态"]},
        ensure_ascii=False,
    )


@tool
def get_pickup_number(order_id: str) -> str:
    """查询订单取餐号。只有订单正在制作时才使用。"""
    order = orders.get(order_id)
    if order is None:
        return json.dumps({"found": False, "原因": "订单不存在"}, ensure_ascii=False)
    return json.dumps({"found": True, "取餐号": order["取餐号"]}, ensure_ascii=False)


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

tools = [get_order_status, get_pickup_number]
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
    max_retries=3,
    timeout=60,
).bind_tools(tools)


def call_model(state: MessagesState) -> dict:
    """agent 节点：读取 state["messages"]，让模型决定下一步。"""
    response = model.invoke(state["messages"])
    # LangGraph 会把这个 AIMessage 自动追加到 state["messages"]。
    return {"messages": [response]}


def should_continue(state: MessagesState) -> str:
    """条件边：根据 AI 最新回复，决定去 tools 还是 END。"""
    last_message = state["messages"][-1]

    # 第 1、2 次模型回复有 tool_calls，所以返回 "tools"。
    # 第 3 次是最终文字答复，tool_calls 是空列表，所以返回 END。
    if getattr(last_message, "tool_calls", []):
        return "tools"
    return END


# StateGraph(MessagesState) 表示整张图共享的状态里有 messages 列表。
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)  # agent 节点运行 call_model 函数。
workflow.add_node("tools", ToolNode(tools))  # tools 节点由 LangGraph 自动执行工具、追加 ToolMessage。

workflow.add_edge(START, "agent")  # 程序开始后，先让 AI 看用户问题。
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END},
)
workflow.add_edge("tools", "agent")  # 工具结果出来后，再回到 AI。

# compile() 得到可运行的 Agent 图。此后不需要我们手写 for 循环。
agent_graph = workflow.compile()

system_message = """
你是订单客服 Agent。
先调用 get_order_status 查询订单状态。
只有收到“状态是制作中”的工具结果后，才调用 get_pickup_number。
拿到需要的工具结果后，用简短中文回答用户。
"""
question = "订单 A1001 现在什么状态？如果正在制作，请告诉我取餐号。"

try:
    final_state = agent_graph.invoke(
        {
            "messages": [
                SystemMessage(content=system_message),
                HumanMessage(content=question),
            ]
        },
        # recursion_limit 是保险：图意外一直循环时，最多走 6 个节点就停止。
        config={"recursion_limit": 6},
    )
except APIConnectionError:
    print("无法连接 DeepSeek，本次没有执行任何工具。请直接重新运行一次。")
else:
    print("Agent 图的执行过程：")

    # final_state["messages"] 保存了图运行后的全部消息，和之前手写 messages 一样。
    for message in final_state["messages"]:
        if isinstance(message, ToolMessage):
            print("工具结果：", message.content)
        elif isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                print("Agent 请求工具：", tool_call["name"], tool_call["args"])
        elif isinstance(message, AIMessage) and message.content:
            print("Agent 最终答复：", message.content)
