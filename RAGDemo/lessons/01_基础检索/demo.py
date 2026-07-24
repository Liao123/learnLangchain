"""最小语义检索示例：只验证检索，不调用聊天模型。"""

import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import util


# lesson 文件位于 lessons/01_基础检索；向上两层就是 RAGDemo 根目录。
RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from rag_core import QUERY_INSTRUCTION, load_embedding_model


# 索引中保存了切分后的文本、每段文本的向量，以及构建索引时使用的模型名称。
index_file = RAG_ROOT / "data" / "indexes" / "咖啡店知识库索引.json"
index_data = json.loads(index_file.read_text(encoding="utf-8"))
# 优先使用项目 models/ 下已下载的模型；本地不存在时，才按索引中的名称加载。
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])

# 修改这个问题后重新运行，可以观察语义检索会找回哪些片段。
question = "我买的咖啡豆还没拆封，五天前买的，可以退吗？"
# BGE 检索模型要求查询前加指令；归一化后，向量点积等价于余弦相似度。
query_embedding = embedding_model.encode(
    [QUERY_INSTRUCTION + question],
    normalize_embeddings=True,
)
# JSON 文件中的向量是普通列表，转换为 float32 的 NumPy 数组后才能高效计算相似度。
document_embeddings = np.array(index_data["embeddings"], dtype=np.float32)
# semantic_search 返回每个命中片段的编号 corpus_id 和相似度 score。
results = util.semantic_search(query_embedding, document_embeddings, top_k=2)[0]

print("BGE 模型来源：", model_source)
print("\n问题：", question)
for result in results:
    print(f"\n相似度：{result['score']:.4f}")
    # corpus_id 与 chunks 列表的下标对应，因此能取回原始文本。
    print(index_data["chunks"][result["corpus_id"]])
