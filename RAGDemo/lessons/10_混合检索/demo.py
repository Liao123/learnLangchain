"""第 38 课：把 BGE 语义检索和 BM25 关键词检索合在一起。"""

# sys：Python 用它临时增加“去哪里找其他 Python 文件”的位置。
import sys

# Path：用来处理文件夹路径，比手动拼接字符串更不容易写错。
from pathlib import Path

# jieba：中文分词。它把“金卡会员的九折优惠”拆成一组词，给 BM25 使用。
import jieba

# BM25Okapi：关键词检索算法。它根据词有没有出现在资料中、出现多少次来评分。
from rank_bm25 import BM25Okapi


# __file__ 就是当前 demo.py 的路径。
# parents[2] 表示从 demo.py 往上走两层，得到 RAGDemo 文件夹。
RAG_ROOT = Path(__file__).resolve().parents[2]

# rag_core.py 放在 RAGDemo/app/ 中。
# insert(0, ...) 把 app 放到 Python 最先查找的位置，下面才能 import 它。
sys.path.insert(0, str(RAG_ROOT / "app"))

# 这三个函数是前面课程已经学过的“读索引、加载 BGE、BGE 语义检索”。
# 本课新学的 BM25 与 RRF 会直接写在这个 demo 里，不先封装。
from 检索核心.rag_core import (
    load_embedding_model,
    load_parent_child_index,
    retrieve_parent_context,
)


# 这题同时有精确关键词“九折优惠、限时促销”，也有口语化问法“一起使用吗”。
# 所以适合同时观察关键词检索和语义检索。
question = "金卡会员的九折优惠能和限时促销一起使用吗？"

# top_k=3 表示每种检索方式各自先拿出前三个子片段，再交给 RRF 合并。
top_k = 3

# index_data 是一个大字典，里面有：
# - index_data["children"]：9 个子片段的文字，例如 child_6 写着“金卡会员……九折优惠……限时促销”。
# - index_data["child_embeddings"]：这 9 个子片段早已算好的 BGE 向量。
# - index_data["parents_by_id"]：通过 parent_id 找完整章节的查询表。
index_data = load_parent_child_index()

print("正在加载 BGE 向量模型...")
# 左边两个变量接住函数返回的两个值：BGE 模型对象和它的来源。
# model_source 可能是本地模型路径，也可能是 "BAAI/bge-small-zh-v1.5"。
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])

# -------------------- 第一步：BGE 看语义 --------------------

# BGE 会把 question 变成查询向量，再和 9 个已有的资料向量比较。
# bge_result 是结果包；本课主要取 bge_result["matched_children"]。
# 它大致像：[{"score": 0.8, "child": {"child_id": "child_6", ...}}, ...]。
bge_result = retrieve_parent_context(
    question,
    index_data,
    embedding_model,
    top_k=top_k,
)

# -------------------- 第二步：BM25 看关键词 --------------------

# 这一步不调用 embedding_model.encode()。
# BM25 先把“每一段资料”切成词；例如 child_6 会被拆成 ["普通", "会员", ..., "九折", "优惠", ...]。
# tokenized_children 是一个二维列表：外层有 9 项，分别对应 9 个 child；每一项里面是那段资料的词。
tokenized_children = []
for child in index_data["children"]:
    # jieba.lcut() 的返回值是列表。这里把当前 child 的分词结果追加到总列表。
    tokenized_children.append(jieba.lcut(child["content"]))

# 把 9 段资料的分词结果交给 BM25，创建一个“关键词索引”。
# bm25_index 之后会记住哪些词出现在哪些资料中，不需要 BGE 向量。
bm25_index = BM25Okapi(tokenized_children)

# 问题也要用完全相同的方式分词。
# 这个变量的真实数据大致是：["金卡", "会员", "的", "九折", "优惠", "能", "和", "限时", "促销", ...]。
question_tokens = jieba.lcut(question)

# get_scores() 会给每一个 child 一分，因此 bm25_scores 也有 9 个数。
# 例如 bm25_scores[5] 是 child_6 的 BM25 分数，因为 Python 列表从 0 开始。
bm25_scores = bm25_index.get_scores(question_tokens)

# range(len(bm25_scores)) 先得到 0 到 8，分别代表 9 个 child 的位置。
# sorted(..., key=..., reverse=True) 按 BM25 分数从高到低排这些位置；[:top_k] 只留下前三名位置。
bm25_ranked_indices = sorted(
    range(len(bm25_scores)),
    key=lambda child_index: bm25_scores[child_index],
    reverse=True,
)[:top_k]

# 把“位置 + 分数”换成和 BGE 结果相似的资料包，后面才能一起展示、一起合并。
# 第一项大致会是：{"score": 13.9, "child": {"child_id": "child_6", ...}}。
bm25_matches = []
for child_index in bm25_ranked_indices:
    bm25_matches.append({
        "score": float(bm25_scores[child_index]),
        "child": index_data["children"][child_index],
    })

# -------------------- 第三步：RRF 合并两个排序 --------------------

# 不能把 BGE 的 0.x 分数和 BM25 的 10.x 分数直接相加：两种算法的分数不是同一把尺子。
# 所以我们建立一个字典，键是 child_id，值是这条资料目前拿到的 RRF 分数和各自名次。
merged_by_child_id = {}

# 这里先做一个小字典，实际值大致是：
# {"bge": [BGE 前三条], "bm25": [BM25 前三条]}。
# items() 每次拿出“方法名 + 那个方法的结果列表”。
for source_name, matches in {
    "bge": bge_result["matched_children"],
    "bm25": bm25_matches,
}.items():
    # enumerate(..., start=1) 让每条资料得到第 1、2、3 名，而不是 Python 默认的 0、1、2。
    for source_rank, match in enumerate(matches, start=1):
        child = match["child"]
        child_id = child["child_id"]

        # 同一条资料可能被两种方法都找到。
        # 只有第一次见到它时才新建记录，第二次见到时就往同一份记录继续加分。
        if child_id not in merged_by_child_id:
            merged_by_child_id[child_id] = {
                "child": child,
                "rrf_score": 0.0,
                "bge_rank": None,
                "bm25_rank": None,
            }

        merged_match = merged_by_child_id[child_id]

        # RRF 的公式是 1 / (60 + 名次)。第 1 名加 1/61，第 2 名加 1/62。
        # child_6 若同时是 BGE 第 1、BM25 第 1，就会加两次 1/61，因此更靠前。
        merged_match["rrf_score"] += 1 / (60 + source_rank)

        # f"{source_name}_rank" 会根据 source_name 变成 "bge_rank" 或 "bm25_rank"。
        # 这样一条合并记录会同时保存它在两种方法里的名次。
        merged_match[f"{source_name}_rank"] = source_rank

# values() 取出字典中的全部合并记录；list(...) 把它变回可以排序的列表。
fused_matches = list(merged_by_child_id.values())

# sort() 就地排序。key=... 表示按 rrf_score 排，reverse=True 表示分数高的放前面。
fused_matches.sort(
    key=lambda match: match["rrf_score"],
    reverse=True,
)


def format_rank(rank: int | None) -> str:
    """把名次数字或 None 变成适合直接看的中文。"""
    # None 说明它没进入这一种检索的前三名；终端显示“未进前三”比“第 None 名”更清楚。
    if rank is None:
        return "未进前三"
    # 其他情况的 rank 会是 1、2 或 3，所以拼成“第 1 名”这类文字。
    return f"第 {rank} 名"


# -------------------- 第四步：把真实过程打印出来 --------------------

print("\n用户问题：", question)
print("BGE 模型来源：", model_source)
print("BM25 看到的问题词：", question_tokens)

# tokenized_children[5] 是 child_6 的分词结果，因为 Python 列表从 0 开始数。
# 这一行让你看到 BM25 真的不是在看完整句子，而是在看一串词。
print("child_6 被 BM25 分出的词：", tokenized_children[5])

print("\nBGE 语义检索：")
# enumerate(..., start=1) 会一边遍历列表，一边给第一、二、三条编号为 1、2、3。
for rank, match in enumerate(bge_result["matched_children"], start=1):
    print(f"{rank}. {match['child']['child_id']}，BGE 分数：{match['score']:.4f}")
    print("   ", match["child"]["content"])

print("\nBM25 关键词检索：")
for rank, match in enumerate(bm25_matches, start=1):
    print(f"{rank}. {match['child']['child_id']}，BM25 分数：{match['score']:.4f}")
    print("   ", match["child"]["content"])

print("\n混合后的最终顺序（RRF）：")
for rank, match in enumerate(fused_matches, start=1):
    # bge_rank / bm25_rank 是资料在对应列表里的名次。
    # None 表示这个方法的前三名里没有出现该资料，format_rank() 会显示成“未进前三”。
    print(
        f"{rank}. {match['child']['child_id']}，"
        f"BGE {format_rank(match['bge_rank'])}，"
        f"BM25 {format_rank(match['bm25_rank'])}，"
        f"RRF 分数：{match['rrf_score']:.6f}"
    )
    print("   ", match["child"]["content"])


# 本课重点：混合检索仍然只是“找资料”。
# 要让 AI 回答时，下一步仍要根据 fused_matches 找到对应的完整父章节，再把完整章节放进 SystemMessage。
