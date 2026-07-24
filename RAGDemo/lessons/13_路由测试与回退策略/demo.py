"""第 41 课：用一题固定题，先看懂“预期值和实际值比较”。"""

import sys
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

# 下面三个函数的内部路由循环来自第 40 课。
# 第 41 课不要求你重看循环，重点只看“预期值 -> 实际值 -> 是否通过”。
from rag_core import (
    build_routed_index_data,
    choose_route_action,
    load_embedding_model,
    load_parent_child_index,
    match_knowledge_base_routes,
    retrieve_parent_context,
)


MIN_RELEVANCE_SCORE = 0.50

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

# ==================== 这就是一条测试题的“标准答案” ====================

# 你只先看这一组值：程序应该把这句话送到“到店服务”。
question = "周末几点营业？"
expected_routes = ["到店服务"]
expected_action = "single_route"
expected_parent_id = "parent_4"


# ==================== 第一步：拿到实际路由 ====================

# actual_matched_routes 是第 40 课路由逻辑的实际输出。
# 默认题大致是：[{"route_name": "到店服务", "matched_keywords": ["营业", "周末"], "parent_ids": ["parent_4"]}]。
actual_matched_routes = match_knowledge_base_routes(question, knowledge_base_routes)

# 把复杂结果中最重要的“路由名”拿出来。
# 默认题运行后，actual_route_names 的实际值是：["到店服务"]。
actual_route_names = []
for matched_route in actual_matched_routes:
    actual_route_names.append(matched_route["route_name"])

# 路由数量转换成动作。默认题只有一个路由，所以实际值是 "single_route"。
actual_action = choose_route_action(actual_matched_routes)

# == 的意思是“左右两边完全一样吗”。
# 默认题：["到店服务"] == ["到店服务"]，所以 route_passed 是 True。
route_passed = actual_route_names == expected_routes
action_passed = actual_action == expected_action

print("用户问题：", question)
print("预期路由：", expected_routes)
print("实际路由：", actual_route_names)
print("预期动作：", expected_action)
print("实际动作：", actual_action)


# ==================== 第二步：只有非拒答题才加载 BGE 并检索 ====================

if actual_action == "reject":
    # 改成“维修电脑”练习时会走这里：没有路由，因此不加载 BGE。
    parent_passed = expected_parent_id is None
    print("本题无路由：不加载 BGE，应拒答或转人工。")

else:
    # 第 40 课已学过：把路由允许的 parent_id 换成对应的子片段与向量。
    # 默认题实际返回：allowed_parent_ids = {"parent_4"}，routed_children = [child_8, child_9]。
    routed_index_data, allowed_parent_ids, routed_children = build_routed_index_data(
        load_parent_child_index(),
        actual_matched_routes,
    )

    print("\n正在加载 BGE 向量模型...")
    embedding_model, model_source = load_embedding_model(routed_index_data["embedding_model"])

    # BGE 现在只能在 child_8、child_9 中检索。
    result = retrieve_parent_context(
        question,
        routed_index_data,
        embedding_model,
        top_k=3,
        min_relevance_score=MIN_RELEVANCE_SCORE,
    )

    # 默认题 result["parents"] 大致是 [{"parent_id": "parent_4", ...}]。
    actual_parent_ids = []
    for parent in result["parents"]:
        actual_parent_ids.append(parent["parent_id"])

    # 默认题："parent_4" in ["parent_4"]，所以 parent_passed 是 True。
    # 多路由练习的 expected_parent_id 是 None，本课不要求它固定命中哪一章。
    parent_passed = (
        expected_parent_id is None
        or expected_parent_id in actual_parent_ids
    )

    print("允许父章节：", allowed_parent_ids)
    print("允许子片段：", [child["child_id"] for child in routed_children])
    print("BGE 模型来源：", model_source)
    print("预期父章节：", expected_parent_id)
    print("实际父章节：", actual_parent_ids)


# ==================== 第三步：一眼看测试结果 ====================

# 三项都要是 True，整题才通过。
test_passed = route_passed and action_passed and parent_passed

if test_passed:
    print("\n测试结果：通过")
else:
    print("\n测试结果：失败")
    print("路由检查：", route_passed)
    print("动作检查：", action_passed)
    print("父章节检查：", parent_passed)


# 本课只看一题的预期与实际对比。
# 批量跑很多题、统计通过率，等你看熟这一题后再做。
