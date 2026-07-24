# os：Python 自带模块，用来读取环境变量中的 DeepSeek API Key。
import os

# SentenceTransformer：加载“嵌入模型”，把文字转换成语义向量。 会自动从 Hugging Face下载模型到本地缓存。
# util：提供 semantic_search()，用来从资料片段中找语义最接近的问题答案。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：LangChain 中连接 DeepSeek 聊天模型的类。
from langchain_openai import ChatOpenAI

# SystemMessage：给 AI 规则和检索出的资料。
# HumanMessage：用户用自然语言提出的问题。
from langchain.messages import SystemMessage, HumanMessage


# 本地知识库文件。它与本程序放在同一个文件夹中。
knowledge_file = "咖啡店知识库.md"

# 嵌入模型名称。第一次运行时会从 Hugging Face 下载这个公开的中文模型，理解中文的本地小模型
# 下载完成后会缓存在电脑中，之后一般不需要重复下载。
# BGE 把中文问题理解后，转成语义数字向量
# → 在知识库各段文字对应的数字向量中，找意思最接近的几段
# → 取回这些段落原本的中文文字
# → DeepSeek 根据“用户问题 + 找到的中文资料”生成中文回答
embedding_model_name = "BAAI/bge-small-zh-v1.5" 

# BGE 中文模型建议给“短问题”加上的检索提示。
# 这不是给 DeepSeek 看的提示词，而是给嵌入模型看的检索说明。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# top_k：每次从知识库中取语义最相关的几段资料。
top_k = 2


def split_markdown_into_chunks(markdown_text: str) -> list[str]:
    """按 Markdown 的二级标题（##）把知识库切成多个可检索片段。"""

    # split("\n## ")：以“换行 + 二级标题”作为切分位置。
    # sections[0] 是文档总标题，本课不把它当作知识片段使用。
    sections = markdown_text.split("\n## ")

    # chunks：保存切分后的每段资料。
    chunks = []

    # sections[1:]：从第二项开始逐段处理。标题不要
    for section in sections[1:]:
        # strip()：去掉开头和结尾多余的空白、换行。
        clean_section = section.strip()

        # if：跳过空段落，避免把空文字送去做语义检索。
        if clean_section:
            # append()：把一段资料加入 chunks 列表。
            # 加回 ##，方便后面打印时看清这段资料原来的标题。
            chunks.append("## " + clean_section)

    return chunks


# open()：只读方式打开本地知识库；encoding="utf-8" 保证中文正常读取。
# with：读取结束后，Python 自动关闭文件。
with open(knowledge_file, "r", encoding="utf-8") as file:
    knowledge_text = file.read()


# 先把长文档切成小段。资料很大时，不应该把全文都发送给 DeepSeek。
chunks = split_markdown_into_chunks(knowledge_text)

print("知识库一共切成", len(chunks), "个片段。")


# 加载本地嵌入模型。
# 它不负责聊天回答，只负责把“问题”和“资料片段”转换成数字向量。
embedding_model = SentenceTransformer(embedding_model_name)


# 为每一个知识片段创建语义向量。
# normalize_embeddings=True：把向量统一到相同长度，便于比较语义相似度。
document_embeddings = embedding_model.encode(
    chunks,
    normalize_embeddings=True,
)


# 可以修改这句话，试试用户说法与知识库文字不完全一致时的检索效果。
question = "我买的咖啡豆还没拆封，五天前买的，可以退吗？"

# 只给“查询问题”加 BGE 的检索提示；资料片段不需要加。
# [ ... ]：把一个问题放入列表，方便以后一次检索多个问题。 它在本机把文字转换成数字向量。
query_embedding = embedding_model.encode(
    [query_instruction + question],
    # 表示把每个向量统一成相同长度，方便后面公平比较“问题向量”和“资料向量”谁更接近。
    normalize_embeddings=True,
)


# semantic_search()：比较“问题向量”和“资料向量”，找出最接近的 top_k 段。
# 返回的是“每个问题的检索结果列表”；本课只有一个问题，所以 [0] 取第一组结果。
# → 比较问题向量和资料向量
# → 给资料排相关性分数
search_results = util.semantic_search(
    query_embedding,
    document_embeddings,
    top_k=top_k,
)[0]


# retrieved_chunks：保存真正要交给 DeepSeek 的少量相关资料。
retrieved_chunks = []

print("\n用户问题：", question)
print("\n语义检索找到的资料：")

for result in search_results:
    # corpus_id：这段资料在 chunks 列表中的位置。
    chunk_index = result["corpus_id"]

    # score：语义相近程度。初学阶段只比较排序，分数不是百分比。
    score = result["score"]

    # 根据位置取回原始文字。
    chunk = chunks[chunk_index]
    retrieved_chunks.append(chunk)

    print(f"\n相似度：{score:.4f}")
    print(chunk)


# join()：把检索到的多段资料合并成一段上下文，用两个换行分隔。
retrieved_context = "\n\n".join(retrieved_chunks)


# 创建 DeepSeek 聊天模型。它只负责依据资料组织自然语言答案。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# 关键规则：AI 只能依据“语义检索找到的资料”回答。
# 如果资料不足，宁可明确说不知道，也不要补编事实。
system_message = SystemMessage(
    content=f"""
你是星光咖啡店客服。
只能依据 <检索资料> 中的内容回答用户问题，不能补充资料中没有的信息。
如果检索资料无法回答，请明确说：资料中暂时没有这项信息。
回答要简短、自然。

<检索资料>
{retrieved_context}
</检索资料>
"""
)


# 最后一步：DeepSeek 根据“用户问题 + 少量相关资料”生成回答。
response = model.invoke([
    system_message,
    HumanMessage(content=question),
])

print("\nDeepSeek 最终回答：")
print(response.content)


# 本课 RAG 流程：
# 1. 文档切块  2. 每块创建语义向量  3. 问题创建语义向量
# 4. 找最相近片段  5. 把片段交给 DeepSeek 生成答案
