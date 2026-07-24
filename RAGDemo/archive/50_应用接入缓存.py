"""第 50 课归档：在真实 RAG 检索前使用缓存，命中时跳过 BGE。"""

import json
import time
from collections import OrderedDict
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util


class RetrievalCache:
    def __init__(self, max_size, ttl_seconds):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.entries = OrderedDict()

    def make_key(self, user_role, knowledge_base_version, question):
        return f"{user_role}:{knowledge_base_version}:{question}"

    def get(self, cache_key, current_time):
        entry = self.entries.get(cache_key)
        if entry is None:
            return None
        if current_time - entry["saved_at"] > self.ttl_seconds:
            del self.entries[cache_key]
            return None
        self.entries.move_to_end(cache_key)
        return entry["result"]

    def set(self, cache_key, result, current_time):
        self.entries[cache_key] = {"result": result, "saved_at": current_time}
        self.entries.move_to_end(cache_key)
        if len(self.entries) > self.max_size:
            self.entries.popitem(last=False)

    def keys(self):
        return list(self.entries.keys())


index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："
top_k = 3
min_relevance_score = 0.50
user_role = "public_customer"
knowledge_base_version = "coffee-kb-v1-top3-threshold050"
questions = ["周末几点营业？", "周末几点营业？"]


# ==================== 读取知识库和 BGE ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)
parents_by_id = {}
for parent in index_data["parents"]:
    parents_by_id[parent["parent_id"]] = parent

print("正在加载 BGE 向量模型...")
try:
    embedding_model = SentenceTransformer(index_data["embedding_model"], local_files_only=True)
    model_source = f"{index_data['embedding_model']}（本地缓存）"
except OSError:
    embedding_model = SentenceTransformer(index_data["embedding_model"])
    model_source = index_data["embedding_model"]
print("BGE 模型来源：", model_source)

cache = RetrievalCache(max_size=10, ttl_seconds=300)
bge_retrieval_count = 0
cache_hit_count = 0


# ==================== 两次相同问题 ====================

for round_number, question in enumerate(questions, start=1):
    cache_key = cache.make_key(user_role, knowledge_base_version, question)
    current_time = int(time.time())
    result = cache.get(cache_key, current_time)

    print(f"\n第 {round_number} 次问题：", question)
    print("缓存 key：", cache_key)

    if result is None:
        # 第 1 次：BGE 真正比较问题向量和全部 child 向量。
        query_embedding = embedding_model.encode(
            [query_instruction + question],
            normalize_embeddings=True,
        )
        search_results = util.semantic_search(query_embedding, child_embeddings, top_k=top_k)[0]

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
        cache.set(cache_key, result, current_time)
        bge_retrieval_count += 1
        source = "BGE 检索（已存缓存）"
    else:
        # 第 2 次：直接拿第 1 次保存的 result。
        cache_hit_count += 1
        source = "缓存（跳过 BGE）"

    parent_titles = []
    for parent in result["parents"]:
        parent_titles.append(parent["title"])

    print("本轮来源：", source)
    print("找回完整章节：", parent_titles)


print("\n测试总结：")
print("BGE 实际检索次数：", bge_retrieval_count)
print("缓存命中次数：", cache_hit_count)
print("当前缓存 key：", cache.keys())


# 本课重点：缓存命中时跳过 BGE，但后续仍能拿到完整 result。
