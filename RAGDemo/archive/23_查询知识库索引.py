# json：Python 自带模块，用来读取 JSON 索引文件。
import json

# os：用来读取环境变量中的 DeepSeek API Key。
import os

# Path：更可靠地处理“与当前 Python 文件同一个文件夹”的路径。
from pathlib import Path

# numpy：把 JSON 中保存的数字列表重新转换成适合语义检索的数组。
import numpy as np

# SentenceTransformer：加载 BGE 嵌入模型，把用户问题转换成语义向量。
# util：提供 semantic_search()，负责比较问题向量和已保存的资料向量。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：连接 DeepSeek 聊天模型。
from langchain_openai import ChatOpenAI

# SystemMessage：给 DeepSeek 规则和检索资料。
# HumanMessage：用户的自然语言问题。
from langchain.messages import SystemMessage, HumanMessage


# 找到与当前 Python 文件同目录的索引文件。
# 这个文件由 22_构建知识库索引.py 生成。
index_file = Path(__file__).with_name("咖啡店知识库索引.json")

# BGE 官方建议短问题检索长资料时使用的中文检索提示。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 每次取最相关的前几段资料。
top_k = 2


# 第一步：读取已经保存的索引 JSON 文件。
# read_text()：读取文件中的全部文字。
index_text = index_file.read_text(encoding="utf-8")

# json.loads()：把 JSON 文字转换回 Python 字典。
index_data = json.loads(index_text)


# 从索引中取回构建时保存的信息。
embedding_model_name = index_data["embedding_model"]
chunks = index_data["chunks"]

# np.array()：把 JSON 的嵌套数字列表转换成 NumPy 数组。
# 这样 semantic_search() 可以高效比较问题向量和资料向量。
# document_embeddings = np.array(index_data["embeddings"])
document_embeddings = np.array(
    index_data["embeddings"],
    dtype=np.float32,
)

print("已读取索引：", index_file.name)
print("索引来自：", index_data["source_file"])
print("索引中有", len(chunks), "个资料片段。")


# 第二步：加载与索引构建时相同的 BGE 模型。
# 因为模型文件已经下载过，本机通常会直接从缓存加载。
embedding_model = SentenceTransformer(embedding_model_name)


# 第三步：这里只转换“本次用户问题”的向量。
# 注意：没有再次对 chunks 调用 encode()，因为资料向量已经保存在索引文件中。
question = "我周日晚上八点半去店里，还营业吗？"

query_embedding = embedding_model.encode(
    [query_instruction + question],
    normalize_embeddings=True,
)


# 第四步：将问题向量与“从索引读取的资料向量”比较，取最相关的 top_k 段。
# [0] 表示：我们只有一个问题，所以取这个问题的检索结果。
search_results = util.semantic_search(
    query_embedding,
    document_embeddings,
    top_k=top_k,
)[0]


# 第五步：根据 corpus_id 从 chunks 中取回原始中文资料。
retrieved_chunks = []

print("\n用户问题：", question)
print("\n检索到的资料：")

for result in search_results:
    chunk_index = result["corpus_id"]
    score = result["score"]
    chunk = chunks[chunk_index]

    retrieved_chunks.append(chunk)

    print(f"\n相似度：{score:.4f}")
    print(chunk)


# join()：将多段检索资料合并成一段文字，供 DeepSeek 阅读。
retrieved_context = "\n\n".join(retrieved_chunks)


# 第六步：DeepSeek 只根据检索出的少量资料，用自然语言回答。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

system_message = SystemMessage(
    content=f"""
你是星光咖啡店客服。
只能依据 <检索资料> 中的内容回答，不能补充资料中没有的信息。
如果资料无法回答，请明确说：资料中暂时没有这项信息。
回答要简短、自然。

<检索资料>
{retrieved_context}
</检索资料>
"""
)

response = model.invoke([
    system_message,
    HumanMessage(content=question),
])

print("\nDeepSeek 最终回答：")
print(response.content)


# 本程序每次提问会做的事：
# 读取索引 → 问题向量化 → 语义检索 → 取回原始中文资料 → DeepSeek 回答。
# 它不会重新切知识库，也不会重新生成所有资料片段的向量。
