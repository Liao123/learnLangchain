"""星光咖啡店父子知识库问答：当前持续维护的 RAG 小应用。"""

import os
import sys
import time
from pathlib import Path

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# 当前文件在 app/聊天问答/；把 app/ 加进搜索路径，才能读取旁边“检索核心”文件夹。
APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from 检索核心.rag_core import (
    build_source_records,
    get_index_content_version,
    load_embedding_model,
    load_parent_child_index,
    retrieve_parent_context,
)
from 检索核心.retrieval_cache import RetrievalCache


TOP_K = 3
MIN_RELEVANCE_SCORE = 0.70
# 当前终端应用没有登录系统，先用一个统一身份占位。
# 接入登录后，应替换成真实用户角色、租户或权限版本。
CACHE_USER_ROLE = "public_customer"
RETRIEVAL_CACHE_MAX_SIZE = 50
RETRIEVAL_CACHE_TTL_SECONDS = 300


def print_retrieval(result: dict) -> None:
    """显示检索依据，方便学习时核对 RAG 是否找对资料。"""
    print(f"最高子片段相似度：{result['best_score']:.4f}")

    for match in result["matched_children"]:
        child = match["child"]
        print(f"\n相似度：{match['score']:.4f}")
        print("子片段：", child["child_id"])
        print("父章节：", child["parent_id"])
        print(child["content"])


def print_sources(result: dict, index_data: dict) -> None:
    """在最终回答后显示本轮检索实际采用的资料来源。"""
    print("\n资料来源：")
    for source in build_source_records(result, index_data):
        print(
            "- "
            f"{source['document_title']} > {source['chapter_title']} "
            f"（{source['child_id']}，相似度 {source['score']:.4f}）"
        )


def rewrite_retrieval_question(
    question: str,
    chat_history: list[HumanMessage | AIMessage],
    chat_model: ChatOpenAI,
) -> str:
    """把依赖上文的追问补成一句可以直接拿去查知识库的话。"""
    # 第一轮没有历史时，用户问题本来就是完整的，不需要额外调用模型改写。
    if not chat_history:
        return question

    # 这次系统消息的工作只有一件事：改写检索问题，不能直接回答用户。
    rewrite_system_message = SystemMessage(
        content="""
你负责改写知识库检索问题，不负责回答用户。
根据此前对话，把用户最新的问题改成一句不看前文也能理解的完整问题。
如果最新问题本来就完整，原样返回。
只返回改写后的问题，不要解释，不要回答。
"""
    )

    # 第一次 invoke() 只负责得到完整检索问题，不会根据知识库回答用户。
    rewrite_response = chat_model.invoke([
        rewrite_system_message,
        # *chat_history 表示把每条历史消息逐条交给改写模型。
        *chat_history,
        HumanMessage(content=question),
    ])

    # content 是模型返回的文字。空字符串时宁可用原问题，避免拿空内容去检索。
    rewritten_question = rewrite_response.content.strip()
    if not rewritten_question:
        return question

    return rewritten_question


def main() -> None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未检测到 DEEPSEEK_API_KEY。请在当前 PowerShell 窗口中设置该环境变量。"
        )

    index_data = load_parent_child_index()
    # 索引 JSON 内容变化时，index_content_version 会自动变化，例如 index-001e7af6fbec。
    index_content_version = get_index_content_version()
    # top_k 或阈值变化也会影响 result，因此也拼进缓存版本。
    retrieval_cache_version = (
        f"{index_content_version}-top{TOP_K}-threshold{MIN_RELEVANCE_SCORE:.2f}"
    )
    print("已读取父子索引：", index_data["source_file"])
    print("父章节数量：", len(index_data["parents"]))
    print("子片段数量：", len(index_data["children"]))
    print("正在加载 BGE 向量模型...")

    embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
    print("BGE 模型来源：", model_source)

    chat_model = ChatOpenAI(
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
        api_key=api_key,
    )

    print(f"相似度低于 {MIN_RELEVANCE_SCORE} 时不会调用 DeepSeek。")
    print("自动缓存版本：", retrieval_cache_version)
    print(f"检索缓存：最多 {RETRIEVAL_CACHE_MAX_SIZE} 条，每条有效 {RETRIEVAL_CACHE_TTL_SECONDS} 秒。")
    print("现在可以提问；输入 exit、quit 或 退出 可结束程序。")
    # 历史只用于维持对话上下文；每一轮仍会用当前 question 重新检索知识库。
    chat_history: list[HumanMessage | AIMessage] = []
    # retrieval_cache 专门缓存 retrieve_parent_context() 的 result，不缓存 DeepSeek 最终回答。
    retrieval_cache = RetrievalCache(
        max_size=RETRIEVAL_CACHE_MAX_SIZE,
        ttl_seconds=RETRIEVAL_CACHE_TTL_SECONDS,
    )

    while True:
        question = input("\n你：").strip()
        if not question:
            continue
        if question.lower() in ("exit", "quit", "退出"):
            print("已结束知识库问答。")
            break

        # 先把“那它呢”这类短追问补完整。原来的 question 仍保留给最终回答使用。
        retrieval_question = rewrite_retrieval_question(
            question,
            chat_history,
            chat_model,
        )
        print("\n本轮用户原话：", question)
        print("本轮拿去知识库查的问题：", retrieval_question)

        # 例如当前 key 会是：
        # "public_customer:index-001e7af6fbec-top3-threshold0.70:周末几点营业？"。
        cache_key = retrieval_cache.make_key(
            CACHE_USER_ROLE,
            retrieval_cache_version,
            retrieval_question,
        )
        current_time = int(time.time())
        result = retrieval_cache.get(cache_key, current_time)

        if result is None:
            # 缓存未命中才真正调用 BGE 检索。
            result = retrieve_parent_context(
                question=retrieval_question,
                index_data=index_data,
                embedding_model=embedding_model,
                top_k=TOP_K,
                min_relevance_score=MIN_RELEVANCE_SCORE,
            )
            removed_key = retrieval_cache.set(cache_key, result, current_time)
            print("本轮检索来源：BGE 检索（已存入缓存）")
            if removed_key is not None:
                print("缓存容量已满，已删除最久未使用的缓存：", removed_key)
        else:
            # 缓存命中时 result 和第一次 BGE 得到的 result 是同一份结构。
            print("本轮检索来源：缓存（跳过 BGE 检索）")

        print_retrieval(result)
        if not result["parents"]:
            refusal = "知识库中暂时没有足够相关的资料，本次不会调用 DeepSeek。"
            print(f"\n{refusal}")
            chat_history.extend([
                HumanMessage(content=question),
                AIMessage(content=refusal),
            ])
            continue

        print("\n找回的完整父章节：")
        print(result["context"])

        system_message = SystemMessage(
            content=f"""
你是星光咖啡店客服。
只能根据 <完整父章节> 中的资料回答，不能补充资料中没有的信息。
如果资料无法回答，请明确说：资料中暂时没有这项信息。
此前对话只用于理解上下文，不能作为资料来源或事实依据。
回答要简短、自然。

<完整父章节>
{result['context']}
</完整父章节>
"""
        )
    # 第二次 invoke() 才带上本轮完整章节，真正生成给用户看的回答。
        response = chat_model.invoke([
            system_message,
            # *chat_history 表示把历史列表拆开，逐条放进消息列表。
            # 例如 [A, B] 会变成 A, B；不写 * 就会把整个列表当成一条错误的消息。
            *chat_history,
            HumanMessage(content=question),
        ])
        chat_history.extend([
            HumanMessage(content=question),
            response,
        ])

        print("\nDeepSeek：")
        print(response.content)
        print_sources(result, index_data)


if __name__ == "__main__":
    main()
