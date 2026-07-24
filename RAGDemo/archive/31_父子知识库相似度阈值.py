# json：读取第 28 课生成的父子知识库索引。
import json

# os：读取环境变量中的 DeepSeek API Key。
import os

# Path：定位与当前程序同目录的索引文件。
from pathlib import Path

# numpy：把 JSON 中保存的子向量还原为 NumPy 数组。
import numpy as np

# SentenceTransformer：把问题转换成 BGE 语义向量。
# util：提供 semantic_search()，用于比较问题和子片段的相似度。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：通过 OpenAI 兼容接口连接 DeepSeek。
from langchain_openai import ChatOpenAI

# SystemMessage：给模型设置资料范围和回答规则。
# HumanMessage：保存用户本轮输入的问题。
from langchain.messages import SystemMessage, HumanMessage


# 第 28 课生成的索引文件。
index_file = Path(__file__).with_name("父子知识库索引.json")

# BGE 官方建议的中文检索提示。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 先取相似度最高的 3 个子片段，再进行相关性判断。
top_k = 3

# 最低相关性分数。
# 0.70 只是本项目的练习起点，不是所有知识库都适用的固定值。
# 应当用真实问题观察分数后，再决定是否提高或降低它。
min_relevance_score = 0.70


# ==================== 程序启动时只执行一次 ====================

# 读取父章节、子片段和子片段向量。
index_data = json.loads(index_file.read_text(encoding="utf-8"))
parents = index_data["parents"]
children = index_data["children"]
child_embeddings = np.array(
    index_data["child_embeddings"],
    dtype=np.float32,
)

# 建立“父章节 ID -> 父章节对象”的查询表。
parents_by_id = {
    parent["parent_id"]: parent
    for parent in parents
}

print("已读取父子索引：", index_file.name)
print("父章节数量：", len(parents))
print("子片段数量：", len(children))
print("子向量数量：", len(child_embeddings))
print("正在加载 BGE 向量模型，首次运行可能需要下载，请耐心等待。")

# 查询向量必须使用和构建索引时相同的模型。
embedding_model = SentenceTransformer(index_data["embedding_model"])

# 未设置 Key 时给出清晰提示，而不是直接抛出 KeyError。
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError(
        "未检测到 DEEPSEEK_API_KEY。请在运行程序的 PowerShell 窗口中设置："
        '$env:DEEPSEEK_API_KEY = "你的真实 Key"'
    )

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)

print("已加载父子知识库，共", len(parents), "个父章节。")
print("最高相似度低于", min_relevance_score, "时，本程序不会调用 DeepSeek。")
print("现在可以连续提问。输入 exit、quit 或 退出 可结束程序。")


# ==================== 每个问题都会执行一次 ====================

while True:
    question = input("\n你：").strip()

    if not question:
        continue

    if question.lower() in ("exit", "quit", "退出"):
        print("已结束父子知识库问答。")
        break

    # 第一步：把问题转换成查询向量。
    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )

    # 第二步：在全部子向量中找最相近的 top_k 个结果。
    search_results = util.semantic_search(
        query_embedding,
        child_embeddings,
        top_k=top_k,
    )[0]

    # semantic_search() 的结果按相似度从高到低排序。
    # “最相近”不等于“已经足够相关”，因此必须先检查最高分。
    best_score = search_results[0]["score"]

    print("\n本次问题：", question)
    print(f"最高子片段相似度：{best_score:.4f}")

    # 不相关时，直接结束本轮；不要找回父章节，也不要调用模型。
    if best_score < min_relevance_score:
        print("知识库中暂时没有足够相关的资料，本次不会调用 DeepSeek。")
        continue

    # 有时最高分合格，但后面的 top_k 结果不合格。
    # 只保留通过阈值的子片段，避免无关资料混入上下文。
    relevant_results = [
        result
        for result in search_results
        if result["score"] >= min_relevance_score
    ]

    retrieved_parent_contents = []
    seen_parent_ids = set()

    print("\n第一步：通过阈值的子片段")

    # 第三步：从合格子片段中取 parent_id，并找回完整父章节。
    for result in relevant_results:
        child_index = result["corpus_id"]
        score = result["score"]
        matched_child = children[child_index]
        parent_id = matched_child["parent_id"]

        print(f"\n相似度：{score:.4f}")
        print("子片段编号：", matched_child["child_id"])
        print("所属父章节：", parent_id)
        print("子片段内容：", matched_child["content"])

        # 多个子片段可能属于同一父章节，完整章节只加入一次。
        if parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)
        matched_parent = parents_by_id[parent_id]
        retrieved_parent_contents.append(
            f"【{matched_parent['title']}】\n{matched_parent['content']}"
        )

    retrieved_context = "\n\n".join(retrieved_parent_contents)

    print("\n第二步：根据 parent_id 找回的完整父章节")
    print(retrieved_context)

    # 第四步：只把通过相关性检查的完整资料交给 DeepSeek。
    system_message = SystemMessage(
        content=f"""
你是星光咖啡店客服。
只能根据 <完整父章节> 中的资料回答，不能补充资料中没有的信息。
如果资料无法回答，请明确说：资料中暂时没有这项信息。
回答要简短、自然。

<完整父章节>
{retrieved_context}
</完整父章节>
"""
    )

    response = model.invoke([
        system_message,
        HumanMessage(content=question),
    ])

    print("\nDeepSeek 最终回答：")
    print(response.content)


# 本课重点：
# 1. 父子检索先搜索子片段，不能因为“总能找到最相近的一个”就相信它相关。
# 2. 阈值判断必须发生在找回父章节和调用 DeepSeek 之前。
# 3. 同时过滤 top_k 中的低分结果，避免无关资料干扰最终回答。
