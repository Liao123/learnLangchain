# json：Python 自带模块，用来读取父子知识库索引文件。
import json

# os：用来读取环境变量中的 DeepSeek API Key。
import os

# Path：用于定位与当前 Python 文件同目录的索引文件。
from pathlib import Path

# numpy：把 JSON 中保存的数字列表还原为 NumPy 数组。
import numpy as np

# SentenceTransformer：加载 BGE 模型，把用户问题转换成语义向量。
# util：提供 semantic_search()，比较问题向量和子片段向量。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：通过 OpenAI 兼容接口连接 DeepSeek。
from langchain_openai import ChatOpenAI

# SystemMessage：告诉 AI 它的角色、规则和检索资料。
# HumanMessage：保存用户提出的自然语言问题。
from langchain.messages import SystemMessage, HumanMessage


# 读取第 28 课生成的父子索引。
index_file = Path(__file__).with_name("父子知识库索引.json")

# BGE 官方建议的中文检索提示，用于把问题转换成检索向量。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 先取最相关的 3 个子片段。
# 这些子片段可能属于同一个父章节，后面会去重父章节。
top_k = 3


# 第一步：读取 JSON 索引文件。
# read_text() 返回 JSON 格式的普通字符串。
index_text = index_file.read_text(encoding="utf-8")

# json.loads() 把 JSON 字符串解析成 Python 字典。
index_data = json.loads(index_text)


# 从索引字典中取出父章节、子片段和子向量。
parents = index_data["parents"]
children = index_data["children"]

# np.array() 把 JSON 中的嵌套数字列表转换成 NumPy 数组。
# dtype=np.float32 保证它和 BGE 查询向量使用相同的数据类型。
child_embeddings = np.array(
    index_data["child_embeddings"],
    dtype=np.float32,
)

print("已读取父子索引：", index_file.name)
print("父章节数量：", len(parents))
print("子片段数量：", len(children))
print("子向量数量：", len(child_embeddings))


# 第二步：建立“父章节ID → 父章节对象”的查询字典。
#
# 原始 parents 是列表：
# [
#     {"parent_id": "parent_1", "title": "退款办理规则", ...},
#     {"parent_id": "parent_2", "title": "会员积分与优惠", ...},
# ]
#
# 转换后可以直接通过 parents_by_id["parent_1"] 找到父章节，
# 不需要每次都从头遍历整个 parents 列表。
parents_by_id = {
    parent["parent_id"]: parent
    for parent in parents
}


# 第三步：加载与构建索引时相同的 BGE 模型。
embedding_model = SentenceTransformer(
    index_data["embedding_model"]
)

# 先用一个固定问题观察完整流程。
# 你理解代码后，可以直接修改这句话再运行。
question = "金卡会员有什么福利？"

# encode() 的输入仍然要使用列表，即使现在只有一个问题。
# 输出是一个查询向量，后面会与所有子向量比较。
query_embedding = embedding_model.encode(
    [query_instruction + question],
    normalize_embeddings=True,
)


# 第四步：只搜索子向量。
# semantic_search() 不会直接返回中文，也不会直接返回父章节。
# 它返回最相似向量的下标 corpus_id 和相似度 score。
search_results = util.semantic_search(
    query_embedding,
    child_embeddings,
    top_k=top_k,
)[0]


# 保存最终要交给 AI 的完整父章节文字。
retrieved_parent_contents = []

# set()：集合，用来记录已经取过的 parent_id。
# 如果多个子片段属于同一个父章节，就只把父章节交给 AI 一次。
seen_parent_ids = set()

print("\n用户问题：", question)
print("\n第一步：BGE 搜索到的子片段")

for result in search_results:
    # corpus_id 是匹配到的子向量在 child_embeddings 中的下标。
    child_index = result["corpus_id"]
    score = result["score"]

    # 由于 children[i] 和 child_embeddings[i] 保持相同顺序，
    # 可以使用同一个 child_index 找到对应的子片段对象。
    matched_child = children[child_index]

    # 子片段对象中的 parent_id 就是连接父章节的关键字段。
    parent_id = matched_child["parent_id"]

    print(f"\n相似度：{score:.4f}")
    print(f"\n子片段下标：{child_index}")
    print("子片段编号：", matched_child["child_id"])
    print("所属父章节：", parent_id)
    print("子片段内容：", matched_child["content"])

    # 如果这个父章节已经添加过，就跳过，避免重复传给 AI。
    if parent_id in seen_parent_ids:
        continue

    # add()：把一个父章节ID加入集合。
    seen_parent_ids.add(parent_id)

    # 通过 parent_id 从查询字典中找回完整父章节对象。
    matched_parent = parents_by_id[parent_id]

    # 只把完整父章节的正文加入最终上下文。
    retrieved_parent_contents.append(
        f"【{matched_parent['title']}】\n{matched_parent['content']}"
    )


# join()：使用两个换行，把多个完整父章节拼成一段上下文。
retrieved_context = "\n\n".join(retrieved_parent_contents)

print("\n第二步：根据 parent_id 找回的完整父章节")
print(retrieved_context)


# 第五步：连接 DeepSeek，让它阅读完整父章节并组织自然语言答案。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

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

# invoke()：把系统规则和用户问题一起发送给 DeepSeek。
response = model.invoke([
    system_message,
    HumanMessage(content=question),
])

print("\nDeepSeek 最终回答：")
print(response.content)


# 本课的核心链路：
# 用户问题
# -> query_embedding
# -> semantic_search(child_embeddings) 这个返回的 corpus_id属性就是向量数组下标记 所以可以同步取到向量前源文章数组对象下标 拿到父id 也就是 完整文章对象 给ai
 # -> result["corpus_id"]
# -> children[child_index]
# -> matched_child["parent_id"]
# -> parents_by_id[parent_id]
# -> 完整父章节
# -> DeepSeek 自然语言回答


