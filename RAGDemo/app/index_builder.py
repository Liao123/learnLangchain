"""父子知识库索引的构建逻辑，供应用构建命令复用。"""

import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer


def split_into_parent_sections(markdown_text: str) -> tuple[str, list[dict]]:
    """按 Markdown 二级标题拆出完整父章节。"""
    parts = markdown_text.split("\n## ")
    document_title = parts[0].strip()
    parents = []

    for parent_number, section_text in enumerate(parts[1:], start=1):
        lines = section_text.strip().splitlines()
        if not lines:
            continue
        parents.append({
            "parent_id": f"parent_{parent_number}",
            "title": lines[0].strip(),
            "content": "\n".join(lines[1:]).strip(),
        })

    return document_title, parents


def validate_metadata(parent_sections: list[dict], metadata_file: Path) -> None:
    """防止新增、删除章节后仍使用错误的元数据编号。"""
    metadata_by_parent_id = json.loads(metadata_file.read_text(encoding="utf-8"))
    parent_ids = {parent["parent_id"] for parent in parent_sections}
    metadata_ids = set(metadata_by_parent_id)
    missing_ids = parent_ids - metadata_ids
    extra_ids = metadata_ids - parent_ids

    if missing_ids or extra_ids:
        raise ValueError(
            "父章节和元数据编号不一致。"
            f"缺少元数据：{sorted(missing_ids)}；多余元数据：{sorted(extra_ids)}。"
            f"请先更新 {metadata_file.name}，旧索引不会被覆盖。"
        )


def build_parent_child_index(
    source_file: Path,
    metadata_file: Path,
    embedding_model: SentenceTransformer,
    embedding_model_name: str,
    child_chunk_size: int = 100,
    child_chunk_overlap: int = 20,
) -> dict:
    """从 Markdown 生成完整父章节、可检索子片段和 BGE 向量。"""
    source_text = source_file.read_text(encoding="utf-8")
    document_title, parents = split_into_parent_sections(source_text)
    validate_metadata(parents, metadata_file)

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_chunk_size,
        chunk_overlap=child_chunk_overlap,
        length_function=len,
        is_separator_regex=False,
        separators=["。", "！", "？", "；", "，", " ", ""],
    )

    children = []
    for parent in parents:
        for child_text in child_splitter.split_text(parent["content"]):
            child_number = len(children) + 1
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

    child_embeddings = embedding_model.encode(
        [child["embedding_text"] for child in children],
        normalize_embeddings=True,
    )

    return {
        "embedding_model": embedding_model_name,
        "source_file": source_file.name,
        "document_title": document_title,
        "child_chunk_size": child_chunk_size,
        "child_chunk_overlap": child_chunk_overlap,
        "parents": parents,
        "children": children,
        "child_embeddings": child_embeddings.tolist(),
    }


def write_parent_child_index(index_data: dict, index_file: Path) -> None:
    """把 Python 索引字典写成应用可读取的 UTF-8 JSON 文件。"""
    index_file.write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
