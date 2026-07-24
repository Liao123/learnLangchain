"""用固定问题检查父子检索是否找对章节。"""

import sys
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 这个阈值和课程 Demo 保持一致。改了它以后，要重新运行全部测试题。
MIN_RELEVANCE_SCORE = 0.50

# 每个字典是一道固定测试题。
# expected_parent 写章节标题，表示这题应该找回哪一章。
# expected_parent 写 None，表示这题本来就不该找回任何章节。
TEST_CASES = [
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
        "name": "知识库外的问题",
        "question": "店里能维修电脑吗？",
        "expected_parent": None,
    },
]


def evaluate_case(test_case: dict, index_data: dict, embedding_model) -> dict:
    """运行一道题，并把期待结果和实际结果放进同一个字典。"""
    result = retrieve_parent_context(
        test_case["question"],
        index_data,
        embedding_model,
        min_relevance_score=MIN_RELEVANCE_SCORE,
    )

    # actual_titles 是本题实际找回的所有父章节标题。
    actual_titles = []
    for parent in result["parents"]:
        actual_titles.append(parent["title"])

    expected_parent = test_case["expected_parent"]
    if expected_parent is None:
        # None 表示期待“拒答”，所以一个章节也没有找回才算通过。
        passed = len(actual_titles) == 0
    else:
        # 只要期待的章节出现在实际结果里，这道题就算通过。
        passed = expected_parent in actual_titles

    return {
        "name": test_case["name"],
        "question": test_case["question"],
        "expected_parent": expected_parent,
        "actual_titles": actual_titles,
        "best_score": result["best_score"],
        "passed": passed,
    }


def main() -> None:
    index_data = load_parent_child_index()
    print("正在加载 BGE 向量模型...")
    embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
    print("BGE 模型来源：", model_source)
    print(f"相似度阈值：{MIN_RELEVANCE_SCORE}")

    passed_count = 0
    case_number = 0

    for test_case in TEST_CASES:
        # case_number += 1 表示在原数字基础上加一，用于给测试题编号。
        case_number += 1
        evaluation = evaluate_case(test_case, index_data, embedding_model)

        print(f"\n第 {case_number} 题：{evaluation['name']}")
        print("问题：", evaluation["question"])
        print(f"最高相似度：{evaluation['best_score']:.4f}")

        if evaluation["expected_parent"] is None:
            print("期待：不找回任何章节，直接拒答")
        else:
            print("期待章节：", evaluation["expected_parent"])

        if evaluation["actual_titles"]:
            # join() 用“、”把多个章节标题连成一行文字。
            print("实际找回：", "、".join(evaluation["actual_titles"]))
        else:
            print("实际找回：没有章节")

        if evaluation["passed"]:
            print("结果：通过")
            passed_count += 1
        else:
            print("结果：失败")

    print(f"\n测试总结：{passed_count} / {len(TEST_CASES)} 题通过")
    print("本课只检查检索和拒答，不检查 DeepSeek 的回答文字。")


if __name__ == "__main__":
    main()
