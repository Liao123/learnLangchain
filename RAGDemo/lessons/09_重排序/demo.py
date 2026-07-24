"""第 37 课：BGE 先找候选，reranker 再重新排序。"""

import sys
from pathlib import Path


# __file__ 是当前 demo.py 的位置；向上两层得到 RAGDemo 文件夹。
RAG_ROOT = Path(__file__).resolve().parents[2]

# rag_core.py 在 RAGDemo/app 文件夹中，加入搜索路径后才能 import 它。
sys.path.insert(0, str(RAG_ROOT / "app"))

# load_embedding_model：加载 BGE，负责快速找候选资料。
# load_reranker_model：加载 reranker，负责重新判断候选资料谁更贴题。
# rerank_matches：把 BGE 找到的候选片段交给 reranker 后重新排序。
from rag_core import (
    load_embedding_model,
    load_parent_child_index,
    load_reranker_model,
    rerank_matches,
    retrieve_parent_context,
)


# 这题有两个容易混淆的点：“拆封后”和“退款”。
# BGE 会先找 3 段看起来相关的片段，reranker 再判断哪段最直接回答“拆封后”。
question = "咖啡豆拆封后还能退款吗？"

# 读取知识库和已经算好的资料向量。
index_data = load_parent_child_index()

print("正在加载 BGE 向量模型...")
# BGE 只负责快速召回候选，不负责最终精细排序。
embedding_model, embedding_source = load_embedding_model(index_data["embedding_model"])

print("正在加载 reranker 模型...")
# reranker 是另一种模型。它会同时看“问题 + 一段资料”，直接判断这一对是否贴题。
reranker_model, reranker_source = load_reranker_model()

# 第一步：BGE 从全部子片段中快速找最像的 3 段。
# 本例没有设阈值，目的是把 3 个候选都展示出来给你比较。
result = retrieve_parent_context(
    question,
    index_data,
    embedding_model,
    top_k=3,
)

# result["matched_children"] 是 BGE 找到的候选片段列表。
# 例如其中一项大致像：{"score": 0.8, "child": {"child_id": "child_2", ...}}。
# 这里的 0.8 只是示例；真实 BGE 分数要以运行后的终端输出为准。

# 第二步：把同一个问题和每个候选片段配成一对，交给 reranker 重新打分。
reranked_matches = rerank_matches(
    question,
    result["matched_children"],
    reranker_model,
)

# reranked_matches 还是一个列表，但每项多了 rerank_score。
# 其中一项大致像：{"score": 0.76, "child": {...}, "rerank_score": 3.12}。
# rerank_score 是另一种模型的分数，只用来决定 reranker 这一列里的先后顺序。

print("\n用户问题：", question)
print("BGE 模型来源：", embedding_source)
print("reranker 模型来源：", reranker_source)

print("\nBGE 初始排序：")
# enumerate(..., start=1) 会在遍历列表时同时给出 1、2、3 这样的显示序号。
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

# 注意：BGE 分数和 reranker 分数来自不同模型，不能直接比较大小。
# 只看同一列内部的排序：BGE 列看 BGE 排序，reranker 列看 reranker 排序。
