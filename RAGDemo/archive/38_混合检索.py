"""第 38 课归档：把 BGE 语义检索和 BM25 关键词检索合在一起。"""

# json：读取父子知识库索引 JSON。
import json

# Path：定位当前 archive 文件夹中的索引文件。
from pathlib import Path

# numpy：把 JSON 中的向量列表还原为 NumPy 数组。
import numpy as np

# SentenceTransformer：加载 BGE，把问题变成向量。
# util.semantic_search()：把问题向量和资料向量做相似度检索。
from sentence_transformers import SentenceTransformer, util

# jieba：中文分词。lcut("金卡会员") 会得到一个词列表。
# BM25Okapi：根据关键词是否命中来给每段资料评分。
try:
    import jieba
    from rank_bm25 import BM25Okapi
except ImportError as error:
    raise RuntimeError(
        "第 38 课需要额外安装 jieba 和 rank-bm25。"
        "请运行：py -m pip install jieba rank-bm25"
    ) from error


# __file__ 是当前 38_混合检索.py 的位置；with_name() 把文件名换成索引文件名。
index_file = Path(__file__).with_name("父子知识库索引.json")

# BGE 在这个项目里需要给查询加的指令。
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 本题有精确词“九折优惠、限时促销”，也有“能一起使用吗”这种自然问法。
question = "金卡会员的九折优惠能和限时促销一起使用吗？"

# 两种方法各找前三条资料。
top_k = 3


# ==================== 程序启动：读取资料和 BGE 向量 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)

print("正在加载 BGE 向量模型...")
embedding_model = SentenceTransformer(index_data["embedding_model"])


# ==================== 第一步：BGE 语义检索 ====================

# encode() 把问题变成一个数字向量。BGE 擅长找到“意思相近”的资料。
query_embedding = embedding_model.encode(
    [query_instruction + question],
    normalize_embeddings=True,
)

# semantic_search() 用查询向量与所有子片段向量比较，得到按 BGE 分数排序的前三条。
bge_search_results = util.semantic_search(
    query_embedding,
    child_embeddings,
    top_k=top_k,
)[0]

bge_matches = []
for result in bge_search_results:
    child = children[result["corpus_id"]]
    bge_matches.append({
        "score": result["score"],
        "child": child,
    })


# ==================== 第二步：BM25 关键词检索 ====================

# BM25 需要词列表，而不是 BGE 向量。
# 例如 child_6 的文字会被切成 ["金卡", "会员", "每", "消费", "一元", ...] 这样的列表。
tokenized_children = []
for child in children:
    tokenized_children.append(jieba.lcut(child["content"]))

# 把 9 个子片段的分词结果交给 BM25，建立关键词索引。
bm25_index = BM25Okapi(tokenized_children)

# 同样把用户问题分词。question_tokens 就是 BM25 实际拿来查资料的关键词。
question_tokens = jieba.lcut(question)
bm25_scores = bm25_index.get_scores(question_tokens)

# range(len(bm25_scores)) 给出每一段资料的位置：0 对应 child_1，5 对应 child_6。
# sorted(..., key=..., reverse=True) 按 BM25 分数从高到低重新排列这些位置。
bm25_ranked_indices = sorted(
    range(len(bm25_scores)),
    key=lambda child_index: bm25_scores[child_index],
    reverse=True,
)[:top_k]

bm25_matches = []
for child_index in bm25_ranked_indices:
    bm25_matches.append({
        "score": float(bm25_scores[child_index]),
        "child": children[child_index],
    })


# ==================== 第三步：RRF 按名次合并 ====================

# 不能直接把 BGE 分数和 BM25 分数相加：它们来自不同算法，数字大小不在同一把尺子上。
# 所以建立这个字典：键是 child_id，值是该资料目前累积到的合并信息。
merged_by_child_id = {}

# 这里有两份排序结果：BGE 的 bge_matches 与 BM25 的 bm25_matches。
# items() 会依次取出：("bge", bge_matches)，再取出 ("bm25", bm25_matches)。
for source_name, matches in {"bge": bge_matches, "bm25": bm25_matches}.items():
    # start=1 让第一名的 rank 是 1，而不是 Python 默认的 0。
    for rank, match in enumerate(matches, start=1):
        child = match["child"]
        child_id = child["child_id"]

        # 同一资料第一次出现时，创建它的记录。
        if child_id not in merged_by_child_id:
            merged_by_child_id[child_id] = {
                "child": child,
                "rrf_score": 0.0,
                "bge_rank": None,
                "bm25_rank": None,
            }

        merged_match = merged_by_child_id[child_id]

        # RRF：第 1 名加 1/(60+1)，第 2 名加 1/(60+2)。
        # 如果 child_6 同时是 BGE 第 1、BM25 第 1，它会加两次分，所以更靠前。
        merged_match["rrf_score"] += 1 / (60 + rank)
        merged_match[f"{source_name}_rank"] = rank

# values() 拿出所有合并记录；再按 RRF 分数从高到低排序。
fused_matches = list(merged_by_child_id.values())
fused_matches.sort(
    key=lambda match: match["rrf_score"],
    reverse=True,
)


def format_rank(rank: int | None) -> str:
    """把 1、2、3 或 None 变成适合终端阅读的名次文字。"""
    # None 说明这条资料没有进入那种检索的前三名。
    if rank is None:
        return "未进前三"
    return f"第 {rank} 名"


# ==================== 第四步：输出真实运行过程 ====================

print("\n用户问题：", question)
print("BM25 看到的问题词：", question_tokens)
print("child_6 被 BM25 分出的词：", tokenized_children[5])

print("\nBGE 语义检索：")
for rank, match in enumerate(bge_matches, start=1):
    print(f"{rank}. {match['child']['child_id']}，BGE 分数：{match['score']:.4f}")
    print("   ", match["child"]["content"])

print("\nBM25 关键词检索：")
for rank, match in enumerate(bm25_matches, start=1):
    print(f"{rank}. {match['child']['child_id']}，BM25 分数：{match['score']:.4f}")
    print("   ", match["child"]["content"])

print("\n混合后的最终顺序（RRF）：")
for rank, match in enumerate(fused_matches, start=1):
    print(
        f"{rank}. {match['child']['child_id']}，"
        f"BGE {format_rank(match['bge_rank'])}，"
        f"BM25 {format_rank(match['bm25_rank'])}，"
        f"RRF 分数：{match['rrf_score']:.6f}"
    )
    print("   ", match["child"]["content"])


# 本课重点：
# 1. BGE 用向量找“意思相近”的资料。
# 2. BM25 用分词找“包含同样关键词”的资料。
# 3. RRF 按名次合并，避免混用两种不在同一尺度上的分数。
# 4. 混合检索仍要配合相似度阈值，避免知识库外问题被硬答。
