# json：Python 自带模块，用来把 Python 数据保存成 JSON 文件。
import json

# Path：更可靠地处理文件路径。
from pathlib import Path

# SentenceTransformer：加载 BGE 嵌入模型，把资料片段转换成语义向量。
from sentence_transformers import SentenceTransformer


# __file__ 表示“当前这个 Python 文件”。
# with_name(...) 表示使用与当前 Python 文件同一个文件夹中的指定文件。
# 这样无论从哪个 PowerShell 文件夹运行程序，都能找到 RAGDemo 中的知识库。
knowledge_file = Path(__file__).with_name("咖啡店知识库.md")

# 本程序要生成的索引文件名称。
# 它会保存“原始片段 + 每段的语义向量”，供下一课查询使用。
index_file = Path(__file__).with_name("咖啡店知识库索引.json")

# 使用较小的中文 BGE 模型，适合本地学习和语义检索。
embedding_model_name = "BAAI/bge-small-zh-v1.5"


def split_markdown_into_chunks(markdown_text: str) -> list[str]:
    """按 Markdown 的二级标题（##）把知识库切成多个资料片段。"""

    # split("\n## ")：按“换行 + 二级标题”切开 Markdown。
    sections = markdown_text.split("\n## ")

    # 准备空列表，用来保存切好的片段。
    chunks = []

    # sections[0] 是文档总标题；从 sections[1:] 开始才是实际知识内容。
    for section in sections[1:]:
        # strip()：去掉片段开头和结尾多余的空白与换行。
        clean_section = section.strip()

        # 跳过空片段。
        if clean_section:
            # append()：把资料片段加入列表。
            # 重新加上 ##，方便后面查看索引时辨认标题。
            chunks.append("## " + clean_section)

    return chunks


# read_text()：读取 Path 指向的文件内容。
# encoding="utf-8"：保证中文正常读取。
knowledge_text = knowledge_file.read_text(encoding="utf-8")

# 第一步：把知识库切块。
chunks = split_markdown_into_chunks(knowledge_text)

print("已读取知识库：", knowledge_file.name)
print("知识库被切成", len(chunks), "个片段。")


# 第二步：加载 BGE 嵌入模型。
# 如果电脑第一次使用该模型，会下载公开模型文件；以后会优先使用本地缓存。
embedding_model = SentenceTransformer(embedding_model_name)


# 第三步：只为“知识库片段”生成语义向量。
# normalize_embeddings=True：统一向量长度，方便下一课比较语义相似度。
document_embeddings = embedding_model.encode(
    chunks,
    normalize_embeddings=True,
)


# tolist()：把模型返回的 NumPy 数组转换成普通 Python 列表。
# JSON 文件只能直接保存普通列表、文字、数字等基础数据，不能直接保存 NumPy 数组。
index_data = {
    "embedding_model": embedding_model_name,
    "source_file": knowledge_file.name,
    "chunks": chunks,
    "embeddings": document_embeddings.tolist(),
}


# json.dumps()：把 Python 字典转换成 JSON 文字。
# ensure_ascii=False：让 JSON 保留中文，而不是变成 \u4e2d 这种编码。
# indent=2：让文件有缩进，方便人阅读和教学。
index_text = json.dumps(
    index_data,
    ensure_ascii=False,
    indent=2,
)

# write_text()：把 JSON 文字写入索引文件。
index_file.write_text(index_text, encoding="utf-8")


print("\n索引构建完成：", index_file.name)
print("索引中保存了", len(index_data["chunks"]), "个资料片段和对应的语义向量。")


# 什么时候运行本程序？
# - 第一次建立知识库时运行一次。
# - 修改、增加或删除知识库资料后，再运行一次更新索引。
# 用户日常提问时不运行本程序；下一课会只读取这个索引来回答问题。
