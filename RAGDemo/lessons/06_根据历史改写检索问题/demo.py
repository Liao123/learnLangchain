"""查询改写示例：先把短追问补完整，再用完整句子检索知识库。"""

import os
import sys
from pathlib import Path

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


MIN_RELEVANCE_SCORE = 0.50


def rewrite_retrieval_question(
    question: str,
    chat_history: list[HumanMessage | AIMessage],
    chat_model: ChatOpenAI,
) -> str:
    """根据前面的聊天，把短追问补成完整的检索问题。"""
    # 没有前文时，当前问题就是唯一线索，直接拿去检索。
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
    rewrite_response = chat_model.invoke([
        rewrite_system_message,
        # *chat_history：把每条历史消息逐条交给改写模型。
        *chat_history,
        HumanMessage(content=question),
    ])
    rewritten_question = rewrite_response.content.strip()

    # 改写模型意外返回空文字时，退回到用户原话，程序仍能继续运行。
    if not rewritten_question:
        return question

    return rewritten_question


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("未检测到 DEEPSEEK_API_KEY，请先在当前 PowerShell 窗口设置它。")

chat_model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)

# 这是一轮已经完成的对话。现在用户说“它”，程序需要从历史里判断“它”指金卡优惠。
chat_history = [
    HumanMessage(content="金卡会员有什么福利？"),
    AIMessage(content="金卡会员每消费一元可获得两倍积分，并享受现制饮品九折优惠。"),
]
question = "那它能和限时促销一起用吗？"

# 第一次模型调用：只负责补全检索问题。
retrieval_question = rewrite_retrieval_question(question, chat_history, chat_model)

# 第二步才是普通 RAG：用改写后的完整句子去找资料。
index_data = load_parent_child_index()
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
result = retrieve_parent_context(
    retrieval_question,
    index_data,
    embedding_model,
    min_relevance_score=MIN_RELEVANCE_SCORE,
)

print("BGE 模型来源：", model_source)
print("\n用户原话：", question)
print("程序拿去知识库查的问题：", retrieval_question)
print(f"最高子片段相似度：{result['best_score']:.4f}")
print("\n找回的完整父章节：")
print(result["context"])