"""父子知识库的相似度阈值示例：不相关时不调用大模型。"""

import sys
from pathlib import Path


# 复用 app/rag_core.py 中的索引加载和父子检索函数。
RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 只有最高命中片段达到此分数，才允许把检索内容交给聊天模型回答。
MIN_RELEVANCE_SCORE = 0.50
# 索引和模型只加载一次；连续提问时无需重复读取文件或加载模型。
index_data = load_parent_child_index()
embedding_model, _ = load_embedding_model(index_data["embedding_model"])

while True:
    # strip() 会去掉首尾空白，避免只输入空格时触发一次无意义检索。
    question = input("\n你：").strip()
    # 提供英文和中文退出词，便于在终端中结束循环。
    if question.lower() in ("exit", "quit", "退出"):
        break
    if not question:
        continue

    # 检索函数先取得 top_k 子片段，再过滤掉低于阈值的命中。
    result = retrieve_parent_context(
        question,
        index_data,
        embedding_model,
        min_relevance_score=MIN_RELEVANCE_SCORE,
    )
    print(f"最高相似度：{result['best_score']:.4f}")

    # parents 为空说明没有子片段通过阈值，RAG 在这里提前拒答。
    if not result["parents"]:
        print("低于阈值：本次不找回父章节，也不调用 DeepSeek。")
        continue

    # 实际应用中，下一步应将 result["context"] 连同用户问题发送给聊天模型。
    print("通过阈值：可以把这些父章节交给 DeepSeek。")
    for parent in result["parents"]:
        # 按父章节而非子片段展示，避免同一章节被多个相邻命中重复列出。
        print("-", parent["title"])
