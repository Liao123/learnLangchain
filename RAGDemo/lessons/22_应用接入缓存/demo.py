"""第 50 课：在真实 RAG 检索前使用缓存，命中时跳过 BGE。"""

import sys
import time
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context
from 检索核心.retrieval_cache import RetrievalCache


TOP_K = 3
MIN_RELEVANCE_SCORE = 0.50
USER_ROLE = "public_customer"
KNOWLEDGE_BASE_VERSION = "coffee-kb-v1-top3-threshold050"

# 两项完全相同，才能让第二次使用第一次的缓存。
questions = ["周末几点营业？", "周末几点营业？"]

# 缓存对象已经封装了权限 key、TTL 和容量规则。
cache = RetrievalCache(max_size=10, ttl_seconds=300)

index_data = load_parent_child_index()
print("正在加载 BGE 向量模型...")
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
print("BGE 模型来源：", model_source)

bge_retrieval_count = 0
cache_hit_count = 0


# 第一次 question 是“周末几点营业？”，第二次也是相同字符串。
for round_number, question in enumerate(questions, start=1):
    # make_key() 的实际值是："public_customer:coffee-kb-v1-top3-threshold050:周末几点营业？"。
    cache_key = cache.make_key(USER_ROLE, KNOWLEDGE_BASE_VERSION, question)
    current_time = int(time.time())

    # get() 命中时给 result 字典，未命中时给 None。
    result = cache.get(cache_key, current_time)

    print(f"\n第 {round_number} 次问题：", question)
    print("缓存 key：", cache_key)

    if result is None:
        # 第 1 次会走这里：真正调用 BGE 检索。
        result = retrieve_parent_context(
            question,
            index_data,
            embedding_model,
            top_k=TOP_K,
            min_relevance_score=MIN_RELEVANCE_SCORE,
        )
        cache.set(cache_key, result, current_time)
        bge_retrieval_count += 1
        source = "BGE 检索（已存缓存）"
    else:
        # 第 2 次会走这里：result 来自第一次保存的数据，不调用 retrieve_parent_context()。
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


# 本课重点：命中缓存时，后续代码拿到的仍是完整 result，只是少做了一次 BGE 检索。
