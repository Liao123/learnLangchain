"""第 40 课归档：先判断查哪个主题，再在允许范围内检索。"""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util


index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："

question = "周末几点营业？"
min_relevance_score = 0.50

# 两个逻辑知识库共用当前父子索引，但每个主题只允许检索自己的 parent_id。
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


# ==================== 读取全部资料 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)
parents_by_id = {}
for parent in index_data["parents"]:
    parents_by_id[parent["parent_id"]] = parent


# ==================== 第一步：路由 ====================

matched_routes = []
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

if not matched_routes:
    print("用户问题：", question)
    print("路由结果：没有命中任何知识库主题。")
    print("本轮不做 BGE 检索，应该拒答或转人工。")
    raise SystemExit


# ==================== 第二步：只留下路由允许的子片段 ====================

allowed_parent_ids = set()
for matched_route in matched_routes:
    allowed_parent_ids.update(matched_route["parent_ids"])

allowed_child_indices = []
for child_index in range(len(children)):
    if children[child_index]["parent_id"] in allowed_parent_ids:
        allowed_child_indices.append(child_index)

routed_children = []
for child_index in allowed_child_indices:
    routed_children.append(children[child_index])

# 默认题的 allowed_child_indices 是 [7, 8]，所以只保留 child_8、child_9 和对应两行向量。
# 这会把原来的 (9, 512) 子片段向量表，缩小成大致 (2, 512) 的向量表。
routed_child_embeddings = child_embeddings[allowed_child_indices]


# ==================== 第三步：BGE 只检索这个范围 ====================

print("正在加载 BGE 向量模型...")
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

# 默认题成功时，search_results 大致是：
# [{"corpus_id": 0, "score": 0.7...}, {"corpus_id": 1, "score": 0.4...}]。
# 注意这里 corpus_id=0 指的是“路由后列表”的第 1 项，也就是 child_8，不再是全库的第 1 项。

best_score = search_results[0]["score"] if search_results else None
passed_results = []
for search_result in search_results:
    if search_result["score"] >= min_relevance_score:
        passed_results.append(search_result)

# 命中的 child 可能属于同一父章节；用 set() 保证完整父章节只加入一次。
seen_parent_ids = set()
retrieved_parents = []
for passed_result in passed_results:
    child = routed_children[passed_result["corpus_id"]]
    parent_id = child["parent_id"]

    if parent_id not in seen_parent_ids:
        seen_parent_ids.add(parent_id)
        retrieved_parents.append(parents_by_id[parent_id])

context = "\n\n".join(
    f"【{parent['title']}】\n{parent['content']}"
    for parent in retrieved_parents
)


# ==================== 第四步：打印本轮过程 ====================

print("\n用户问题：", question)
print("BGE 模型来源：", model_source)
print("\n路由命中：")
for matched_route in matched_routes:
    print(
        f"- {matched_route['route_name']}，"
        f"命中关键词：{matched_route['matched_keywords']}，"
        f"允许父章节：{matched_route['parent_ids']}"
    )

print("\n本轮允许的父章节 ID：", allowed_parent_ids)
print("本轮允许的子片段：", [child["child_id"] for child in routed_children])
print(f"全库子片段数量：{len(children)}")
print(f"路由后子片段数量：{len(routed_children)}")

if best_score is None:
    print("\n路由范围里没有任何子片段，应该检查路由配置。")
else:
    print(f"\n路由范围内最高相似度：{best_score:.4f}")

if not retrieved_parents:
    print("没有资料通过相似度阈值，本次应该拒答。")
else:
    print("\n最终找回的完整父章节：")
    for parent in retrieved_parents:
        print("-", parent["title"])

    print("\n后续会交给 AI 的资料：")
    print(context)


# 本课重点：路由用关键词先缩小范围，BGE 只在这个范围内检索。
# 无路由命中时停止；有路由命中后仍然用相似度阈值避免乱答。
