# json：Python 自带模块，用来把 Python 数据转换成 JSON 文字。
import json

# Path：Python 自带的路径工具，用来定位当前程序旁边的资料文件和索引文件。
from pathlib import Path

# RecursiveCharacterTextSplitter：LangChain 提供的长文档切块工具。
# 它会按照我们给出的分隔符顺序，尽量在段落、换行和标点处切开文档。
from langchain_text_splitters import RecursiveCharacterTextSplitter

# SentenceTransformer：用来加载本地 BGE 嵌入模型。
# BGE 会把每个中文片段转换成一组表示语义的数字向量。
from sentence_transformers import SentenceTransformer


# __file__：当前这个 Python 文件自己的完整路径。
# with_name(...)：保留当前文件所在的文件夹，只把文件名替换掉。
source_file = Path(__file__).with_name("长文档示例.md")

# 本程序生成的新索引文件。
# 它与前面的“咖啡店知识库索引.json”分开，避免覆盖旧索引。
index_file = Path(__file__).with_name("长文档知识库索引.json")

# 本地中文嵌入模型名称。
embedding_model_name = "BAAI/bge-small-zh-v1.5"

# 为了方便观察，本课仍然使用较小的片段长度。
# 以后处理真正的大型资料时，需要根据资料内容和检索测试结果再调整。
chunk_size = 120
chunk_overlap = 30


# read_text()：读取 Markdown 文件中的全部文字。
# 返回值 source_text 是一个普通 Python 字符串 str。
source_text = source_file.read_text(encoding="utf-8")


# 创建长文档切块器。
text_splitter = RecursiveCharacterTextSplitter(
    # 每个片段的目标最大长度约为 120 个字符。
    chunk_size=chunk_size,

    # 相邻片段目标重叠约 30 个字符，降低一句话被边界切断后丢失上下文的风险。
    chunk_overlap=chunk_overlap,

    # 使用 Python 的 len() 计算字符串字符数量。
    length_function=len,

    # separators 中的内容都是普通文字，不是正则表达式。
    is_separator_regex=False,

    # 框架会按从上到下的顺序尝试分割。
    # 优先保留完整段落，其次是换行和完整句子，最后才按更小单位切分。
    separators=[
        "\n\n",
        "\n",
        "。",
        "！",
        "？",
        "；",
        "，",
        " ",
        "",
    ],
)


# split_text()：真正执行切块。
# 输入是一整篇 source_text，输出是字符串列表 chunks。
# 例如：chunks[0] 是第一个文字片段，chunks[1] 是第二个文字片段。
chunks = text_splitter.split_text(source_text)

print("已读取长文档：", source_file.name)
print("原文字符数：", len(source_text))
print("切块大小：", chunk_size)
print("目标重叠：", chunk_overlap)
print("实际切成：", len(chunks), "个片段")


# 加载 BGE 嵌入模型。
# 第一次使用时会下载模型；已经下载过时，会从电脑的模型缓存中加载。
embedding_model = SentenceTransformer(embedding_model_name)


# encode()：一次性把 chunks 中的所有文字片段转换成语义向量。
# 输入有几个文字片段，document_embeddings 中就会有几个对应的向量。
# 对应关系完全依靠相同的列表下标：
# chunks[0] <-> document_embeddings[0]
# chunks[1] <-> document_embeddings[1]
document_embeddings = embedding_model.encode(
    chunks,
    normalize_embeddings=True,
)


# 准备要保存到 JSON 文件中的 Python 字典。
index_data = {
    "embedding_model": embedding_model_name,
    "source_file": source_file.name,

    # 把本次切块参数也保存下来，以后看到索引就知道它是如何生成的。
    "chunk_size": chunk_size,
    "chunk_overlap": chunk_overlap,

    # 原始中文片段列表。
    "chunks": chunks,

    # tolist()：把 NumPy 数组转换成 JSON 能够保存的普通 Python 列表。
    "embeddings": document_embeddings.tolist(),
}


# json.dumps()：把 Python 字典转换成 JSON 格式的字符串。
# ensure_ascii=False：让中文原样显示。
# indent=2：增加缩进，让生成的 JSON 文件更容易阅读。
index_text = json.dumps(
    index_data,
    ensure_ascii=False,
    indent=2,
)

# write_text()：把 JSON 字符串写入索引文件。
index_file.write_text(index_text, encoding="utf-8")


print("\n长文档索引构建完成：", index_file.name)
print("索引中保存了", len(chunks), "个中文片段。")
print("索引中保存了", len(document_embeddings), "个对应的语义向量。")


# 显示前两个片段，方便观察切块结果，但不会把整个索引全部打印出来。
# chunks[:2]：从 chunks 开头最多取出两个片段。
# enumerate(..., start=1)：遍历片段，并让编号从 1 开始。
print("\n索引中的前两个片段：")
for chunk_number, chunk in enumerate(chunks[:2], start=1):
    print("\n" + "=" * 50)
    print(f"片段 {chunk_number}（{len(chunk)} 个字符）")
    print(chunk)


# 这一课的完整数据流程：
# Markdown 长文档
# -> RecursiveCharacterTextSplitter 切成重叠片段
# -> BGE 把每个片段转换成语义向量
# -> JSON 同时保存“中文片段 + 对应向量 + 切块参数”
#
# 本程序只在资料新建或更新后运行，不需要在用户每次提问时运行。
