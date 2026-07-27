"""模块 26：每次重建知识库后，重新检查固定问题。"""

import json
import sys
from pathlib import Path


LESSON_DIR = Path(__file__).resolve().parent
RAG_ROOT = LESSON_DIR.parents[1]
sys.path.insert(0, str(RAG_ROOT / "app"))

# 检索本身已经学过；本课的新内容是“把固定题重复跑一遍，并保存通过/失败结果”。
from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


index_file = LESSON_DIR / "资料" / "父子知识库索引.json"
metadata_file = LESSON_DIR / "资料" / "父子知识库元数据.json"
test_cases_file = LESSON_DIR / "资料" / "测试题.json"
report_file = LESSON_DIR / "输出" / "回归测试报告.json"
min_relevance_score = 0.50


# JSON 里的值大致是：
# {"名称": "退款规则", "问题": "购买后五天...可以退款吗？", "期待章节": "退款办理规则"}。
test_cases = json.loads(test_cases_file.read_text(encoding="utf-8"))
index_data = load_parent_child_index(index_file, metadata_file)
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])

print("测试题数量：", len(test_cases))
print("BGE 模型来源：", model_source)

reports = []
for test_case in test_cases:
    # 例如本轮 question 的值是“周六和周日营业到几点？”。
    question = test_case["问题"]
    result = retrieve_parent_context(
        question,
        index_data,
        embedding_model,
        min_relevance_score=min_relevance_score,
    )

    # actual_titles 可能是 ["营业时间与到店服务"]；知识库外问题则是 []。
    actual_titles = [parent["title"] for parent in result["parents"]]
    expected_title = test_case["期待章节"]
    passed = (
        len(actual_titles) == 0
        if expected_title is None
        else expected_title in actual_titles
    )

    reports.append({
        "名称": test_case["名称"],
        "问题": question,
        "期待章节": expected_title,
        "实际章节": actual_titles,
        "通过": passed,
    })
    print(f"{'通过' if passed else '失败'}：{test_case['名称']}")

passed_count = sum(report["通过"] for report in reports)
report_file.parent.mkdir(exist_ok=True)
report_file.write_text(
    json.dumps(
        {
            "通过数量": passed_count,
            "总题数": len(reports),
            "结果": reports,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print(f"\n回归测试：{passed_count} / {len(reports)} 题通过")
print("报告文件：", report_file.name)
