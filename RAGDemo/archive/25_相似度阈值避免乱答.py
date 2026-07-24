# json：读取知识库索引 JSON 文件。
import json

# os：读取环境变量中的 DeepSeek API Key。
import os

# Path：定位与当前 Python 文件同目录的索引文件。
from pathlib import Path

# numpy：恢复 JSON 中保存的资料向量。
import numpy as np

# SentenceTransformer：加载 BGE，把问题转换成语义向量。
# util：提供 semantic_search()，比较问题向量和资料向量。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：连接 DeepSeek。
from langchain_openai import ChatOpenAI

# SystemMessage：给 DeepSeek 规则和检索到的资料。
# HumanMessage：用户的实际问题。
from langchain.messages import SystemMessage, HumanMessage


# 22 课生成的索引文件。
index_file = Path(__file__).with_name("咖啡店知识库索引.json")

# BGE 官方建议短问题检索长资料时使用的中文检索提示。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 取最相关的两段资料。
top_k = 2

# 最低相关性分数：低于此值，表示现有知识库没有足够可靠的资料。
# 0.80 只是本课的起点，不是所有项目都正确的固定数字。
# 实际项目应使用真实用户问题反复测试后，再决定这个值。
min_relevance_score = 0.80


# ===== 程序启动时：读取索引、加载 BGE 和 DeepSeek =====

index_text = index_file.read_text(encoding="utf-8")
index_data = json.loads(index_text)

chunks = index_data["chunks"]
document_embeddings = np.array(
    index_data["embeddings"],
    dtype=np.float32,
)

embedding_model = SentenceTransformer(index_data["embedding_model"])

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


print("已加载知识库索引，共", len(chunks), "个资料片段。")
print("相关性低于", min_relevance_score, "时，本程序不会调用 DeepSeek。")
print("输入 exit、quit 或 退出 可结束程序。")


while True:
    question = input("\n你：").strip()

    if not question:
        continue

    if question.lower() in ("exit", "quit", "退出"):
        print("已结束知识库问答。")
        break

    # 1. 将本次用户问题转换成语义向量。
    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )

    # 2. 找到最接近的资料片段。
    search_results = util.semantic_search(
        query_embedding,
        document_embeddings,
        top_k=top_k,
    )[0]

    # search_results 已按相关性从高到低排列。
    # [0] 表示最相关的第一条结果。
    best_score = search_results[0]["score"]

    print(f"\n最高相似度：{best_score:.4f}")

    # 3. 先判断是否真的有足够相关的资料。
    # continue：跳过本轮后面的 DeepSeek 调用，直接回到 while 循环等待下一个问题。
    if best_score < min_relevance_score:
        print("知识库中暂时没有足够相关的资料，本次不会调用 DeepSeek。")
        continue

    # 4. 相关性足够时，才取回原始中文资料。
    retrieved_chunks = []

    print("\n本次交给 DeepSeek 的资料：")

    for result in search_results:
        chunk_index = result["corpus_id"]
        score = result["score"]
        chunk = chunks[chunk_index]

        retrieved_chunks.append(chunk)

        print(f"\n相似度：{score:.4f}")
        print(chunk)

    retrieved_context = "\n\n".join(retrieved_chunks)

    # 5. 只把通过相关性检查的资料交给 DeepSeek。
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


# 本课重点：最相近，不等于足够相关。
# 相似度阈值用于减少“资料不相关却硬回答”的情况。
