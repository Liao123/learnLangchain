"""第 35 课：用固定测试题检查 RAG 检索。"""

import sys
from pathlib import Path


# 先定位 RAGDemo 根目录，才能导入公共检索函数。
RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

from rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 本课不调用 DeepSeek，只验证“资料有没有找对”。
MIN_RELEVANCE_SCORE = 0.50

# 每个字典是一道测试题。
# expected_parent 是期待找回的章节标题；None 表示期待程序拒答。
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
        "name": "故意失败：知识库外的问题",
        "question": "店里能维修电脑吗？",
        "expected_parent": None,
    },
]


# 这个函数只负责检查一道题，main() 会反复调用它检查全部题目。
def evaluate_case(test_case: dict, index_data: dict, embedding_model) -> dict:
    result = retrieve_parent_context(
        test_case["question"],
        index_data,
        embedding_model,
        min_relevance_score=MIN_RELEVANCE_SCORE,
    )

    # 先把实际找回的章节标题收集到列表里，后面方便和期待结果比较。
    actual_titles = []
    for parent in result["parents"]:
        actual_titles.append(parent["title"])

    expected_parent = test_case["expected_parent"]
    if expected_parent is None:
        # None 的意思是：这题本来就不该有答案，所以没有章节才算通过。
        passed = len(actual_titles) == 0
    else:
        # in 的意思是“有没有包含”。期待章节在实际列表里，就算通过。
        passed = expected_parent in actual_titles

    return {
        "name": test_case["name"],
        "question": test_case["question"],
        "expected_parent": expected_parent,
        "actual_titles": actual_titles,
        "best_score": result["best_score"],
        "passed": passed,
    }


index_data = load_parent_child_index()
print("正在加载 BGE 向量模型...")
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])
print("BGE 模型来源：", model_source)
print(f"相似度阈值：{MIN_RELEVANCE_SCORE}")

passed_count = 0
case_number = 0

for test_case in TEST_CASES:
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