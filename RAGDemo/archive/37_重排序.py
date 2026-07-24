# Path：定位当前脚本同目录中的父子知识库索引。
from pathlib import Path

# json：读取父子索引和元数据 JSON。
import json

# numpy：把 JSON 里的向量列表还原为 NumPy 数组。
import numpy as np

# SentenceTransformer：加载 BGE 向量模型，快速找候选资料。
# CrossEncoder：加载 reranker，同时阅读“问题 + 候选片段”后直接给相关性分数。
# util：提供 semantic_search()，用于 BGE 的初步检索。
from sentence_transformers import CrossEncoder, SentenceTransformer, util


index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："
reranker_model_name = "BAAI/bge-reranker-base"

# 这题能让多个退款片段进入候选，便于观察 reranker 如何重新排列它们。
question = "咖啡豆拆封后还能退款吗？"
top_k = 3


# ==================== 程序启动时只执行一次 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)

print("正在加载 BGE 向量模型...")
embedding_model = SentenceTransformer(index_data["embedding_model"])
print("正在加载 reranker 模型...")
reranker_model = CrossEncoder(reranker_model_name)


# ==================== 第一步：BGE 快速找候选 ====================

query_embedding = embedding_model.encode(
    [query_instruction + question],
    normalize_embeddings=True,
)
search_results = util.semantic_search(
    query_embedding,
    child_embeddings,
    top_k=top_k,
)[0]

matches = []
for result in search_results:
    child = children[result["corpus_id"]]
    matches.append({
        "score": result["score"],
        "child": child,
    })


# ==================== 第二步：reranker 重新排序 ====================

# pairs 里每一项都是“同一个问题 + 一个候选片段”。
pairs = []
for match in matches:
    pairs.append([question, match["child"]["content"]])

# predict() 一次给所有 pairs 打分。这里的分数只用于 reranker 自己的排序。
rerank_scores = reranker_model.predict(pairs)
reranked_matches = []

for position in range(len(matches)):
    reranked_matches.append({
        "score": matches[position]["score"],
        "child": matches[position]["child"],
        "rerank_score": float(rerank_scores[position]),
    })

# key=lambda ... 表示按 rerank_score 排序；reverse=True 表示高分在前。
reranked_matches.sort(
    key=lambda match: match["rerank_score"],
    reverse=True,
)


# ==================== 输出前后排序 ====================

print("\n用户问题：", question)
print("\nBGE 初始排序：")
for position, match in enumerate(matches, start=1):
    print(f"{position}. {match['child']['child_id']}，BGE 分数：{match['score']:.4f}")
    print("   ", match["child"]["content"])

print("\nreranker 重排序后：")
for position, match in enumerate(reranked_matches, start=1):
    print(
        f"{position}. {match['child']['child_id']}，"
        f"BGE 分数：{match['score']:.4f}，"
        f"reranker 分数：{match['rerank_score']:.4f}"
    )
    print("   ", match["child"]["content"])


# 本课重点：
# 1. BGE 先快速度召回 top_k 候选，reranker 不需要看全部资料。
# 2. reranker 逐条精读问题和候选片段，给出新的排序。
# 3. 重排序只能优化候选顺序，不能替代相似度阈值处理知识库外的问题。
