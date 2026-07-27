"""重建索引后，用固定题检查旧问题是否仍能找对资料。"""

import json
import sys
from pathlib import Path


QUALITY_DIR = Path(__file__).resolve().parent
APP_DIR = QUALITY_DIR.parents[0]
sys.path.insert(0, str(APP_DIR))

from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


TEST_CASES_FILE = QUALITY_DIR / "资料" / "检索回归测试题.json"
REPORT_FILE = QUALITY_DIR / "输出" / "检索回归测试报告.json"
MIN_RELEVANCE_SCORE = 0.50


def run_regression_tests(index_data: dict, embedding_model) -> dict:
    """运行全部固定题，并把每一题的期待结果和实际结果保存成报告。"""
    test_cases = json.loads(TEST_CASES_FILE.read_text(encoding="utf-8"))
    reports = []

    for test_case in test_cases:
        result = retrieve_parent_context(
            test_case["问题"],
            index_data,
            embedding_model,
            min_relevance_score=MIN_RELEVANCE_SCORE,
        )
        actual_titles = [parent["title"] for parent in result["parents"]]
        expected_title = test_case["期待章节"]
        passed = (
            len(actual_titles) == 0
            if expected_title is None
            else expected_title in actual_titles
        )
        reports.append({
            "名称": test_case["名称"],
            "问题": test_case["问题"],
            "期待章节": expected_title,
            "实际章节": actual_titles,
            "通过": passed,
        })
        print(f"{'通过' if passed else '失败'}：{test_case['名称']}")

    passed_count = sum(report["通过"] for report in reports)
    summary = {
        "通过数量": passed_count,
        "总题数": len(reports),
        "全部通过": passed_count == len(reports),
        "结果": reports,
    }
    REPORT_FILE.parent.mkdir(exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"回归测试：{passed_count} / {len(reports)} 题通过")
    print("报告文件：", REPORT_FILE)
    return summary


def main() -> None:
    index_data = load_parent_child_index()
    print("正在加载 BGE 向量模型...")
    embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
    print("BGE 模型来源：", model_source)
    summary = run_regression_tests(index_data, embedding_model)

    if not summary["全部通过"]:
        raise SystemExit("回归测试失败：请检查资料或索引后再启动聊天程序。")


if __name__ == "__main__":
    main()
