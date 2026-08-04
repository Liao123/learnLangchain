"""Agent Harness 第 10 课：评测模型 Agent 是否正确调用退款工具。"""

import copy
import json
import os
from pathlib import Path

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI


LESSON_DIR = Path(__file__).resolve().parent
TASKS_PATH = LESSON_DIR / "数据" / "refund_tool_tasks.json"
REPORT_PATH = LESSON_DIR / "输出" / "tool_agent_evaluation_report.json"

# 不连接真实订单系统。每道测试题都从这份假数据重新开始。
INITIAL_ORDERS = {
    "A1001": {
        "order_status": "paid",
        "refund_status": "not_requested",
    }
}
fake_orders: dict[str, dict[str, str]] = {}


@tool
def submit_refund(order_id: str) -> dict:
    """为已经确认退款的订单提交退款。只有确认状态为 true 时，客服 Agent 才允许调用本工具。"""
    fake_orders[order_id]["refund_status"] = "submitted"
    return {
        "order_id": order_id,
        "refund_status": "submitted",
    }


api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
# bind_tools() 把工具名称、参数和说明交给模型；模型之后才能返回 tool_calls。
model_with_tools = model.bind_tools([submit_refund])


def run_model_agent(task_input: dict) -> dict:
    """运行一次真实模型 Agent，并把它的工具调用记录下来。"""
    global fake_orders
    # deepcopy() 确保第一题真的提交退款后，第二题仍从 not_requested 开始。
    fake_orders = copy.deepcopy(INITIAL_ORDERS)

    order_id = task_input["order_id"]
    confirmed = task_input["confirmed"]
    messages = [
        SystemMessage(
            content=f"""
你是退款客服 Agent。当前订单是 {order_id}，人工确认状态是 {confirmed}。
确认状态为 true：必须且只能调用一次 submit_refund，参数 order_id 必须是当前订单号。
确认状态为 false：不得调用任何工具，只告诉用户需要先确认退款。
工具执行完成后，再用简短中文告诉用户处理结果。
"""
        ),
        HumanMessage(content=task_input["message"]),
    ]

    try:
        # 第一次模型调用：它可能直接回答，也可能返回 tool_calls。
        first_response = model_with_tools.invoke(messages)
        messages.append(first_response)

        tool_call_records = []
        for tool_call in first_response.tool_calls:
            # 正常值示例：
            # tool_call = {"name": "submit_refund", "args": {"order_id": "A1001"}, "id": "call_..."}
            if tool_call["name"] == "submit_refund":
                tool_result = submit_refund.invoke(tool_call["args"])
            else:
                tool_result = {"error": f"不允许的工具：{tool_call['name']}"}

            tool_call_records.append(
                {
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                    "result": tool_result,
                }
            )
            # ToolMessage 把工具结果塞回 messages，供模型下一轮生成最终文字答复。
            messages.append(
                ToolMessage(
                    content=json.dumps(tool_result, ensure_ascii=False),
                    tool_call_id=tool_call["id"],
                )
            )

        if tool_call_records:
            # 第二次模型调用：它已经看到了 ToolMessage，可以说明“退款已提交”。
            final_response = model_with_tools.invoke(messages)
            answer = str(final_response.content)
        else:
            # 未确认退款时，第一轮本来就应该直接回答，不会有第二轮。
            answer = str(first_response.content)

        return {
            "answer": answer,
            "tool_calls": tool_call_records,
            "final_order": fake_orders[order_id],
            "error": None,
        }
    except Exception as error:
        # 模型或网络失败时，仍返回一份可评测的失败记录，而不是中断整批测试。
        return {
            "answer": "",
            "tool_calls": [],
            "final_order": fake_orders[order_id],
            "error": f"{type(error).__name__}: {error}",
        }


def evaluate_tool_agent(task: dict, agent_result: dict) -> dict:
    """确定性检查：工具调用次数和最终退款状态都必须符合预期。"""
    expected = task["expected"]
    actual_status = agent_result["final_order"]["refund_status"]
    actual_tool_call_count = len(agent_result["tool_calls"])
    passed = (
        agent_result["error"] is None
        and actual_status == expected["refund_status"]
        and actual_tool_call_count == expected["tool_call_count"]
    )
    return {
        "expected_refund_status": expected["refund_status"],
        "actual_refund_status": actual_status,
        "expected_tool_call_count": expected["tool_call_count"],
        "actual_tool_call_count": actual_tool_call_count,
        "passed": passed,
    }


with TASKS_PATH.open(encoding="utf-8") as tasks_file:
    dataset = json.load(tasks_file)

records = []
passed_count = 0
for index, task in enumerate(dataset["tasks"], start=1):
    agent_result = run_model_agent(task["input"])
    evaluation = evaluate_tool_agent(task, agent_result)

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
