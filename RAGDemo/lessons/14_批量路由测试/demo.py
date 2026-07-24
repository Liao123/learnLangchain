"""第 42 课：把多道固定题放进列表，批量检查路由结果。"""

import sys
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

# 这两个函数来自第 40、41 课已经学过的路由逻辑。
# 本课不再展开关键词循环，只学习“把单题检查重复跑多次”。
from 检索核心.rag_core import choose_route_action, match_knowledge_base_routes


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

# test_cases 是“测试题列表”。外层 [] 表示列表，里面每个 {} 是一道题的资料包。
# 第 1 项的真实值是：
# {"name": "周末营业时间", "question": "周末几点营业？",
#  "expected_routes": ["到店服务"], "expected_action": "single_route"}
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

# 一开始还没有任何题通过。
total_passed = 0

# len(test_cases) 计算列表里有几道题。当前实际值是 4。
total_count = len(test_cases)


# ==================== 唯一的新循环：一题一题检查 ====================

# 第一次循环时，test_case 就是 test_cases[0]，也就是“周末几点营业？”那一项。
# 第二次循环时，test_case 变成 test_cases[1]，也就是“普通会员消费有什么积分？”。
for test_case in test_cases:
    question = test_case["question"]

    # 调用旧的路由逻辑。第 1 题时实际会找到“到店服务”。
    matched_routes = match_knowledge_base_routes(question, knowledge_base_routes)

    # 从复杂的 matched_routes 中只拿路由名字，方便和预期值比较。
    # 第 1 题后 actual_route_names 的实际值是：["到店服务"]。
    actual_route_names = []
    for matched_route in matched_routes:
        actual_route_names.append(matched_route["route_name"])

    # 第 1、2 题实际动作是 "single_route"；第 3 题是 "reject"；第 4 题是 "multi_route_fallback"。
    actual_action = choose_route_action(matched_routes)

    # == 比较左右是否完全相同。每一道题都有自己的预期值。
    route_passed = actual_route_names == test_case["expected_routes"]
    action_passed = actual_action == test_case["expected_action"]

    # 一道题的路由和动作都正确，才算这题通过。
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


# ==================== 最后只看总数 ====================

print(f"\n测试总结：{total_passed}/{total_count} 题通过")
if total_passed == total_count:
    print("所有路由和回退动作都符合当前预期。")
else:
    print("有题失败：先看那题的预期值和实际值，再决定改关键词还是改预期。")


# 本课重点：批量测试不是新的路由算法，只是把第 41 课的单题比较重复执行多次。
