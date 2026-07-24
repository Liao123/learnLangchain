"""父子检索示例：先匹配子片段，再找回完整父章节。"""

import sys
from pathlib import Path


# 将公共 RAG 代码目录加入模块搜索路径，避免在每节课重复实现检索逻辑。
RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 子片段较短，适合做相似度匹配；父章节较完整，适合提供给模型作为回答上下文。
question = "金卡会员有什么福利？"
# 索引包含父章节、子片段及子片段向量；加载函数会额外建立 parent_id 查找表。
index_data = load_parent_child_index()
# 模型名称从索引读取，确保查询向量和构建索引时的向量处于同一语义空间。
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
# 先检索最相关的子片段，再按 parent_id 去重并找回对应的完整父章节。
result = retrieve_parent_context(question, index_data, embedding_model)

print("BGE 模型来源：", model_source)
print("\n问题：", question)
for match in result["matched_children"]:
    # match 同时保留相似度和原子片段，便于查看“为什么”命中这个父章节。
    child = match["child"]
    print(f"\n子片段 {child['child_id']}，相似度：{match['score']:.4f}")
    print("parent_id：", child["parent_id"])
    print(child["content"])

print("\n找回的完整父章节：")
# context 已经按标题和正文拼接，可直接放入后续调用聊天模型的提示词中。
print(result["context"])
