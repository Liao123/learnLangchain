"""第 58 课：AI 提取意图，workflow 把每一步记录到 state。"""

import json
import os


orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中"},
    "A1002": {"商品": "美式咖啡", "状态": "待制作"},
}


def extract_intent(question):
    """AI 只提取动作和订单号，例如 {"action": "cancel_order", "order_id": "A1001"}。"""
    from langchain.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("请先在 PowerShell 设置 DEEPSEEK_API_KEY。")

    model = ChatOpenAI(
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
        api_key=api_key,
    ).bind(response_format={"type": "json_object"})

    response = model.invoke([
        SystemMessage(
            content="""
你只负责提取用户意图，不负责执行订单操作。
只返回 JSON：
{"action": "query_order 或 cancel_order", "order_id": "订单号或空字符串"}
查订单状态使用 query_order；取消订单使用 cancel_order。
"""
        ),
        HumanMessage(content=question),
    ])
    return json.loads(response.content)


def query_order(order_id):
    """订单工具：输入 A1001，返回订单资料或 None。"""
    return orders.get(order_id)


def cancel_order(order_id):
    """取消工具：只有待制作订单才允许改变状态。"""
    order = orders[order_id]
    if order["状态"] != "待制作":
        return False

    order["状态"] = "已取消"
    return True


def run_workflow(question, intent):
    """固定 workflow：校验 AI 输出 -> 查订单 -> 按业务规则处理。"""
    # state 开始时只有用户原话；后面每一步都会补充新信息。
    state = {"用户问题": question, "当前步骤": "收到 AI 意图"}

    action = intent.get("action", "")
    order_id = intent.get("order_id", "")
    # 例如 AI 对“帮我取消订单 A1001”的输出会让这两个值变成 cancel_order、A1001。
    state["动作"] = action
    state["订单号"] = order_id

    # AI 只能从下面两个动作中选。它输出其他文字时，workflow 不执行。
    if action not in ("query_order", "cancel_order"):
        state["当前步骤"] = "结束"
        state["最终答复"] = "我暂时无法识别这个订单需求。"
        return state

    order = query_order(order_id)
    if order is None:
        state["当前步骤"] = "结束"
        state["最终答复"] = "没有找到这个订单。"
        return state

    # A1001 此时会写入“制作中”；A1002 会写入“待制作”。
    state["订单状态"] = order["状态"]

    if action == "query_order":
        state["当前步骤"] = "结束"
        state["最终答复"] = f"您的{order['商品']}当前状态是：{order['状态']}。"
        return state

    cancelled = cancel_order(order_id)
    state["当前步骤"] = "结束"
    if cancelled:
        state["订单状态"] = "已取消"
        state["最终答复"] = f"您的{order['商品']}订单已取消。"
    else:
        state["最终答复"] = f"订单已经{order['状态']}，暂时不能取消。"

    return state


def main():
    question = "帮我取消订单 A1001"
    print("用户原话：", question)

    intent = extract_intent(question)
    print("AI 提取：", intent)

    state = run_workflow(question, intent)
    print("流程 state：", state)
    print("给用户：", state["最终答复"])


if __name__ == "__main__":
    main()
