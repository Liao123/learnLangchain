"""把当前应用的 Markdown 知识库重新构建成父子索引。"""

from pathlib import Path

from index_builder import build_parent_child_index, write_parent_child_index
from rag_core import get_index_content_version, load_embedding_model


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = PROJECT_ROOT / "data" / "source" / "长文档示例.md"
METADATA_FILE = PROJECT_ROOT / "data" / "indexes" / "父子知识库元数据.json"
INDEX_FILE = PROJECT_ROOT / "data" / "indexes" / "父子知识库索引.json"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
CHILD_CHUNK_SIZE = 100
CHILD_CHUNK_OVERLAP = 20


def main() -> None:
    # 构建前先记住旧版本。源文件没有变化时，重新构建后通常仍是同一个版本。
    old_version = get_index_content_version(INDEX_FILE) if INDEX_FILE.exists() else "（没有旧索引）"

    print("原始 Markdown：", SOURCE_FILE)
    print("元数据文件：", METADATA_FILE)
    print("旧索引版本：", old_version)
    print("正在加载 BGE 模型...")
    embedding_model, model_source = load_embedding_model(EMBEDDING_MODEL_NAME)
    print("BGE 模型来源：", model_source)

    # 元数据编号不匹配时 build_parent_child_index() 会抛出错误，下面的写入动作不会发生。
    index_data = build_parent_child_index(
        source_file=SOURCE_FILE,
        metadata_file=METADATA_FILE,
        embedding_model=embedding_model,
        embedding_model_name=EMBEDDING_MODEL_NAME,
        child_chunk_size=CHILD_CHUNK_SIZE,
        child_chunk_overlap=CHILD_CHUNK_OVERLAP,
    )
    write_parent_child_index(index_data, INDEX_FILE)
    new_version = get_index_content_version(INDEX_FILE)

    print("\n父子索引已更新：", INDEX_FILE)
    print("父章节数量：", len(index_data["parents"]))
    print("子片段数量：", len(index_data["children"]))
    print("新索引版本：", new_version)
    print("版本是否变化：", "是" if old_version != new_version else "否（原始资料没有变化）")
    print("请重新启动 rag_cli.py，让应用读取这份新索引。")


if __name__ == "__main__":
    main()
