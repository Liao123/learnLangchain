"""第 54 课归档：重建索引后，检查固定题是否仍能找对资料。"""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util


archive_dir = Path(__file__).resolve().parent
index_file = archive_dir / "父子知识库索引.json"
report_file = archive_dir / "检索回归测试报告.json"
model_name = "BAAI/bge-small-zh-v1.5"
min_relevance_score = 0.50
test_cases = [
    {"名称": "退款规则", "问题": "购买后五天、还没有拆封的咖啡豆可以退款吗？", "期待章节": "退款办理规则"},
    {"名称": "会员福利", "问题": "金卡会员每消费一元能获得几倍积分？", "期待章节": "会员积分与优惠"},
    {"名称": "周末营业时间", "问题": "周六和周日营业到几点？", "期待章节": "营业时间与到店服务"},
    {"名称": "知识库外的问题", "问题": "店里能维修电脑吗？", "期待章节": None},
]

index_data = json.loads(index_file.read_text(encoding="utf-8"))
parents_by_id = {parent["parent_id"]: parent for parent in index_data["parents"]}
# JSON 里的向量是普通列表；numpy 数字矩阵才能交给 semantic_search 比较。
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)

try:
    embedding_model = SentenceTransformer(model_name, local_files_only=True)
except OSError:
    embedding_model = SentenceTransformer(model_name)

reports = []
for test_case in test_cases:
    query_embedding = embedding_model.encode(
        ["为这个句子生成表示以用于检索相关文章：" + test_case["问题"]],
        normalize_embeddings=True,
    )
    raw_results = util.semantic_search(query_embedding, child_embeddings, top_k=3)[0]
    parents = []
    seen_parent_ids = set()
    for raw_result in raw_results:
        if raw_result["score"] < min_relevance_score:
            continue
        parent_id = index_data["children"][raw_result["corpus_id"]]["parent_id"]
        if parent_id not in seen_parent_ids:
            seen_parent_ids.add(parent_id)
            parents.append(parents_by_id[parent_id])

    actual_titles = [parent["title"] for parent in parents]
    expected_title = test_case["期待章节"]
    passed = len(actual_titles) == 0 if expected_title is None else expected_title in actual_titles
    reports.append({
        "名称": test_case["名称"],
        "期待章节": expected_title,
        "实际章节": actual_titles,
        "通过": passed,
    })
    print(f"{'通过' if passed else '失败'}：{test_case['名称']}")

passed_count = sum(report["通过"] for report in reports)
report_file.write_text(
    json.dumps({"通过数量": passed_count, "总题数": len(reports), "结果": reports}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"回归测试：{passed_count} / {len(reports)} 题通过")
print("报告文件：", report_file.name)
