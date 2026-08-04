"""Agent Harness 第 7 课：用模型按评分标准评审开放式回答。"""

import json
import os
from pathlib import Path

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class JudgeResult(BaseModel):
    # 评审模型必须给出这三项。
    # 正常值示例：{"passed": true, "reason": "包含时效和退款方式", "missing_points": []}
    passed: bool
    reason: str
    missing_points: list[str]


LESSON_DIR = Path(__file__).resolve().parent
RECORD_PATH = LESSON_DIR / "输出" / "judge_record.json"

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
# judge_model 只是在同一个模型上附加“必须返回 JSON”的要求。
judge_model = model.bind(response_format={"type": "json_object"})


# 这是人提前写好的测试任务和评分标准。
task = {
    "task_id": "refund-answer-001",
    "question": "退款申请提交后，钱什么时候退回来？",
    "knowledge": "退款申请提交后，通常会在 1 到 3 个工作日原路退回。",
    "rubric": [
        "回答明确说明 1 到 3 个工作日。",
        "回答明确说明原路退回。",
        "不能编造其他退款时间或退款方式。",
    ],
}


def run_agent(current_task: dict) -> str:
    """被测的退款 Agent：根据给定资料回答用户。"""
    response = model.invoke(
        [
            SystemMessage(
                content=f"""
你是退款客服。
只能根据下面资料回答，不能补充资料没有的内容。

资料：{current_task['knowledge']}
"""
            ),
            HumanMessage(content=current_task["question"]),
        ]
    )

    # answer 的值示例："退款申请提交后，通常会在 1 到 3 个工作日原路退回。"
    return str(response.content)


def judge_answer(current_task: dict, answer: str) -> JudgeResult:
    """评审模型：只负责按 rubric 判分，不负责回答用户。"""
    # evaluation_input 的值包含题目、评分标准和 Agent 实际回答。
    # 评审模型看不到 Agent 内部思考，只能依据这些可记录的数据判定。
    evaluation_input = {
        "question": current_task["question"],
        "rubric": current_task["rubric"],
        "agent_answer": answer,
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
            HumanMessage(
                # ensure_ascii=False 保留中文，给评审模型看的是正常中文而不是转义字符。
                content=json.dumps(evaluation_input, ensure_ascii=False)
            ),
        ]
    )

    # 将模型文字，例如 '{"passed": true, ...}'，变成经过字段检查的 JudgeResult 对象。
    return JudgeResult.model_validate(json.loads(response.content))


answer = run_agent(task)

try:
    evaluation = judge_answer(task, answer)
except (json.JSONDecodeError, ValidationError, TypeError) as error:
    # 评审模型格式异常也必须留下记录，不能装作评测通过。
    evaluation = JudgeResult(
        passed=False,
        reason=f"评审结果格式异常：{type(error).__name__}",
        missing_points=["无法获得有效评审结果"],
    )

# 运行记录的值大致如下：
# {"task": {...}, "agent_answer": "...", "evaluation": {"passed": true, ...}}
record = {
    "task": task,
    "agent_answer": answer,
    # model_dump() 把 Pydantic 对象变回普通字典，才能写入 JSON。
    "evaluation": evaluation.model_dump(),
}

with RECORD_PATH.open("w", encoding="utf-8") as record_file:
    json.dump(record, record_file, ensure_ascii=False, indent=2)

result_text = "通过" if evaluation.passed else "失败"
print(f"Agent 回答：{answer}")
print(f"模型评审：{result_text}")
print(f"评审原因：{evaluation.reason}")
if evaluation.missing_points:
    print(f"缺失点：{'；'.join(evaluation.missing_points)}")
print(f"完整记录已写入：{RECORD_PATH}")
