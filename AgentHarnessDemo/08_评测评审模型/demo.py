"""Agent Harness 第 8 课：用人工标签测试评审模型是否会正确判分。"""

import json
import os
from pathlib import Path

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class JudgeResult(BaseModel):
    # 评审模型单次输出的格式，例如：
    # {"passed": false, "reason": "缺少原路退回", "missing_points": ["原路退回"]}
    passed: bool
    reason: str
    missing_points: list[str]


LESSON_DIR = Path(__file__).resolve().parent
CASES_PATH = LESSON_DIR / "数据" / "judge_cases.json"
REPORT_PATH = LESSON_DIR / "输出" / "judge_evaluation_report.json"

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
judge_model = model.bind(response_format={"type": "json_object"})


def judge_answer(question: str, rubric: list[str], agent_answer: str) -> JudgeResult:
    """评审模型按评分标准判断一段已给出的回答。"""
    evaluation_input = {
        "question": question,
        "rubric": rubric,
        "agent_answer": agent_answer,
    }
    response = judge_model.invoke(
        [
            SystemMessage(
                content="""
你是严格的客服回答评审员。
根据输入中的 rubric 检查 agent_answer。
所有评分点都满足，且没有编造信息，passed 才是 true。
只能返回 JSON，格式如下：
{"passed": true, "reason": "简短原因", "missing_points": []}
"""
            ),
            HumanMessage(content=json.dumps(evaluation_input, ensure_ascii=False)),
        ]
    )
    return JudgeResult.model_validate(json.loads(response.content))


# dataset 的值来自 JSON 文件，包含题目、rubric 和人工已标注的四个案例。
with CASES_PATH.open(encoding="utf-8") as cases_file:
    dataset = json.load(cases_file)

records = []
matched_count = 0

for index, case in enumerate(dataset["cases"], start=1):
    judge_format_valid = True
    try:
        judge_result = judge_answer(
            dataset["question"],
            dataset["rubric"],
            case["agent_answer"],
        )
    except (json.JSONDecodeError, ValidationError, TypeError) as error:
        # 格式错误不能因为碰巧 expected_passed=false 就被算作“判断正确”。
        judge_format_valid = False
        judge_result = JudgeResult(
            passed=False,
            reason=f"评审格式异常：{type(error).__name__}",
            missing_points=["无法获得有效评审结果"],
        )

    # 这是本课真正的判分：评审模型的 passed 要和人工标签 expected_passed 一样。
    # 例如第一题：judge_result.passed=True，case["expected_passed"]=True，结果为 True。
    judge_matches_human = (
        judge_format_valid and judge_result.passed == case["expected_passed"]
    )
    if judge_matches_human:
        matched_count += 1

    record = {
        "case_id": case["case_id"],
        "agent_answer": case["agent_answer"],
        "human_expected_passed": case["expected_passed"],
        "human_reason": case["human_reason"],
        "judge_output": judge_result.model_dump(),
        "judge_matches_human": judge_matches_human,
    }
    records.append(record)

    result_text = "一致" if judge_matches_human else "不一致"
    print(f"第 {index} 题：人工和评审模型 {result_text}")

accuracy = matched_count / len(dataset["cases"])
report = {
    "summary": {
        "total_count": len(dataset["cases"]),
        "matched_count": matched_count,
        "accuracy": accuracy,
    },
    "cases": records,
}

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(report, report_file, ensure_ascii=False, indent=2)

print(f"\n评审模型与人工标签一致：{matched_count}/{len(dataset['cases'])}，准确率 {accuracy:.0%}")
print(f"完整报告已写入：{REPORT_PATH}")
