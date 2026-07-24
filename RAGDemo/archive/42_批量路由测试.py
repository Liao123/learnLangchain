"""第 42 课归档：把多道固定题放进列表，批量检查路由结果。"""

# 第 42 课只测试路由，不需要模型、BGE 向量或 DeepSeek。

knowledge_base_routes = {
    "会员与订单": {
        "keywords": ["会员", "积分", "优惠", "退款", "订单", "咖啡豆", "饮品"],
        "parent_ids": ["parent_1", "parent_2", "parent_3"],
    },
    "到店服务": {
        "keywords": ["营业", "周末", "周六", "周日", "打烊", "预订", "到店", "门店"],
        "parent_ids": ["parent_4"],
    },
}

# 每个 {} 是一道题。当前一共 4 道题。
test_cases = [
    {
        "name": "周末营业时间",
        "question": "周末几点营业？",
        "expected_routes": ["到店服务"],
        "expected_action": "single_route",
    },
    {
        "name": "普通会员积分",
        "question": "普通会员消费有什么积分？",
        "expected_routes": ["会员与订单"],
        "expected_action": "single_route",
    },
    {
        "name": "知识库外问题",
        "question": "店里能维修电脑吗？",
        "expected_routes": [],
        "expected_action": "reject",
    },
    {
        "name": "多个主题同时命中",
        "question": "门店会员有什么优惠？",
        "expected_routes": ["会员与订单", "到店服务"],
        "expected_action": "multi_route_fallback",
    },
]

total_passed = 0
total_count = len(test_cases)  # 实际值是 4。


# 这个 for 是本课唯一的新重点：把单题检查重复跑 4 次。
for test_case in test_cases:
    question = test_case["question"]
    matched_routes = []

    # 第 40 课学过的关键词路由：字符串命中 -> 路由名 + parent_id。
    for route_name, route in knowledge_base_routes.items():
        matched_keywords = []
        for keyword in route["keywords"]:
            if keyword in question:
                matched_keywords.append(keyword)

        if matched_keywords:
            matched_routes.append({
                "route_name": route_name,
                "matched_keywords": matched_keywords,
                "parent_ids": route["parent_ids"],
            })

    actual_route_names = []
    for matched_route in matched_routes:
        actual_route_names.append(matched_route["route_name"])

    if len(matched_routes) == 0:
        actual_action = "reject"
    elif len(matched_routes) == 1:
        actual_action = "single_route"
    else:
        actual_action = "multi_route_fallback"

    route_passed = actual_route_names == test_case["expected_routes"]
    action_passed = actual_action == test_case["expected_action"]
    case_passed = route_passed and action_passed

    print(f"\n【{test_case['name']}】")
    print("问题：", question)
    print("预期路由：", test_case["expected_routes"])
    print("实际路由：", actual_route_names)
    print("预期动作：", test_case["expected_action"])
    print("实际动作：", actual_action)

    if case_passed:
        total_passed += 1
        print("测试结果：通过")
    else:
        print("测试结果：失败")
        print("路由检查：", route_passed)
        print("动作检查：", action_passed)


print(f"\n测试总结：{total_passed}/{total_count} 题通过")
if total_passed == total_count:
    print("所有路由和回退动作都符合当前预期。")
else:
    print("有题失败：先看那题的预期值和实际值，再决定改关键词还是改预期。")


# 本课重点：批量测试 = 多道测试数据 + 一个重复执行单题检查的 for 循环。
