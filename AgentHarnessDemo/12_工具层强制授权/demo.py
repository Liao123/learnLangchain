"""Agent Harness 第 12 课：工具层自己检查授权，模型犯错也不能真的退款。"""

import copy
import json
from pathlib import Path

from langchain.tools import tool


LESSON_DIR = Path(__file__).resolve().parent
TASKS_PATH = LESSON_DIR / "数据" / "tool_authorization_tasks.json"
REPORT_PATH = LESSON_DIR / "输出" / "tool_authorization_report.json"

INITIAL_ORDERS = {
    "A1001": {
        "order_status": "paid",
        "refund_status": "not_requested",
    }
}

# 这两个变量模拟服务器数据。模型看不到也不能修改它们。
fake_orders: dict[str, dict[str, str]] = {}
server_confirmations: dict[str, bool] = {}


@tool
def submit_refund(order_id: str) -> dict:
    """提交退款。工具会自己从服务器确认状态检查订单是否已获批准。"""
    # 这一行才是实际授权判断，不是提示词。
    # 例如 server_confirmations["A1001"] = False 时，直接拒绝。
    if not server_confirmations.get(order_id, False):
        return {
            "ok": False,
            "reason": "服务器未确认退款，拒绝执行。",
            "order_id": order_id,
        }

    fake_orders[order_id]["refund_status"] = "submitted"
    return {
        "ok": True,
        "reason": "退款已提交。",
        "order_id": order_id,
        "refund_status": "submitted",
    }


def run_forced_tool_request(task_input: dict) -> dict:
    """模拟模型已经发出了工具请求，验证工具层最终会不会放行。"""
    global fake_orders, server_confirmations
    fake_orders = copy.deepcopy(INITIAL_ORDERS)

    order_id = task_input["order_id"]
    # 服务器保存的真实确认状态。例如第二题是：{"A1001": False}。
    server_confirmations = {order_id: task_input["server_confirmed"]}

    tool_calls = []
    if task_input["force_tool_call"]:
        # 这里故意无条件调用工具，模拟一个已经犯错的模型返回了 tool_calls。
        tool_result = submit_refund.invoke({"order_id": order_id})
        tool_calls.append(
            {
                "name": "submit_refund",
                "args": {"order_id": order_id},
                "result": tool_result,
            }
        )

    return {
        "tool_calls": tool_calls,
        "final_order": fake_orders[order_id],
    }


def evaluate_tool_authorization(task: dict, result: dict) -> dict:
    expected = task["expected"]
    actual_status = result["final_order"]["refund_status"]

    # 本课每题都 force_tool_call=True，所以第一条就是工具的实际返回值。
    tool_result = result["tool_calls"][0]["result"]
    tool_succeeded = tool_result["ok"]

    passed = (
        actual_status == expected["refund_status"]
        and tool_succeeded == expected["tool_succeeded"]
    )
    return {
        "expected_refund_status": expected["refund_status"],
        "actual_refund_status": actual_status,
        "expected_tool_succeeded": expected["tool_succeeded"],
        "actual_tool_succeeded": tool_succeeded,
        "tool_reason": tool_result["reason"],
        "passed": passed,
    }


with TASKS_PATH.open(encoding="utf-8") as tasks_file:
    dataset = json.load(tasks_file)

records = []
passed_count = 0
for index, task in enumerate(dataset["tasks"], start=1):
    result = run_forced_tool_request(task["input"])
    evaluation = evaluate_tool_authorization(task, result)
    records.append(
        {
            "task_id": task["task_id"],
            "server_confirmed": task["input"]["server_confirmed"],
            "result": result,
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
