"""第 41 课归档：用一题固定题，先看懂“预期值和实际值比较”。"""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util


index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："
min_relevance_score = 0.50

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

# 一条测试题的预期值。
question = "周末几点营业？"
expected_routes = ["到店服务"]
expected_action = "single_route"
expected_parent_id = "parent_4"


# ==================== 第一步：实际路由 ====================

actual_matched_routes = []
for route_name, route in knowledge_base_routes.items():
    matched_keywords = []
    for keyword in route["keywords"]:
        if keyword in question:
            matched_keywords.append(keyword)

    if matched_keywords:
        actual_matched_routes.append({
            "route_name": route_name,
            "matched_keywords": matched_keywords,
            "parent_ids": route["parent_ids"],
        })

# 默认题的 actual_matched_routes 大致是：[{"route_name": "到店服务", ...}]。
actual_route_names = []
for matched_route in actual_matched_routes:
    actual_route_names.append(matched_route["route_name"])

if len(actual_matched_routes) == 0:
    actual_action = "reject"
elif len(actual_matched_routes) == 1:
    actual_action = "single_route"
else:
    actual_action = "multi_route_fallback"

route_passed = actual_route_names == expected_routes
action_passed = actual_action == expected_action

print("用户问题：", question)
print("预期路由：", expected_routes)
print("实际路由：", actual_route_names)
print("预期动作：", expected_action)
print("实际动作：", actual_action)


# ==================== 第二步：非拒答题才检索 ====================

if actual_action == "reject":
    parent_passed = expected_parent_id is None
    print("本题无路由：不加载 BGE，应拒答或转人工。")

else:
    index_data = json.loads(index_file.read_text(encoding="utf-8"))
    children = index_data["children"]
    child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)
    parents_by_id = {}
    for parent in index_data["parents"]:
        parents_by_id[parent["parent_id"]] = parent

    # 默认题最后得到 allowed_parent_ids = {"parent_4"}，allowed_child_indices = [7, 8]。
    allowed_parent_ids = set()
    for matched_route in actual_matched_routes:
        allowed_parent_ids.update(matched_route["parent_ids"])

    allowed_child_indices = []
    for child_index in range(len(children)):
        if children[child_index]["parent_id"] in allowed_parent_ids:
            allowed_child_indices.append(child_index)

    routed_children = []
    for child_index in allowed_child_indices:
        routed_children.append(children[child_index])
    routed_child_embeddings = child_embeddings[allowed_child_indices]

    print("\n正在加载 BGE 向量模型...")
    try:
        embedding_model = SentenceTransformer(
            index_data["embedding_model"],
            local_files_only=True,
        )
        model_source = f"{index_data['embedding_model']}（本地缓存）"
    except OSError:
        embedding_model = SentenceTransformer(index_data["embedding_model"])
        model_source = index_data["embedding_model"]

    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )
    search_results = util.semantic_search(
        query_embedding,
        routed_child_embeddings,
        top_k=min(3, len(routed_children)),
    )[0]

    actual_parent_ids = []
    seen_parent_ids = set()
    for search_result in search_results:
        if search_result["score"] < min_relevance_score:
            continue

        child = routed_children[search_result["corpus_id"]]
        parent_id = child["parent_id"]
        if parent_id not in seen_parent_ids:
            seen_parent_ids.add(parent_id)
            actual_parent_ids.append(parent_id)

    parent_passed = (
        expected_parent_id is None
        or expected_parent_id in actual_parent_ids
    )

    print("允许父章节：", allowed_parent_ids)
    print("允许子片段：", [child["child_id"] for child in routed_children])
    print("BGE 模型来源：", model_source)
    print("预期父章节：", expected_parent_id)
    print("实际父章节：", actual_parent_ids)


# ==================== 第三步：测试结果 ====================

test_passed = route_passed and action_passed and parent_passed
if test_passed:
    print("\n测试结果：通过")
else:
    print("\n测试结果：失败")
    print("路由检查：", route_passed)
    print("动作检查：", action_passed)
    print("父章节检查：", parent_passed)


# 本课只测一题。看清“预期值和实际值”后，再扩展成批量测试。
