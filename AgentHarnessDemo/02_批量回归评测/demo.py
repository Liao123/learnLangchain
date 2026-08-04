"""Agent Harness 第 2 课：一次运行一组固定任务，得到回归评测报告。"""

import json
import os
from pathlib import Path
from typing import Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class RouteOutput(BaseModel):
    # Agent 输出例如：{"route": "order"}
    route: Literal["order", "refund", "human"]


LESSON_DIR = Path(__file__).resolve().parent
# 最终文件类似：...\02_批量回归评测\输出\batch_report.json
REPORT_PATH = LESSON_DIR / "输出" / "batch_report.json"

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
router_model = model.bind(response_format={"type": "json_object"})


def run_agent(task_input: dict[str, str]) -> dict:
    """被测 Agent：根据问题选择客服路线。"""
    question = task_input["question"]
    response = router_model.invoke(
        [
            SystemMessage(
                content="""
你是客服总调度。
订单进度、配送、修改订单 -> order
退款、退货、退款到账 -> refund
无法判断或不属于客服范围 -> human
只能返回 JSON，例如：{"route": "order"}
"""
            ),
            HumanMessage(content=question),
        ]
    )

    try:
        route = RouteOutput.model_validate(json.loads(response.content)).route
    except (json.JSONDecodeError, ValidationError, TypeError):
        route = "invalid"

    # 返回值示例：{"route": "refund"}
    return {"route": route}


def evaluate_task(task: dict, agent_output: dict) -> dict:
    """独立判分：只比较人工标准和 Agent 实际输出。"""
    expected_route = task["expected"]["route"]
    actual_route = agent_output["route"]
    return {
        "expected_route": expected_route,
        "actual_route": actual_route,
        "passed": actual_route == expected_route,
    }


# 这就是固定任务集。之后改提示词或模型时，仍然用这组题来跑。
# 第一题的值是：
# {"task_id": "route-order-001", "input": {"question": "订单 A1001 到哪里了？"},
#  "expected": {"route": "order"}}
tasks = [
    {
        "task_id": "route-order-001",
        "input": {"question": "订单 A1001 到哪里了？"},
        "expected": {"route": "order"},
    },
    {
        "task_id": "route-refund-001",
        "input": {"question": "我想退钱"},
        "expected": {"route": "refund"},
    },
    {
        "task_id": "route-refund-002",
        "input": {"question": "退款单 R2001 什么时候到账？"},
        "expected": {"route": "refund"},
    },
    {
        "task_id": "route-human-001",
        "input": {"question": "明天上海会下雨吗？"},
        "expected": {"route": "human"},
    },
]

case_records = []
passed_count = 0

# enumerate 给每道题一个显示用的序号：第一轮 index=1，task=tasks[0]。
for index, task in enumerate(tasks, start=1):
    # 1. 给当前任务运行 Agent。
    agent_output = run_agent(task["input"])

    # 2. 用独立评测器判分。
    evaluation = evaluate_task(task, agent_output)

    # 3. 这道题的完整记录。值示例：
    # {"task_id": "route-refund-001", "agent_output": {"route": "refund"},
    #  "evaluation": {"expected_route": "refund", "actual_route": "refund", "passed": True}}
    case_record = {
        "task_id": task["task_id"],
        "input": task["input"],
        "agent_output": agent_output,
        "evaluation": evaluation,
    }
    case_records.append(case_record)

    if evaluation["passed"]:
        passed_count += 1

    result_text = "通过" if evaluation["passed"] else "失败"
    print(f"第 {index} 题：{task['task_id']} -> {result_text}")

success_rate = passed_count / len(tasks)

# 一次批量运行的总报告：既有总分，也保留了每道题的过程和判分。
batch_report = {
    "summary": {
        "total_count": len(tasks),
        "passed_count": passed_count,
        "success_rate": success_rate,
    },
    "cases": case_records,
}

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(batch_report, report_file, ensure_ascii=False, indent=2)

print(f"\n总结果：{passed_count}/{len(tasks)}，成功率 {success_rate:.0%}")
print(f"完整报告已写入：{REPORT_PATH}")
