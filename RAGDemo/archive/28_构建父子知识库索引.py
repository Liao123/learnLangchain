# json：Python 自带模块，用于把 Python 数据保存成 JSON 文字。
import json

# Path：Python 自带的路径工具，用于定位当前程序旁边的资料和索引文件。
from pathlib import Path

# RecursiveCharacterTextSplitter：LangChain 提供的长文本切块工具。
from langchain_text_splitters import RecursiveCharacterTextSplitter

# SentenceTransformer：用于加载 BGE 嵌入模型，把文字转换成语义向量。
from sentence_transformers import SentenceTransformer


# 找到与当前 Python 文件处于同一文件夹的长文档。
source_file = Path(__file__).with_name("长文档示例.md")

# 这节课生成一个新的父子索引，不会覆盖前面生成的普通长文档索引。
index_file = Path(__file__).with_name("父子知识库索引.json")

# 本地中文嵌入模型名称。
embedding_model_name = "BAAI/bge-small-zh-v1.5"

# 子片段用于检索，所以要相对短小。
child_chunk_size = 100
child_chunk_overlap = 20


def split_into_parent_sections(markdown_text: str):
    """把 Markdown 文档中的每个二级标题章节保存为一个父章节。"""

    # split("\n## ")：遇到 Markdown 二级标题时切开文档。
    # parts[0] 是文档总标题，parts[1:] 是各个完整章节。
    parts = markdown_text.split("\n## ")

    # strip()：删除总标题开头和结尾多余的空白与换行。
    document_title = parts[0].strip()

    # 用普通 Python 列表保存所有父章节。
    parent_sections = []

    # enumerate(..., start=1)：遍历每个章节，同时从 1 开始生成编号。
    for parent_number, section_text in enumerate(parts[1:], start=1):
        clean_section = section_text.strip()

        # splitlines()：按照换行把章节转换成多行文字列表。
        # 第一行是章节标题，剩余行是章节正文。
        lines = clean_section.splitlines()

        # 如果遇到空章节，就跳过，避免访问不存在的 lines[0]。
        if not lines:
            continue

        section_title = lines[0].strip()

        # lines[1:]：取得标题后面的所有正文行。
        # "\n".join(...)：使用换行符把这些正文行重新连接成一整段文字。
        section_body = "\n".join(lines[1:]).strip()

        # 每个父章节都是一个 Python 字典。
        # parent_id 是父章节的唯一编号，后面子片段通过它找到所属父章节。
        parent_section = {
            "parent_id": f"parent_{parent_number}",
            "title": section_title,
            "content": section_body,
        }

        parent_sections.append(parent_section)

    # Python 函数可以一次返回两个结果。
    return document_title, parent_sections


# 读取完整 Markdown 文档。
source_text = source_file.read_text(encoding="utf-8")

# 第一层切分：按照二级标题得到完整的父章节。
document_title, parents = split_into_parent_sections(source_text)


# 创建负责生成子片段的切块器。
# 父章节用于提供完整上下文，子片段用于进行精确语义检索。
child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=child_chunk_size,
    chunk_overlap=child_chunk_overlap,
    length_function=len,
    is_separator_regex=False,
    separators=[
        "。",
        "！",
        "？",
        "；",
        "，",
        " ",
        "",
    ],
)


# 用于保存所有子片段。
children = []

# 第二层切分：把每个父章节的正文继续切成较短的子片段。
for parent in parents:
    child_texts = child_splitter.split_text(parent["content"])

    for child_text in child_texts:
        # len(children) 表示当前已经保存了多少个子片段。
        # 加 1 后可得到新子片段的编号。
        child_number = len(children) + 1

        # embedding_text 是真正交给 BGE 生成向量的文字。
        # 每个子片段都补上文档标题和父章节标题，使子片段离开原位置后仍知道自己的主题。
        embedding_text = (
            f"文档：{document_title}\n"
            f"章节：{parent['title']}\n"
            f"内容：{child_text}"
        )

        child = {
            "child_id": f"child_{child_number}",

            # 这是父子关系的关键字段。
            # 下一课检索到这个子片段后，会根据 parent_id 找回完整父章节。
            "parent_id": parent["parent_id"],

            # content 保存子片段的原始正文。
            "content": child_text,

            # embedding_text 保存加入标题信息后的检索文字。
            "embedding_text": embedding_text,
        }

        children.append(child)


print("已读取文档：", source_file.name)
print("文档总标题：", document_title)
print("父章节数量：", len(parents))
print("子片段数量：", len(children))


# 加载 BGE 嵌入模型。
embedding_model = SentenceTransformer(embedding_model_name)

# 列表推导式：依次取得每个子片段的 embedding_text。
# BGE 只为子片段生成向量，因为查询时需要先搜索短小、准确的子片段。
child_embedding_texts = [
    child["embedding_text"]
    for child in children
]

# encode()：把所有子片段的检索文字转换成语义向量。
child_embeddings = embedding_model.encode(
    child_embedding_texts,
    normalize_embeddings=True,
)


# 准备父子索引数据。
index_data = {
    "embedding_model": embedding_model_name,
    "source_file": source_file.name,
    "document_title": document_title,
    "child_chunk_size": child_chunk_size,
    "child_chunk_overlap": child_chunk_overlap,

    # parents 保存完整章节，负责在回答问题时提供完整上下文。
    "parents": parents,

    # children 保存短小片段以及它们各自的 parent_id，负责语义检索。
    "children": children,

    # child_embeddings[i] 永远对应 children[i]。
    "child_embeddings": child_embeddings.tolist(),
}


# json.dumps()：把 Python 字典转换成 JSON 字符串。
index_text = json.dumps(
    index_data,
    ensure_ascii=False,
    indent=2,
)

# write_text()：把 JSON 字符串写入父子索引文件。
index_file.write_text(index_text, encoding="utf-8")


print("\n父子知识库索引构建完成：", index_file.name)
print("保存了", len(parents), "个完整父章节。")
print("保存了", len(children), "个可检索子片段。")
print("保存了", len(child_embeddings), "个子片段语义向量。")


# 打印父子对应关系，方便观察 parent_id 是怎样把两层内容连接起来的。
print("\n父子对应关系：")
for child in children:
    print(
        child["child_id"],
        "->",
        child["parent_id"],
    )


# 本课的数据流程：
# 完整 Markdown 文档
# -> 按二级标题切成父章节
# -> 每个父章节继续切成多个子片段
# -> 子片段记录所属父章节的 parent_id
# -> BGE 只为子片段生成向量
# -> JSON 同时保存父章节、子片段、父子关系和子片段向量
#
# 下一课的数据流程：
# 用户问题
# -> 检索最相关的子片段
# -> 读取子片段的 parent_id
# -> 找回完整父章节
# -> 把完整父章节交给 AI 回答
