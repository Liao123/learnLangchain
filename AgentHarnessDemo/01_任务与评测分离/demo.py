"""Agent Harness 第 1 课：把任务、Agent 运行和评测分开记录。"""

import json
import os
from pathlib import Path
from typing import Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class RouteOutput(BaseModel):
    # Agent 正常输出示例：{"route": "refund"}
    route: Literal["order", "refund", "human"]


# 输出文件的最终位置类似：...\01_任务与评测分离\输出\run_record.json
LESSON_DIR = Path(__file__).resolve().parent
RECORD_PATH = LESSON_DIR / "输出" / "run_record.json"

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
    """这是被测的 Agent。本课中它是一个“选择客服路线”的小 Agent。"""
    # task_input 的值示例：{"question": "我想退钱"}
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
        # 这里故意记为 invalid，交给评测发现错误；不把错误伪装成正常 human 路线。
        route = "invalid"

    # Agent 的实际产物。值示例：
    # {"route": "refund", "trace": [{"step": "总调度", "output": "refund"}]}
    return {
        "route": route,
        "trace": [
            {
                "step": "总调度",
                "input": question,
                "output": route,
            }
        ],
    }


def evaluate_task(task: dict, agent_output: dict) -> dict:
    """这是独立的评测器：它不调用 Agent，只比较期望值和实际值。"""
    expected_route = task["expected"]["route"]
    actual_route = agent_output["route"]
    passed = actual_route == expected_route

    # 返回值示例：
    # {"expected_route": "refund", "actual_route": "refund", "passed": True}
    return {
        "expected_route": expected_route,
        "actual_route": actual_route,
        "passed": passed,
    }


# 任务数据由人先写好，不是模型临时猜出来的。
# 它包含：这题叫什么、给 Agent 的输入、人工认定的正确结果。
task = {
    "task_id": "route-refund-001",
    "input": {"question": "我想退钱"},
    "expected": {"route": "refund"},
}

# 1. Agent 只负责完成任务，得到实际结果。
agent_output = run_agent(task["input"])

# 2. 评测器只负责判分，不参与 Agent 的决策。
evaluation = evaluate_task(task, agent_output)

# 3. Harness 把任务、过程、结果、判分放在同一份运行记录中。
#    文件中的完整值大致是：
#    {"task": {...}, "agent_output": {...}, "evaluation": {"passed": True}}
run_record = {
    "task": task,
    "agent_output": agent_output,
    "evaluation": evaluation,
}

with RECORD_PATH.open("w", encoding="utf-8") as record_file:
    json.dump(run_record, record_file, ensure_ascii=False, indent=2)

result_text = "通过" if evaluation["passed"] else "失败"
print(f"任务：{task['task_id']}")
print(f"Agent 实际选择：{agent_output['route']}")
print(f"评测结果：{result_text}")
print(f"完整运行记录已写入：{RECORD_PATH}")
