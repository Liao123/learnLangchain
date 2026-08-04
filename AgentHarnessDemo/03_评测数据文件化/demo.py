"""Agent Harness 第 3 课：从 JSON 文件读取评测题目。"""

import json
import os
from pathlib import Path
from typing import Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class RouteOutput(BaseModel):
    route: Literal["order", "refund", "human"]


LESSON_DIR = Path(__file__).resolve().parent
# DATASET_PATH 的值类似：...\03_评测数据文件化\数据\routing_tasks.json
DATASET_PATH = LESSON_DIR / "数据" / "routing_tasks.json"
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

    return {"route": route}


def evaluate_task(task: dict, agent_output: dict) -> dict:
    expected_route = task["expected"]["route"]
    actual_route = agent_output["route"]
    return {
        "expected_route": expected_route,
        "actual_route": actual_route,
        "passed": actual_route == expected_route,
    }


# json.load 会直接把 JSON 文件内容变成 Python 字典。
# dataset 的值大致是：
# {"dataset_name": "客服路由基础题集", "version": "v1", "tasks": [{...}, {...}]}
with DATASET_PATH.open(encoding="utf-8") as dataset_file:
    dataset = json.load(dataset_file)

# tasks 是 JSON 里的 tasks 列表。
# tasks[0] 的值是：
# {"task_id": "route-order-001", "case_type": "订单查询",
#  "input": {"question": "订单 A1001 到哪里了？"}, "expected": {"route": "order"}}
tasks = dataset["tasks"]
case_records = []
passed_count = 0

for index, task in enumerate(tasks, start=1):
    agent_output = run_agent(task["input"])
    evaluation = evaluate_task(task, agent_output)

    case_records.append(
        {
            "task_id": task["task_id"],
            "case_type": task["case_type"],
            "input": task["input"],
            "agent_output": agent_output,
            "evaluation": evaluation,
        }
    )

    if evaluation["passed"]:
        passed_count += 1

    result_text = "通过" if evaluation["passed"] else "失败"
    print(f"第 {index} 题：{task['case_type']} -> {result_text}")

success_rate = passed_count / len(tasks)
batch_report = {
    # 报告带上题集名称和版本，之后看到报告才知道它是用哪套题跑出来的。
    "dataset_name": dataset["dataset_name"],
    "dataset_version": dataset["version"],
    "summary": {
        "total_count": len(tasks),
        "passed_count": passed_count,
        "success_rate": success_rate,
    },
    "cases": case_records,
}

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(batch_report, report_file, ensure_ascii=False, indent=2)

print(f"\n题集：{dataset['dataset_name']} {dataset['version']}")
print(f"总结果：{passed_count}/{len(tasks)}，成功率 {success_rate:.0%}")
print(f"完整报告已写入：{REPORT_PATH}")
