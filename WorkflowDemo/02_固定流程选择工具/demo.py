"""第 56 课：程序按固定规则选择工具。"""


orders = {
    "A1001": {
        "商品": "冰拿铁",
        "状态": "制作中",
        "取餐号": "18",
    }
}


def query_order(order_id):
    """订单工具：输入 A1001，返回这笔订单。"""
    order = orders.get(order_id)
    if order is None:
        return {"found": False, "message": "没有找到这个订单。"}

    return {
        "found": True,
        "商品": order["商品"],
        "状态": order["状态"],
        "取餐号": order["取餐号"],
    }


def query_business_hours():
    """营业时间工具：不需要输入，直接返回门店时间。"""
    return {
        "工作日": "08:00 至 20:00",
        "周末": "09:00 至 21:00",
    }


# 程序目前收到的需求是“查营业时间”。
# 改成“查订单”后，下面的 if 会走另一条固定路线。
user_action = "查营业时间"
user_order_id = "A1001"

print("用户要做：", user_action)

# if / elif 就是这节课的 workflow：不是 AI 猜，而是程序按你写好的文字选择工具。
if user_action == "查订单":
    print("程序调用：查询订单工具")
    result = query_order(user_order_id)

    if result["found"]:
        print("工具返回：", result)
        print(f"给用户：您的{result['商品']}正在{result['状态']}，取餐号是 {result['取餐号']}。")
    else:
        print("给用户：", result["message"])

elif user_action == "查营业时间":
    print("程序调用：查询营业时间工具")
    result = query_business_hours()
    print("工具返回：", result)
    print(f"给用户：周末营业时间是 {result['周末']}。")

else:
    print("给用户：这个需求暂时没有对应的工具。")
