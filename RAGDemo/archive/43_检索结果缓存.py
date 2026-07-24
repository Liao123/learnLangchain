"""第 43 课归档：相同问题第二次出现时，复用第一次的检索结果。"""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util


index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："
min_relevance_score = 0.50

# 第 1、3 轮完全相同，第三轮应该命中缓存。
questions = [
    "周末几点营业？",
    "普通会员消费有什么积分？",
    "周末几点营业？",
]

# 空字典：问题字符串 -> 以前检索得到的结果包。
retrieval_cache = {}
bge_retrieval_count = 0
cache_hit_count = 0


# ==================== 读取索引和模型 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)
parents_by_id = {}
for parent in index_data["parents"]:
    parents_by_id[parent["parent_id"]] = parent

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


# ==================== 三轮提问：先看缓存，再决定是否检索 ====================

for round_number, question in enumerate(questions, start=1):
    print(f"\n{'=' * 16} 第 {round_number} 轮 {'=' * 16}")
    print("用户问题：", question)
    print("当前缓存键：", list(retrieval_cache.keys()))

    if question in retrieval_cache:
        # 第 3 轮会走这里，result 直接等于第 1 轮已经存好的结果包。
        result = retrieval_cache[question]
        cache_hit_count += 1
        source = "缓存"

    else:
        # 第 1、2 轮会走这里：问题转向量，再和 9 个 child 向量比较。
        query_embedding = embedding_model.encode(
            [query_instruction + question],
            normalize_embeddings=True,
        )
        search_results = util.semantic_search(
            query_embedding,
            child_embeddings,
            top_k=3,
        )[0]

        passed_results = []
        for search_result in search_results:
            if search_result["score"] >= min_relevance_score:
                passed_results.append(search_result)

        seen_parent_ids = set()
        retrieved_parents = []
        for passed_result in passed_results:
            child = children[passed_result["corpus_id"]]
            parent_id = child["parent_id"]
            if parent_id not in seen_parent_ids:
                seen_parent_ids.add(parent_id)
                retrieved_parents.append(parents_by_id[parent_id])

        result = {"parents": retrieved_parents}
        retrieval_cache[question] = result
        bge_retrieval_count += 1
        source = "本轮 BGE 检索"

    parent_titles = []
    for parent in result["parents"]:
        parent_titles.append(parent["title"])

    print("资料来源：", source)
    print("找回完整章节：", parent_titles)


print("\n测试总结：")
print(f"三轮提问次数：{len(questions)}")
print(f"BGE 实际检索次数：{bge_retrieval_count}")
print(f"缓存命中次数：{cache_hit_count}")
print("最终缓存键：", list(retrieval_cache.keys()))


# 本课重点：同一个字符串第二次出现时，直接复用字典中以前保存的 result。
