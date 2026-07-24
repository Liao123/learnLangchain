"""模块 25：把 Markdown 知识库重新构建成当前应用可读取的父子索引。

本文件故意把构建过程完整写开。后面的 app/index_builder.py 才把同一逻辑收起来复用。
"""

# hashlib：Python 自带库。这里用它查看“重新构建前后”的索引版本是否变化。
import hashlib
# json：Python 自带库。负责读取元数据、保存最终索引 JSON。
import json
from pathlib import Path

# 这两个库已经在前面的父子检索课用过：
# RecursiveCharacterTextSplitter 负责把长章节切成短子片段；SentenceTransformer 负责把文字变成 BGE 向量。
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


# LESSON_DIR 的实际值大致是：RAGDemo/lessons/25_重建当前应用索引。
LESSON_DIR = Path(__file__).resolve().parent
# parents[2] 从 lessons/25_重建当前应用索引 回到 RAGDemo 根目录。
RAG_ROOT = LESSON_DIR.parents[1]

# 当前 rag_cli.py 真正使用的是这份较长的 Markdown，不是 data/source/咖啡店知识库.md。
source_file = RAG_ROOT / "data" / "source" / "长文档示例.md"
# 元数据没有放进索引 JSON；应用读取索引时会单独读取它，所以构建前必须检查编号能对上。
metadata_file = RAG_ROOT / "data" / "indexes" / "父子知识库元数据.json"
# Demo 不覆盖应用索引，只在本课目录生成一份演示结果。
demo_index_file = LESSON_DIR / "演示父子知识库索引.json"

embedding_model_name = "BAAI/bge-small-zh-v1.5"
child_chunk_size = 100
child_chunk_overlap = 20


def make_short_version(index_file: Path) -> str:
    """读取整个 JSON 文件字节，生成例如 index-001e7af6fbec 的短版本号。"""
    # read_bytes() 的值像 b'{\n  "embedding_model": ...}'，是完整文件内容的字节版。
    # hexdigest() 会得到 64 个字符；这里只取前 12 个，让输出和缓存 key 更短。
    file_hash = hashlib.sha256(index_file.read_bytes()).hexdigest()
    return f"index-{file_hash[:12]}"


def split_into_parent_sections(markdown_text: str) -> tuple[str, list[dict]]:
    """按 Markdown 二级标题拆出父章节。"""
    # 当前资料按 "\n## " 拆分后，parts 大致是：
    # ["# 星光咖啡店长文档示例", "退款办理规则\n...", "现制饮品与订单修改\n...", ...]。
    parts = markdown_text.split("\n## ")
    document_title = parts[0].strip()
    parents = []

    # enumerate(..., start=1) 会依次给出 (1, 第一章文字)、(2, 第二章文字) ...。
    for parent_number, section_text in enumerate(parts[1:], start=1):
        lines = section_text.strip().splitlines()
        if not lines:
            continue

        # 当前第一章会得到 title="退款办理规则"；正文会保留这一章的所有规则。
        title = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        parents.append({
            "parent_id": f"parent_{parent_number}",
            "title": title,
            "content": content,
        })

    return document_title, parents


def validate_metadata(parent_sections: list[dict], metadata_by_parent_id: dict) -> None:
    """新增或删除章节时，阻止元数据和父章节编号错配。"""
    # set 是“不重复名单”。当前 parent_ids 的值是 {"parent_1", "parent_2", "parent_3", "parent_4"}。
    parent_ids = {parent["parent_id"] for parent in parent_sections}
    metadata_ids = set(metadata_by_parent_id)

    # 例如新增加一个章节后，missing_ids 可能是 {"parent_5"}。
    missing_ids = parent_ids - metadata_ids
    # 例如删除章节但忘记删元数据后，extra_ids 可能是 {"parent_4"}。
    extra_ids = metadata_ids - parent_ids

    if missing_ids or extra_ids:
        raise ValueError(
            "父章节和元数据编号不一致。"
            f"缺少元数据：{sorted(missing_ids)}；多余元数据：{sorted(extra_ids)}。"
            "请先更新 data/indexes/父子知识库元数据.json，再重新构建。"
        )


# 1. 读取当前应用实际使用的原始 Markdown。
source_text = source_file.read_text(encoding="utf-8")

# 2. 先得到完整父章节。当前资料会得到 4 章，例如 parent_3 是“会员积分与优惠”。
document_title, parents = split_into_parent_sections(source_text)

# 3. 元数据只做安全检查，不参与 BGE 向量生成。
metadata_by_parent_id = json.loads(metadata_file.read_text(encoding="utf-8"))
validate_metadata(parents, metadata_by_parent_id)

# 4. 每个完整章节再切成约 100 个字符的子片段，供检索时精确匹配。
child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=child_chunk_size,
    chunk_overlap=child_chunk_overlap,
    length_function=len,
    is_separator_regex=False,
    separators=["。", "！", "？", "；", "，", " ", ""],
)

children = []
for parent in parents:
    # 例如 parent_1 的 223 个字符正文，会拆成 3 个 child_text。
    child_texts = child_splitter.split_text(parent["content"])

    for child_text in child_texts:
        child_number = len(children) + 1
        # 子片段离开原文后，也要知道自己属于哪个文档、哪个章节。
        embedding_text = (
            f"文档：{document_title}\n"
            f"章节：{parent['title']}\n"
            f"内容：{child_text}"
        )
        children.append({
            "child_id": f"child_{child_number}",
            "parent_id": parent["parent_id"],
            "content": child_text,
            "embedding_text": embedding_text,
        })

print("读取的 Markdown：", source_file.name)
print("完整父章节数：", len(parents), "（当前应为 4）")
print("可检索子片段数：", len(children), "（当前应为 9）")
print("第一章：", parents[0]["parent_id"], "->", parents[0]["title"])

# 5. BGE 只给子片段生成向量。local_files_only=True 表示优先只使用本机已经下载的模型。
try:
    embedding_model = SentenceTransformer(embedding_model_name, local_files_only=True)
    print("BGE 模型来源：本地缓存")
except OSError:
    # 电脑第一次没有模型缓存时，才允许下载。
    embedding_model = SentenceTransformer(embedding_model_name)
    print("BGE 模型来源：联网下载")

# 列表中的第 0 项就是 child_1 的 embedding_text；当前一共有 9 项文字。
child_embedding_texts = [child["embedding_text"] for child in children]
child_embeddings = embedding_model.encode(
    child_embedding_texts,
    normalize_embeddings=True,
)
print("BGE 向量形状：", child_embeddings.shape, "（9 条子片段，每条通常 512 个数字）")

# 6. 把“完整章节 + 子片段 + 向量”保存为一个配套的索引 JSON。
index_data = {
    "embedding_model": embedding_model_name,
    "source_file": source_file.name,
    "document_title": document_title,
    "child_chunk_size": child_chunk_size,
    "child_chunk_overlap": child_chunk_overlap,
    "parents": parents,
    "children": children,
    # tolist() 把 numpy 向量转成 JSON 能保存的普通列表，例如 [0.012, -0.034, ...]。
    "child_embeddings": child_embeddings.tolist(),
}

old_version = make_short_version(demo_index_file) if demo_index_file.exists() else "（第一次运行，没有旧演示索引）"
demo_index_file.write_text(
    json.dumps(index_data, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
new_version = make_short_version(demo_index_file)

print("\n演示索引已写入：", demo_index_file.name)
print("构建前演示版本：", old_version)
print("构建后演示版本：", new_version)
print("\n本课 demo 只写 lessons/25_重建当前应用索引/，没有修改 app 正在使用的索引。")

