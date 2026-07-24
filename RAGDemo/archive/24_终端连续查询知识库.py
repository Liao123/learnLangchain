# json：读取 JSON 索引文件。
import json

# os：读取环境变量中的 DeepSeek API Key。
import os

# Path：定位与当前 Python 文件同目录的索引文件。
from pathlib import Path

# numpy：将 JSON 中保存的资料向量恢复成 NumPy 数组。
import numpy as np

# SentenceTransformer：加载 BGE，把每个用户问题转换成语义向量。
# util：提供 semantic_search()，从已保存的资料向量中找相关片段。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：连接 DeepSeek。
from langchain_openai import ChatOpenAI

# SystemMessage：给 DeepSeek 规则和检索资料。
# HumanMessage：用户的实际问题。
from langchain.messages import SystemMessage, HumanMessage


# 找到 22 课生成的索引文件。
index_file = Path(__file__).with_name("咖啡店知识库索引.json")

# BGE 官方建议短问题检索长资料时使用的中文检索提示。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 每次从索引中取最相关的前两段资料。
top_k = 2


# ===== 程序启动时只执行一次 =====

# 读取索引 JSON，并转换为 Python 字典。
index_text = index_file.read_text(encoding="utf-8")
index_data = json.loads(index_text)

# 从索引取出资料片段和已计算好的资料向量。
chunks = index_data["chunks"]

# dtype=np.float32：确保与 BGE 为用户问题生成的向量类型一致。
document_embeddings = np.array(
    index_data["embeddings"],
    dtype=np.float32,
)

# 加载已经下载过的 BGE 模型。
# 它只在程序启动时加载一次；后面的连续问题会重复使用它。
embedding_model = SentenceTransformer(index_data["embedding_model"])

# 创建 DeepSeek 模型对象，也只需要创建一次。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


print("已加载知识库索引，共", len(chunks), "个资料片段。")
print("现在可以连续提问。输入 exit、quit 或 退出 可结束程序。")


# while True：持续接收多个用户问题，直到遇到 break。
while True:
    # input()：暂停程序，等待用户在终端输入问题。
    # strip()：去掉输入前后多余的空格和换行。
    question = input("\n你：").strip()

    # 空问题没有意义，直接进入下一次循环。
    if not question:
        continue

    # lower()：把英文转换成小写，方便 EXIT、Exit、exit 都能退出。
    # in (...)：判断 question 是否属于这些退出词之一。
    if question.lower() in ("exit", "quit", "退出"):
        print("已结束知识库问答。")
        break

    # ===== 每个用户问题都会执行以下 RAG 查询流程 =====

    # 1. 只把“本次问题”转换成 BGE 语义向量。
    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )

    # 2. 在已保存的资料向量中，找最相关的前 top_k 段。
    search_results = util.semantic_search(
        query_embedding,
        document_embeddings,
        top_k=top_k,
    )[0]

    # 3. 根据检索结果的 corpus_id，取回原始中文资料。
    retrieved_chunks = []

    print("\n本次检索到的资料：")

    for result in search_results:
        chunk_index = result["corpus_id"]
        score = result["score"]
        chunk = chunks[chunk_index]

        retrieved_chunks.append(chunk)

        print(f"\n相似度：{score:.4f}")
        print(chunk)

    # 4. 将多段资料拼成上下文，再交给 DeepSeek 回答。
    retrieved_context = "\n\n".join(retrieved_chunks)

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

    print("\nAI：", response.content)


# ===== 程序结束 =====
