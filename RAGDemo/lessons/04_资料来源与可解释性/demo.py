"""资料来源示例：显示本轮检索实际采用了哪些知识库片段。"""

import sys
from pathlib import Path


# 从课程目录定位到 RAGDemo 根目录，再导入公共检索逻辑。
RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from 检索核心.rag_core import (
    build_source_records,
    load_embedding_model,
    load_parent_child_index,
    retrieve_parent_context,
)


# 只有通过阈值的命中才会成为资料来源，避免展示无关的“凑数”片段。
MIN_RELEVANCE_SCORE = 0.50
question = "金卡会员有什么福利？"

index_data = load_parent_child_index()
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
result = retrieve_parent_context(
    question,
    index_data,
    embedding_model,
    min_relevance_score=MIN_RELEVANCE_SCORE,
)

print("BGE 模型来源：", model_source)
print("\n问题：", question)
print(f"最高子片段相似度：{result['best_score']:.4f}")

# 这里不调用 DeepSeek；先确认能否把“回答依据”从检索结果中准确整理出来。
sources = build_source_records(result, index_data)
if not sources:
    print("\n没有通过阈值的资料来源，本次不应生成知识库回答。")

else:
    print("\n本轮回答可引用的资料来源：")
    for source in sources:
        print(
            "- "
            f"{source['document_title']} > {source['chapter_title']} "
            f"（{source['child_id']}，相似度 {source['score']:.4f}）"
        )

    print("\n找回的完整父章节：")
    print(result["context"])