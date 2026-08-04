"""Agent Harness 第 9 课：检查 Agent 的工具调用和最终业务状态。"""

import copy
import json
from pathlib import Path


LESSON_DIR = Path(__file__).resolve().parent
TASKS_PATH = LESSON_DIR / "数据" / "refund_tool_tasks.json"
REPORT_PATH = LESSON_DIR / "输出" / "tool_evaluation_report.json"

# 这是假的订单系统初始数据，不会连接真实数据库。
# 每次测试开始时，A1001 的值都是：
# {"order_status": "paid", "refund_status": "not_requested"}
INITIAL_ORDERS = {
    "A1001": {
        "order_status": "paid",
        "refund_status": "not_requested",
    }
}


def submit_refund(orders: dict, order_id: str) -> dict:
    """模拟退款工具：把指定订单的退款状态改为 submitted。"""
    orders[order_id]["refund_status"] = "submitted"
    return {"order_id": order_id, "refund_status": "submitted"}


def run_refund_agent(task_input: dict) -> dict:
    """被测的退款处理流程。本课用固定规则代替模型，专注测试工具副作用。"""
    # deepcopy() 会创建一份全新的假订单数据。
    # 第一题改成 submitted 后，不会污染第二题；第二题仍从 not_requested 开始。
    orders = copy.deepcopy(INITIAL_ORDERS)
    order_id = task_input["order_id"]
    confirmed = task_input["confirmed"]
    tool_calls = []

    if confirmed:
        # confirmed=True 时，流程调用工具。tool_result 的值是：
        # {"order_id": "A1001", "refund_status": "submitted"}
        tool_result = submit_refund(orders, order_id)
        tool_calls.append(
            {
                "name": "submit_refund",
                "args": {"order_id": order_id},
                "result": tool_result,
            }
        )
        answer = "退款已提交。"
    else:
        # confirmed=False 时，流程不能调用退款工具，订单状态必须保持原样。
        answer = "尚未确认，未提交退款。"

    # 返回值示例：
    # {"answer": "退款已提交。", "tool_calls": [{...}],
    #  "final_order": {"order_status": "paid", "refund_status": "submitted"}}
    return {
        "answer": answer,
        "tool_calls": tool_calls,
        "final_order": orders[order_id],
    }


def evaluate_tool_result(task: dict, agent_result: dict) -> dict:
    """确定性评测：直接比较工具名和最终订单状态。"""
    expected = task["expected"]
    actual_status = agent_result["final_order"]["refund_status"]

    # 有工具调用时取第一条工具名；没有调用时，actual_tool_name=None。
    if agent_result["tool_calls"]:
        actual_tool_name = agent_result["tool_calls"][0]["name"]
    else:
        actual_tool_name = None

    passed = (
        actual_status == expected["refund_status"]
        and actual_tool_name == expected["tool_name"]
    )
    return {
        "expected_refund_status": expected["refund_status"],
        "actual_refund_status": actual_status,
        "expected_tool_name": expected["tool_name"],
        "actual_tool_name": actual_tool_name,
        "passed": passed,
    }


with TASKS_PATH.open(encoding="utf-8") as tasks_file:
    dataset = json.load(tasks_file)

records = []
passed_count = 0
for index, task in enumerate(dataset["tasks"], start=1):
    agent_result = run_refund_agent(task["input"])
    evaluation = evaluate_tool_result(task, agent_result)

    records.append(
        {
            "task_id": task["task_id"],
            "agent_result": agent_result,
            "evaluation": evaluation,
        }
    )
    if evaluation["passed"]:
        passed_count += 1

    result_text = "通过" if evaluation["passed"] else "失败"
    print(f"第 {index} 题：{task['task_id']} -> {result_text}")

report = {
    "dataset_name": dataset["dataset_name"],
    "dataset_version": dataset["version"],
    "summary": {
        "total_count": len(dataset["tasks"]),
        "passed_count": passed_count,
    },
    "cases": records,
}

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(report, report_file, ensure_ascii=False, indent=2)

print(f"\n总结果：{passed_count}/{len(dataset['tasks'])}")
print(f"完整报告已写入：{REPORT_PATH}")
