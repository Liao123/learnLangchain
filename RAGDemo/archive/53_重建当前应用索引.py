"""第 53 课归档：从 Markdown 重建父子知识库索引。"""

import hashlib
import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


archive_dir = Path(__file__).resolve().parent
source_file = archive_dir / "长文档示例.md"
metadata_file = archive_dir / "父子知识库元数据.json"
index_file = archive_dir / "父子知识库索引.json"
embedding_model_name = "BAAI/bge-small-zh-v1.5"
child_chunk_size = 100
child_chunk_overlap = 20


def short_version(file: Path) -> str:
    return f"index-{hashlib.sha256(file.read_bytes()).hexdigest()[:12]}"


def split_into_parents(markdown_text: str) -> tuple[str, list[dict]]:
    parts = markdown_text.split("\n## ")
    document_title = parts[0].strip()
    parents = []
    for number, section_text in enumerate(parts[1:], start=1):
        lines = section_text.strip().splitlines()
        if lines:
            parents.append({
                "parent_id": f"parent_{number}",
                "title": lines[0].strip(),
                "content": "\n".join(lines[1:]).strip(),
            })
    return document_title, parents


source_text = source_file.read_text(encoding="utf-8")
document_title, parents = split_into_parents(source_text)
metadata_by_parent_id = json.loads(metadata_file.read_text(encoding="utf-8"))
parent_ids = {parent["parent_id"] for parent in parents}
metadata_ids = set(metadata_by_parent_id)
if parent_ids != metadata_ids:
    raise ValueError(
        f"父章节编号 {sorted(parent_ids)} 和元数据编号 {sorted(metadata_ids)} 不一致。"
    )

splitter = RecursiveCharacterTextSplitter(
    chunk_size=child_chunk_size,
    chunk_overlap=child_chunk_overlap,
    length_function=len,
    is_separator_regex=False,
    separators=["。", "！", "？", "；", "，", " ", ""],
)
children = []
for parent in parents:
    for child_text in splitter.split_text(parent["content"]):
        child_number = len(children) + 1
        children.append({
            "child_id": f"child_{child_number}",
            "parent_id": parent["parent_id"],
            "content": child_text,
            "embedding_text": (
                f"文档：{document_title}\n"
                f"章节：{parent['title']}\n"
                f"内容：{child_text}"
            ),
        })

try:
    embedding_model = SentenceTransformer(embedding_model_name, local_files_only=True)
    model_source = "本地缓存"
except OSError:
    embedding_model = SentenceTransformer(embedding_model_name)
    model_source = "联网下载"

embeddings = embedding_model.encode(
    [child["embedding_text"] for child in children],
    normalize_embeddings=True,
)
old_version = short_version(index_file) if index_file.exists() else "（没有旧索引）"
index_data = {
    "embedding_model": embedding_model_name,
    "source_file": source_file.name,
    "document_title": document_title,
    "child_chunk_size": child_chunk_size,
    "child_chunk_overlap": child_chunk_overlap,
    "parents": parents,
    "children": children,
    "child_embeddings": embeddings.tolist(),
}
index_file.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")

print("归档索引已更新：", index_file.name)
print("父章节数量：", len(parents))
print("子片段数量：", len(children))
print("BGE 模型来源：", model_source)
print("构建前版本：", old_version)
print("构建后版本：", short_version(index_file))

