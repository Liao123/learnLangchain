"""查看 BGE 初排和 reranker 重排序差异的应用示例。"""

import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(APP_DIR))

from 检索核心.rag_core import (
    load_embedding_model,
    load_parent_child_index,
    load_reranker_model,
    rerank_matches,
    retrieve_parent_context,
)


question = "咖啡豆拆封后还能退款吗？"

index_data = load_parent_child_index()
print("正在加载 BGE 向量模型...")
embedding_model, embedding_source = load_embedding_model(index_data["embedding_model"])
print("正在加载 reranker 模型...")
reranker_model, reranker_source = load_reranker_model()

# 先让 BGE 快速找 3 个候选片段。本例暂不设阈值，方便看到全部候选和排序变化。
result = retrieve_parent_context(
    question,
    index_data,
    embedding_model,
    top_k=3,
)

# 再让 reranker 逐条比较“问题 + 候选片段”，得到新的排序。
reranked_matches = rerank_matches(question, result["matched_children"], reranker_model)

print("\n用户问题：", question)
print("BGE 模型来源：", embedding_source)
print("reranker 模型来源：", reranker_source)

print("\nBGE 初始排序：")
for position, match in enumerate(result["matched_children"], start=1):
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
