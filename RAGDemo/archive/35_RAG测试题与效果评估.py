# json：读取父子知识库索引。
import json

# Path：定位当前脚本同目录中的索引文件。
from pathlib import Path

# numpy：把 JSON 中的向量列表转回 NumPy 数组。
import numpy as np

# SentenceTransformer：把测试问题转换成语义向量。
# util：在全部子片段向量中查找最相近的结果。
from sentence_transformers import SentenceTransformer, util


# 第 28 课构建的父子索引文件，和当前归档脚本放在同一文件夹。
index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："

top_k = 3
# 练习起点。改这个值后，必须重新跑下面所有题，不要只看其中一题。
min_relevance_score = 0.50

# 每个字典是一道固定题。
# expected_parent 写标题表示期待找回该章节；写 None 表示期待程序拒答。
test_cases = [
    {
        "name": "退款规则",
        "question": "购买后五天、还没有拆封的咖啡豆可以退款吗？",
        "expected_parent": "退款办理规则",
    },
    {
        "name": "会员福利",
        "question": "金卡会员每消费一元能获得几倍积分？",
        "expected_parent": "会员积分与优惠",
    },
    {
        "name": "周末营业时间",
        "question": "周六和周日营业到几点？",
        "expected_parent": "营业时间与到店服务",
    },
    {
        "name": "故意失败：知识库外的问题",
        "question": "店里能维修电脑吗？",
        "expected_parent": None,
    },
]


# ==================== 程序启动时只执行一次 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
parents = index_data["parents"]
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)
parents_by_id = {
    parent["parent_id"]: parent
    for parent in parents
}

print("已读取父子索引：", index_file.name)
print("正在加载 BGE 向量模型...")
embedding_model = SentenceTransformer(index_data["embedding_model"])
print(f"相似度阈值：{min_relevance_score}")

passed_count = 0
case_number = 0


# ==================== 逐题检查 ====================

for test_case in test_cases:
    case_number += 1
    question = test_case["question"]

    # 每道题都像平常一样做一次子片段检索。
    query_embedding = embedding_model.encode(
        [query_instruction + question],
        normalize_embeddings=True,
    )
    raw_results = util.semantic_search(
        query_embedding,
        child_embeddings,
        top_k=top_k,
    )[0]

    best_score = raw_results[0]["score"] if raw_results else None
    passed_results = [
        result
        for result in raw_results
        if result["score"] >= min_relevance_score
    ]

    # actual_titles 保存这道题实际找回的章节标题。
    actual_titles = []
    seen_parent_ids = set()
    for result in passed_results:
        child = children[result["corpus_id"]]
        parent_id = child["parent_id"]

        # 同一父章节可能有多个子片段命中，但章节标题只需要记一次。
        if parent_id in seen_parent_ids:
            continue

        seen_parent_ids.add(parent_id)
        actual_titles.append(parents_by_id[parent_id]["title"])

    expected_parent = test_case["expected_parent"]
    if expected_parent is None:
        # 知识库外的问题，没有找回任何章节才是正确结果。
        passed = len(actual_titles) == 0
    else:
        passed = expected_parent in actual_titles

    print(f"\n第 {case_number} 题：{test_case['name']}")
    print("问题：", question)
    print(f"最高相似度：{best_score:.4f}")

    if expected_parent is None:
        print("期待：不找回任何章节，直接拒答")
    else:
        print("期待章节：", expected_parent)

    if actual_titles:
        print("实际找回：", "、".join(actual_titles))
    else:
        print("实际找回：没有章节")

    if passed:
        print("结果：通过")
        passed_count += 1
    else:
        print("结果：失败")

print(f"\n测试总结：{passed_count} / {len(test_cases)} 题通过")
print("本课只检查检索和拒答，不调用 DeepSeek。")


# 本课重点：
# 1. 固定测试题能帮助你比较改动前后的检索效果。
# 2. 成功题检查“该找的有没有找对”，故意失败题检查“该拒答时有没有拒答”。
# 3. 测试失败时先看相似度和实际章节，再决定要不要调整阈值、切块或资料内容。