"""第 55 课：最简单的工具调用。"""


# 这里先假装这是订单系统里的资料。
# A1001 对应的实际值是：冰拿铁、制作中、取餐号 18。
orders = {
    "A1001": {
        "商品": "冰拿铁",
        "状态": "制作中",
        "取餐号": "18",
    }
}


def query_order(order_id):
    """工具：输入订单号，返回订单资料。"""
    order = orders.get(order_id)

    # B9999 不在 orders 里时，order 的值是 None。
    if order is None:
        return {
            "found": False,
            "message": "没有找到这个订单。",
        }

    # A1001 进来时，返回的值大致是：
    # {"found": True, "商品": "冰拿铁", "状态": "制作中", "取餐号": "18"}。
    return {
        "found": True,
        "商品": order["商品"],
        "状态": order["状态"],
        "取餐号": order["取餐号"],
    }


# 现在模拟用户提供了订单号。把 A1001 改成 B9999，可以测试“查不到”的结果。
user_order_id = "A1001"

# 这一行就是调用工具：把 "A1001" 交给 query_order()，结果放进 result。
result = query_order(user_order_id)

print("用户订单号：", user_order_id)
print("工具返回：", result)

# workflow 在这里是固定的：查到订单就显示状态，查不到就显示工具给的失败原因。
if result["found"]:
    print(f"给用户：您的{result['商品']}正在{result['状态']}，取餐号是 {result['取餐号']}。")
else:
    print("给用户：", result["message"])
