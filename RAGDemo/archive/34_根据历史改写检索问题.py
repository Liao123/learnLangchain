# json：读取父子知识库索引。
import json

# os：读取环境变量中的 DeepSeek API Key。
import os

# Path：定位当前脚本同目录中的索引文件。
from pathlib import Path

# numpy：把 JSON 保存的向量列表还原为 NumPy 数组。
import numpy as np

# SentenceTransformer：把当前问题转换成 BGE 语义向量。
# util：提供 semantic_search()，用于查找最相近的子片段。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：通过 OpenAI 兼容接口连接 DeepSeek。
from langchain_openai import ChatOpenAI

# AIMessage：保存模型上一次的回答。
# HumanMessage：保存用户消息。
# SystemMessage：保存本轮资料范围和回答规则。
from langchain.messages import AIMessage, HumanMessage, SystemMessage


index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："
top_k = 3
min_relevance_score = 0.70


# ==================== 程序启动时只执行一次 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
parents = index_data["parents"]
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)
parents_by_id = {
    parent["parent_id"]: parent
    for parent in parents
}
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

# chat_history 保存已完成的“用户消息 -> AI 消息”对话。
# 它帮助模型理解上下文，但不会替代每轮的知识库检索。
chat_history = []


# 把“那它呢”这类短追问补成一条可以直接查知识库的完整问题。
def rewrite_retrieval_question(question: str) -> str:
    # 第一轮没有历史，当前问题本身就是检索问题，不需要改写。
    if not chat_history:
        return question

    rewrite_system_message = SystemMessage(
        content="""
你负责改写知识库检索问题，不负责回答用户。
根据此前对话，把用户最新的问题改成一句不看前文也能理解的完整问题。
如果最新问题本来就完整，原样返回。
只返回改写后的问题，不要解释，不要回答。
"""
    )

    # 第一次 invoke() 只负责得到完整检索问题，不会根据知识库回答用户。
    rewrite_response = model.invoke([
        rewrite_system_message,
        # *chat_history：把历史列表拆成多条消息，一条一条交给改写模型。
        *chat_history,
        HumanMessage(content=question),
    ])

    rewritten_question = rewrite_response.content.strip()
    if not rewritten_question:
        return question

    return rewritten_question


# ==================== 每个问题都会执行一次 ====================

while True:
    question = input("\n你：").strip()

    if not question:
        continue

    if question.lower() in ("exit", "quit", "退出"):
        print("已结束父子知识库问答。")
        break

    # 先根据历史把短追问补完整。question 保留用户原话，retrieval_question 专门用于查资料。
    retrieval_question = rewrite_retrieval_question(question)
    print("\n本轮用户原话：", question)
    print("本轮拿去知识库查的问题：", retrieval_question)

    query_embedding = embedding_model.encode(
        [query_instruction + retrieval_question],
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

    if best_score < min_relevance_score:
        refusal = "知识库中暂时没有足够相关的资料，本次不会调用 DeepSeek。"
        print(refusal)

        # 拒答也是对话的一部分，记录后可让下一轮知道发生过什么。
        chat_history.extend([
            HumanMessage(content=question),
            AIMessage(content=refusal),
        ])
        continue

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

        source_records.append({
            "chapter_title": matched_parent["title"],
            "child_id": matched_child["child_id"],
            "score": result["score"],
        })

        if parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)
        retrieved_parent_contents.append(
            f"【{matched_parent['title']}】\n{matched_parent['content']}"
        )

    retrieved_context = "\n\n".join(retrieved_parent_contents)
    print("\n第二步：找回的完整父章节")
    print(retrieved_context)

    # 本轮系统消息带的是新检索到的资料，不会沿用上一轮资料。
    system_message = SystemMessage(
        content=f"""
你是星光咖啡店客服。
只能根据 <完整父章节> 中的资料回答，不能补充资料中没有的信息。
如果资料无法回答，请明确说：资料中暂时没有这项信息。
此前对话只用于理解上下文，不能作为资料来源或事实依据。
回答要简短、自然。

<完整父章节>
{retrieved_context}
</完整父章节>
"""
    )

    # 历史放在系统消息之后、当前问题之前，让模型能看见连续对话。
    # 第二次 invoke() 才带上本轮完整章节，真正生成给用户看的回答。
    response = model.invoke([
        system_message,
        # *chat_history 表示把历史列表拆开，逐条放进消息列表。
        # 例如 [A, B] 会变成 A, B；不写 * 就会把整个列表当成一条错误的消息。
        *chat_history,
        HumanMessage(content=question),
    ])

    # 只有模型已经给出本轮回答，才把这对消息追加到历史中。
    chat_history.extend([
        HumanMessage(content=question),
        response,
    ])

    print("\nDeepSeek 最终回答：")
    print(response.content)

    print("\n资料来源：")
    for source in source_records:
        print(
            f"- {document_title} > {source['chapter_title']} "
            f"（{source['child_id']}，相似度 {source['score']:.4f}）"
        )


# 本课重点：
# 1. 先用历史把不完整追问改写成 retrieval_question，再拿它去做向量检索。
# 2. 最终回答仍使用用户的原话 question；改写后的句子只负责帮程序找资料。
# 3. 一轮对话会调用两次模型：第一次改写问题，第二次根据新资料回答问题。