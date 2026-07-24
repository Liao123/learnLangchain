"""第 43 课：相同问题第二次出现时，复用第一次的检索结果。"""

import sys
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

# 这是前面已学过的：读取索引、加载 BGE、检索完整父章节。
# 本课新学的缓存逻辑会直接写在下面。
from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


MIN_RELEVANCE_SCORE = 0.50

# 这三轮会依次执行。第 1 轮和第 3 轮的字符串完全一样。
questions = [
    "周末几点营业？",
    "普通会员消费有什么积分？",
    "周末几点营业？",
]

# retrieval_cache 是一个空字典。键是问题字符串，值是这个问题以前检索得到的 result。
# 刚启动时实际值是：{}。
retrieval_cache = {}

# 两个计数器只为演示效果：后面验证第 3 轮确实没有调用 BGE。
bge_retrieval_count = 0
cache_hit_count = 0

# 索引和 BGE 模型只加载一次，三轮问题共同使用。
index_data = load_parent_child_index()
print("正在加载 BGE 向量模型...")
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])


# ==================== 依次处理三轮问题 ====================

# 第一次循环：question = "周末几点营业？"
# 第二次循环：question = "普通会员消费有什么积分？"
# 第三次循环：question = "周末几点营业？"，与第一次完全相同。
for round_number, question in enumerate(questions, start=1):
    print(f"\n{'=' * 16} 第 {round_number} 轮 {'=' * 16}")
    print("用户问题：", question)
    print("当前缓存键：", list(retrieval_cache.keys()))

    # in 的意思是“这个字符串是否已经是字典中的键”。
    # 第 1 轮："周末几点营业？" in {} 是 False。
    # 第 3 轮："周末几点营业？" in {"周末几点营业？": result_1, ...} 是 True。
    if question in retrieval_cache:
        # 缓存命中：直接取以前存好的 result，不调用 retrieve_parent_context()。
        result = retrieval_cache[question]
        cache_hit_count += 1
        source = "缓存"

    else:
        # 缓存未命中：现在才调用 BGE 检索。
        result = retrieve_parent_context(
            question,
            index_data,
            embedding_model,
            top_k=3,
            min_relevance_score=MIN_RELEVANCE_SCORE,
        )

        # 把这次完整 result 存起来。
        # 第 1 轮后字典大致是：{"周末几点营业？": result_1}。
        retrieval_cache[question] = result
        bge_retrieval_count += 1
        source = "本轮 BGE 检索"

    # result["parents"] 是完整父章节列表。
    # 第 1、3 轮大致都是 [{"parent_id": "parent_4", "title": "营业时间与到店服务", ...}]。
    parent_titles = []
    for parent in result["parents"]:
        parent_titles.append(parent["title"])

    print("资料来源：", source)
    print("找回完整章节：", parent_titles)


# ==================== 最后看缓存是否真的减少检索 ====================

print("\n测试总结：")
print(f"三轮提问次数：{len(questions)}")
print(f"BGE 实际检索次数：{bge_retrieval_count}")
print(f"缓存命中次数：{cache_hit_count}")
print("最终缓存键：", list(retrieval_cache.keys()))


# 本课重点：缓存只复用相同问题以前的检索结果。
# 它不改知识库原文，也不缓存 DeepSeek 的最终回答。
