"""第 59 课：AI 提出取消订单，用户确认后才真正执行。"""

import json
import os


# A1002 是待制作订单，专门用于演示“确认后才能取消”。
orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中"},
    "A1002": {"商品": "美式咖啡", "状态": "待制作"},
}


def extract_order_id(question):
    """AI 只从自然语言中提取订单号。"""
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
        SystemMessage(content='只返回 JSON：{"order_id": "订单号或空字符串"}。'),
        HumanMessage(content=question),
    ])
    return json.loads(response.content).get("order_id", "").strip()


def prepare_cancellation(order_id):
    """第一段 workflow：只检查订单并准备取消，绝不改变订单状态。"""
    order = orders.get(order_id)
    if order is None:
        return {"步骤": "结束", "最终答复": "没有找到这个订单。"}

    if order["状态"] != "待制作":
        return {
            "步骤": "结束",
            "最终答复": f"订单已经{order['状态']}，暂时不能取消。",
        }

    # A1002 到这里时，state 的值大致是：
    # {"步骤": "等待确认", "订单号": "A1002", "商品": "美式咖啡"}。
    return {
        "步骤": "等待确认",
        "订单号": order_id,
        "商品": order["商品"],
    }


def confirm_cancellation(state, user_confirmation):
    """第二段 workflow：只有用户输入“确认”才改变订单状态。"""
    if state["步骤"] != "等待确认":
        return state

    if user_confirmation != "确认":
        state["步骤"] = "结束"
        state["最终答复"] = "已取消本次操作，订单没有变化。"
        return state

    orders[state["订单号"]]["状态"] = "已取消"
    state["步骤"] = "结束"
    state["最终答复"] = f"{state['商品']}订单已取消。"
    return state


def main():
    question = "帮我取消订单 A1002"
    print("用户原话：", question)

    order_id = extract_order_id(question)
    print("AI 提取的订单号：", order_id)

    state = prepare_cancellation(order_id)
    print("流程 state：", state)

    if state["步骤"] == "等待确认":
        user_confirmation = input("输入 确认 才会取消订单：").strip()
        state = confirm_cancellation(state, user_confirmation)

    print("给用户：", state["最终答复"])


if __name__ == "__main__":
    main()
