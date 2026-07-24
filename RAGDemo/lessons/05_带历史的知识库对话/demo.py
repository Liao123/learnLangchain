"""第 33 课：真实运行一轮带历史的知识库对话。"""

import os
import sys
from pathlib import Path

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


# lesson 文件在 lessons/05_带历史的知识库对话，向上两层就是 RAGDemo。
RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 0.50 方便本课观察流程；实际项目要用测试题决定最终阈值。
MIN_RELEVANCE_SCORE = 0.50


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("未检测到 DEEPSEEK_API_KEY，请先在当前 PowerShell 窗口设置它。")

# 本课会真实调用一次 DeepSeek 来回答，所以需要聊天模型对象。
chat_model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)

index_data = load_parent_child_index()
print("正在加载 BGE 向量模型...")
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
print("BGE 模型来源：", model_source)
print("\n第 33 课建议按这个顺序提问：")
print("1. 普通会员消费有什么积分？")
print("2. 那金卡会员呢？")
print("“那它呢？”还没有足够关键词，下一课才会把它补完整后再检索。")
print("输入 exit、quit 或 退出 可结束程序。")

# 一开始没有历史。每轮回答结束后，程序会把“用户问题 + AI 回答”加进来。
chat_history: list[HumanMessage | AIMessage] = []

while True:
    question = input("\n你：").strip()

    if not question:
        continue

    if question.lower() in ("exit", "quit", "退出"):
        print("已结束第 33 课。")
        break

    # 第 33 课的检索只看当前这句话。它不会把历史文字拼进检索问题。
    result = retrieve_parent_context(
        question,
        index_data,
        embedding_model,
        min_relevance_score=MIN_RELEVANCE_SCORE,
    )

    print("\n本轮拿去知识库查的问题：", question)
    print(f"最高子片段相似度：{result['best_score']:.4f}")

    if not result["parents"]:
        refusal = "知识库中暂时没有足够相关的资料，本次不会调用 DeepSeek。"
        print(refusal)
        print("提示：如果你输入的是“那它呢？”，它属于第 34 课要解决的不完整检索问题。")

        # 拒答也算一轮对话，保存后下一轮模型能知道刚才发生过什么。
        chat_history.extend([
            HumanMessage(content=question),
            AIMessage(content=refusal),
        ])
        continue

    # context 是本轮根据最新问题找回的完整父章节，不是上一轮留下的旧资料。
    system_message = SystemMessage(
        content=f"""
你是星光咖啡店客服。
只能根据 <完整父章节> 中的资料回答，不能补充资料中没有的信息。
此前对话只用于理解上下文，不能作为资料来源或事实依据。
回答要简短、自然。

<完整父章节>
{result['context']}
</完整父章节>
"""
    )

    # 真正发给 DeepSeek 的顺序：本轮资料 -> 历史问答 -> 当前问题。
    messages = [
        system_message,
        # *chat_history 表示把历史列表拆开，逐条放进消息列表。
        *chat_history,
        HumanMessage(content=question),
    ]

    # len() 返回列表里有多少条消息。这里打印它，只是让你看到历史真的在变多。
    print("本轮会带给 DeepSeek 的历史消息数：", len(chat_history))
    response = chat_model.invoke(messages)

    print("\nDeepSeek：")
    print(response.content)

    # 这轮结束后才保存。下一轮提问时，chat_history 里就会有这两条消息。
    chat_history.extend([
        HumanMessage(content=question),
        response,
    ])