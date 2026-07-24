# json：Python 自带模块，用来读取 JSON 格式的父子知识库索引。
import json

# os：Python 自带模块，用来读取操作系统环境变量中的 API Key。
import os

# Path：pathlib 模块中的路径类，用来定位当前 Python 文件旁边的索引文件。
from pathlib import Path

# numpy：用于把 JSON 中保存的嵌套数字列表转换成 NumPy 数组。
import numpy as np

# SentenceTransformer：加载 BGE 中文嵌入模型，把问题转换成语义向量。
# util：sentence-transformers 提供的工具模块，其中的 semantic_search()
# 用来比较问题向量和子片段向量的相似度。
from sentence_transformers import SentenceTransformer, util

# ChatOpenAI：LangChain 提供的聊天模型类，可以通过 OpenAI 兼容接口连接 DeepSeek。
from langchain_openai import ChatOpenAI

# SystemMessage：保存发给模型的系统规则。
# HumanMessage：保存用户本次输入的问题。
from langchain.messages import SystemMessage, HumanMessage


# Path(__file__)：__file__ 是 Python 提供的特殊变量，表示当前脚本文件的路径。
# with_name()：保留当前文件所在文件夹，只把文件名替换成指定的索引文件名。
index_file = Path(__file__).with_name("父子知识库索引.json")

# BGE 官方建议的中文检索提示。
# 它用于告诉嵌入模型：接下来这段文字是一个检索问题。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 每次查询取最相关的 3 个子片段。
# top_k 是 semantic_search() 的参数，表示最多返回多少个检索结果。
top_k = 3


# ==================== 程序启动时只执行一次 ====================

# read_text()：读取文本文件内容。
# encoding="utf-8"：使用 UTF-8 解码，避免中文在 Windows 中出现乱码。
index_text = index_file.read_text(encoding="utf-8")

# json.loads()：把 JSON 格式的字符串解析成 Python 对象。
# 当前索引文件的最外层对象是一个字典。
index_data = json.loads(index_text)

# 从索引字典中取出父章节和子片段列表。
parents = index_data["parents"]
children = index_data["children"]

# np.array()：把 JSON 读取后的嵌套列表转换成 NumPy 数组。
# dtype=np.float32：指定每个数字使用 32 位浮点数，
# 使资料向量和之后生成的问题向量保持相同的数据类型。
child_embeddings = np.array(
    index_data["child_embeddings"],
    dtype=np.float32,
)

print("已读取父子索引：", index_file.name)
print("父章节数量：", len(parents))
print("子片段数量：", len(children))
print("子向量数量：", len(child_embeddings))


# 把父章节列表转换成“父章节 ID → 父章节对象”的字典。
# 字典推导式会逐项遍历 parents，并为每个父章节建立一个键值对。
# 这样查询时可以使用 parents_by_id[parent_id] 直接找到完整父章节。
parents_by_id = {
    parent["parent_id"]: parent
    for parent in parents
}

# SentenceTransformer()：根据模型名称加载已经下载的 BGE 模型。
# 这里必须使用和第28课构建索引时相同的嵌入模型，
# 否则资料向量和问题向量可能不在同一个语义空间中。
embedding_model = SentenceTransformer(
    index_data["embedding_model"]
)

# ChatOpenAI()：创建连接 DeepSeek 的聊天模型对象。
# base_url：指定兼容 OpenAI 接口格式的服务地址。
# model：指定要使用的 DeepSeek 模型名称。
# api_key：从环境变量中读取密钥，不把真实密钥写进代码。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

print("已加载父子知识库，共", len(parents), "个父章节。")
print("现在可以连续提问。输入 exit、quit 或 退出 可结束程序。")


# ==================== 每个问题都会执行一次 ====================

# while True：创建一个不会自动结束的循环。
# 只有遇到下面的 break，程序才会离开循环。
while True:
    # input()：暂停程序，在终端等待用户输入一行文字。
    # \n：让提示语从新的一行开始显示。
    # strip()：删除输入文字前后的空格、制表符和换行符。
    question = input("\n你：").strip()

    # if：根据条件决定是否执行缩进代码块。
    # not question：空字符串会被 Python 判断为 False，not 后变成 True。
    # continue：跳过本轮循环剩余内容，直接回到 while 开头等待下一个问题。
    if not question:
        continue

    # lower()：把英文字符转换成小写。
    # in：判断 question 是否属于括号中的退出词元组。
    # 这样输入 EXIT、Exit、exit 都可以结束程序。
    if question.lower() in ("exit", "quit", "退出"):
        print("已结束父子知识库问答。")
        break

    # encode()：把本次用户问题转换成语义向量。
    # 输入仍然使用列表，因为 encode() 可以一次处理多个文字。
    # normalize_embeddings=True：把向量长度归一化，方便比较相似度。
    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )

    # semantic_search()：在所有子片段向量中查找最相似的片段。
    # query_embedding：本次问题的向量。
    # child_embeddings：第28课已经保存的全部子片段向量。
    # top_k：最多返回 3 个结果。
    # [0]：因为本次输入虽然只有一个问题，但返回结果仍按“每个问题一组”组织，
    # 所以取第 0 组结果。
    search_results = util.semantic_search(
        query_embedding,
        child_embeddings,
        top_k=top_k,
    )[0]

    # retrieved_parent_contents：保存最终要交给 DeepSeek 的完整父章节文字。
    retrieved_parent_contents = []

    # set()：创建一个空集合。
    # 它用于记录已经加入上下文的 parent_id，避免同一个父章节重复加入。
    seen_parent_ids = set()

    print("\n本次问题：", question)
    print("\n第一步：BGE 找到的子片段")

    # for：依次遍历 semantic_search() 返回的每个结果字典。
    for result in search_results:
        # result["corpus_id"]：返回匹配向量在 child_embeddings 中的数组下标。
        child_index = result["corpus_id"]

        # result["score"]：返回问题向量和子片段向量的相似度分数。
        score = result["score"]

        # children 和 child_embeddings 保持相同顺序，
        # 因此可以用 child_index 找到对应的子片段对象。
        matched_child = children[child_index]

        # 子片段对象中的 parent_id 记录了它属于哪个父章节。
        parent_id = matched_child["parent_id"]

        print(f"\n相似度：{score:.4f}")
        print("子片段下标：", child_index)
        print("子片段编号：", matched_child["child_id"])
        print("所属父章节：", parent_id)
        print("子片段内容：", matched_child["content"])

        # 如果同一个父章节已经被加入，就跳过本次结果。
        # continue 会直接进入 for 循环的下一项。
        if parent_id in seen_parent_ids:
            continue

        # add()：把 parent_id 加入集合。
        seen_parent_ids.add(parent_id)

        # 使用 parent_id 从查询字典中取回完整父章节。
        matched_parent = parents_by_id[parent_id]

        # append()：把一段文字追加到列表末尾。
        retrieved_parent_contents.append(
            f"【{matched_parent['title']}】\n{matched_parent['content']}"
        )

    # join()：用两个换行符把多个父章节文字连接成一段上下文。
    retrieved_context = "\n\n".join(retrieved_parent_contents)

    print("\n第二步：根据 parent_id 找回的完整父章节")
    print(retrieved_context)

    # SystemMessage：给 DeepSeek 设置本次回答的角色和资料范围。
    # f-string：允许把 retrieved_context 的值插入三引号字符串。
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

    # HumanMessage：把本轮用户问题包装成 LangChain 消息对象。
    # invoke()：调用 DeepSeek，并传入本轮的系统消息和用户消息。
    # 注意：这里每轮只传入本次问题，没有传入上一轮消息，
    # 所以这是“连续查询”，还不是“带聊天记忆的多轮对话”。
    response = model.invoke([
        system_message,
        HumanMessage(content=question),
    ])

    print("\nDeepSeek 最终回答：")
    print(response.content)


# 本课的核心变化：
# 程序启动时：读取索引、加载 BGE、创建 DeepSeek 模型，只执行一次。
# 每个问题：重新生成 query_embedding，并重新执行一次父子检索。
# 输入退出词：break 离开 while 循环，程序结束。
