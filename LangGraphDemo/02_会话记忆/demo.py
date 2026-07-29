"""LangGraph 第 2 课：让 LangGraph 通过 thread_id 保存同一个会话的 messages。"""

import json
import os

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
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
    return json.dumps(
        {"found": True, "商品": order["商品"], "状态": order["状态"]},
        ensure_ascii=False,
    )


@tool
def get_pickup_number(order_id: str) -> str:
    """查询订单取餐号。用户问取餐号时使用。"""
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
    """agent 节点：state 中会自动带上本会话以前保存的 messages。"""
    return {"messages": [model.invoke(state["messages"])]}


def should_continue(state: MessagesState) -> str:
    """AI 请求工具就去 tools；AI 直接回答就结束。"""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", []):
        return "tools"
    return END


workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END},
)
workflow.add_edge("tools", "agent")

# MemorySaver 是内存检查点仓库。compile 时传进去，图每走一步都会保存状态。
memory = MemorySaver()
agent_graph = workflow.compile(checkpointer=memory)


def print_last_answer(state: MessagesState) -> None:
    """从本次完整 messages 中，倒着找到最后一条没有工具调用的 AI 答复。"""
    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage) and not message.tool_calls and message.content:
            print("Agent：", message.content)
            return


system_message = SystemMessage(
    content="""
你是订单客服 Agent。
订单状态和取餐号必须调用工具查询，不能自行编造。
用户使用“那”“它”等代词时，结合此前同一会话的消息理解指代。
拿到工具结果后，用简短中文回答。
"""
)

# thread_id 是会话编号。两次 invoke 使用同一个值，MemorySaver 才会取回旧 messages。
conversation_config = {"configurable": {"thread_id": "customer-001"}}

try:
    print("用户（第 1 轮）：订单 A1001 现在什么状态？")
    first_state = agent_graph.invoke(
        {
            "messages": [
                system_message,
                HumanMessage(content="订单 A1001 现在什么状态？"),
            ]
        },
        config=conversation_config,
    )
    print_last_answer(first_state)
    print("此会话目前保存的 messages 数：", len(first_state["messages"]))

    # 第二轮只提交新问题，没有再次放 A1001，也没有手动加入第一轮历史。
    print("\n用户（第 2 轮）：那取餐号呢？")
    second_state = agent_graph.invoke(
        {"messages": [HumanMessage(content="那取餐号呢？")]},
        config=conversation_config,
    )
    print_last_answer(second_state)
    print("此会话目前保存的 messages 数：", len(second_state["messages"]))
except APIConnectionError:
    print("无法连接 DeepSeek，本次没有执行任何工具。请直接重新运行一次。")
