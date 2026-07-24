# json：读取父子知识库索引。
import json

# os：读取环境变量中的 DeepSeek API Key。
import os

# Path：定位当前脚本同目录中的索引文件。
from pathlib import Path

# numpy：把 JSON 保存的向量列表还原为 NumPy 数组。
import numpy as np

# SentenceTransformer：把用户问题转换成 BGE 语义向量。
# util：提供 semantic_search()，用于查找最相近的子片段。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：通过 OpenAI 兼容接口连接 DeepSeek。
from langchain_openai import ChatOpenAI

# SystemMessage：设置资料范围和回答规则。
# HumanMessage：保存本轮用户问题。
from langchain.messages import HumanMessage, SystemMessage


# 第 28 课构建的父子知识库索引，与当前脚本放在同一文件夹。
index_file = Path(__file__).with_name("父子知识库索引.json")

# BGE 中文检索使用的查询指令。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 每轮先取最相近的 3 个子片段，再过滤低相关结果。
top_k = 3
min_relevance_score = 0.70


# ==================== 程序启动时只执行一次 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
parents = index_data["parents"]
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)

# 通过 parent_id 快速找回完整父章节。
parents_by_id = {
    parent["parent_id"]: parent
    for parent in parents
}

# document_title 是来源展示的一部分，去掉 Markdown 标题符号后更适合终端输出。
document_title = index_data["document_title"].lstrip("# ").strip()

print("已读取父子索引：", index_file.name)
print("父章节数量：", len(parents))
print("子片段数量：", len(children))
print("正在加载 BGE 向量模型，首次运行可能需要下载，请耐心等待。")

embedding_model = SentenceTransformer(index_data["embedding_model"])

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

    # 第一步：问题向量与已有的子片段向量进行相似度搜索。
    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )
    search_results = util.semantic_search(
        query_embedding,
        child_embeddings,
        top_k=top_k,
    )[0]

    best_score = search_results[0]["score"]
    print("\n本次问题：", question)
    print(f"最高子片段相似度：{best_score:.4f}")

    # 没有可靠资料时，既不生成回答，也不展示伪造的来源。
    if best_score < min_relevance_score:
        print("知识库中暂时没有足够相关的资料，本次不会调用 DeepSeek。")
        continue

    # 最高分合格不代表 top_k 中每一段都合格，仍要逐条过滤。
    relevant_results = [
        result
        for result in search_results
        if result["score"] >= min_relevance_score
    ]

    retrieved_parent_contents = []
    source_records = []
    seen_parent_ids = set()

    print("\n第一步：通过阈值的子片段")
    for result in relevant_results:
        matched_child = children[result["corpus_id"]]
        parent_id = matched_child["parent_id"]
        matched_parent = parents_by_id[parent_id]

        print(f"\n相似度：{result['score']:.4f}")
        print("子片段编号：", matched_child["child_id"])
        print("所属父章节：", matched_parent["title"])
        print("子片段内容：", matched_child["content"])

        # 一条来源对应一个实际命中的子片段，便于用户追查本轮依据。
        source_records.append({
            "chapter_title": matched_parent["title"],
            "child_id": matched_child["child_id"],
            "score": result["score"],
        })

        # 同一父章节可能有多个命中子片段，但完整正文只加入一次。
        if parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)
        retrieved_parent_contents.append(
            f"【{matched_parent['title']}】\n{matched_parent['content']}"
        )

    retrieved_context = "\n\n".join(retrieved_parent_contents)
    print("\n第二步：找回的完整父章节")
    print(retrieved_context)

    # 第三步：只把本轮找回的完整资料交给模型。
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

    # 第四步：把本轮实际采用的检索片段作为资料来源展示。
    print("\n资料来源：")
    for source in source_records:
        print(
            f"- {document_title} > {source['chapter_title']} "
            f"（{source['child_id']}，相似度 {source['score']:.4f}）"
        )


# 本课重点：
# 1. 来源来自通过阈值的子片段，而不是模型凭空生成的链接。
# 2. 资料来源说明“为什么检索到这段内容”，不等于保证回答绝对正确。
# 3. 低相关时不回答，也不显示无关来源来伪装依据。