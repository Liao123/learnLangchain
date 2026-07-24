# json：读取父子知识库索引和元数据标签。
import json

# Path：定位当前脚本同目录中的 JSON 文件。
from pathlib import Path

# numpy：把索引里的向量列表转成 NumPy 数组。
import numpy as np

# SentenceTransformer：把用户问题变成语义向量。
# util：在允许参加检索的子片段中找最相近的结果。
from sentence_transformers import SentenceTransformer, util


index_file = Path(__file__).with_name("父子知识库索引.json")
metadata_file = Path(__file__).with_name("父子知识库元数据.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："
min_relevance_score = 0.50

# 订单系统已经知道用户买的是现制饮品。
# 本课用这个条件先筛资料，再做相似度检索。
metadata_filters = {"商品类型": "现制饮品"}
question = "可以退款吗？"


# ==================== 程序启动时只执行一次 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
metadata_by_parent_id = json.loads(metadata_file.read_text(encoding="utf-8"))
parents = index_data["parents"]
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)

parents_by_id = {}
for parent in parents:
    # 把每个父章节的标签加进 parent 字典，后面筛选时直接读取。
    parent["metadata"] = metadata_by_parent_id[parent["parent_id"]]
    parents_by_id[parent["parent_id"]] = parent

print("已读取父子索引：", index_file.name)
print("订单已知条件：", metadata_filters)
print("正在加载 BGE 向量模型...")
embedding_model = SentenceTransformer(index_data["embedding_model"])


# ==================== 先按元数据筛选 ====================

# candidate_child_indices 保存允许参加本轮检索的子片段下标。
candidate_child_indices = []
for child_index in range(len(children)):
    child = children[child_index]
    parent = parents_by_id[child["parent_id"]]

    # items() 会拿出每个“字段名 + 期待值”。所有条件都符合才保留。
    matches_all_filters = True
    for field_name, expected_value in metadata_filters.items():
        if parent["metadata"].get(field_name) != expected_value:
            matches_all_filters = False
            break

    if matches_all_filters:
        candidate_child_indices.append(child_index)

if not candidate_child_indices:
    print("没有任何资料符合这个元数据条件，本次应该直接拒答。")

else:
    # 只把通过元数据筛选的向量交给 semantic_search()。
    candidate_embeddings = child_embeddings[candidate_child_indices]
    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )
    candidate_results = util.semantic_search(
        query_embedding,
        candidate_embeddings,
        top_k=min(3, len(candidate_child_indices)),
    )[0]

    print("\n用户问题：", question)
    print("允许参加检索的子片段数量：", len(candidate_child_indices))
    print(f"最高子片段相似度：{candidate_results[0]['score']:.4f}")

    seen_parent_ids = set()
    retrieved_parents = []
    for candidate_result in candidate_results:
        # corpus_id 是筛选后列表的下标，要换回原始 children 列表的下标。
        original_child_index = candidate_child_indices[candidate_result["corpus_id"]]
        child = children[original_child_index]
        parent_id = child["parent_id"]

        if parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)
        retrieved_parents.append(parents_by_id[parent_id])

    print("\n实际找回的章节：")
    for parent in retrieved_parents:
        print("-", parent["title"])


# 本课重点：
# 1. 元数据过滤先缩小资料范围，再由 BGE 做语义比较。
# 2. 系统已知的订单类型、门店、权限等信息，比让 AI 猜更可靠。
# 3. 没有资料符合过滤条件时，应直接拒答，不能退回到全部资料里乱找。