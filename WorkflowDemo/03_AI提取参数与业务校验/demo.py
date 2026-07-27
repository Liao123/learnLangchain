"""第 57 课：AI 提取订单号，固定业务流程决定能否取消。"""

import json
import os

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


# 假装这是订单系统。
# A1001 已经制作中，不能取消；A1002 还是待制作，可以取消。
orders = {
    "A1001": {"商品": "冰拿铁", "状态": "制作中"},
    "A1002": {"商品": "美式咖啡", "状态": "待制作"},
}


def extract_order_id(question):
    """只让 AI 从自然语言中提取订单号。"""
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
你只负责从用户的话中提取订单号，不负责决定能否取消订单。
只返回 JSON，例如：{"order_id": "A1001"}。
没有订单号时返回：{"order_id": ""}。
"""
        ),
        HumanMessage(content=question),
    ])

    # data 的实际值大致是：{"order_id": "A1001"}。
    data = json.loads(response.content)
    return data.get("order_id", "").strip()


def cancel_order_workflow(order_id):
    """固定业务流程：查订单 -> 看状态 -> 决定取消或拒绝。"""
    order = orders.get(order_id)
    if order is None:
        return {"success": False, "message": "没有找到这个订单。"}

    # 这里的 order["状态"] 对 A1001 是“制作中”，对 A1002 是“待制作”。
    if order["状态"] != "待制作":
        return {
            "success": False,
            "状态": order["状态"],
            "message": f"订单已经{order['状态']}，暂时不能取消。",
        }

    # 只有“待制作”才允许改变订单状态。
    order["状态"] = "已取消"
    return {
        "success": True,
        "状态": order["状态"],
        "message": f"{order['商品']}订单已取消。",
    }


def main():
    question = "帮我取消订单 A1001"
    print("用户原话：", question)

    # AI 在这一步只输出 A1001，不执行取消动作。
    order_id = extract_order_id(question)
    print("AI 提取的订单号：", order_id)

    # 真正是否取消，由下面这个固定 Python workflow 决定。
    result = cancel_order_workflow(order_id)

    if "状态" in result:
        print("订单当前结果：", result["状态"])
    print("给用户：", result["message"])


if __name__ == "__main__":
    main()
