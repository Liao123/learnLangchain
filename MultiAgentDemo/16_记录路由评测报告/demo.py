"""多 Agent 第 16 课：把总调度路由评测保存成可查看的报告。"""

import json
import os
from pathlib import Path
from typing import Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class RouteResult(BaseModel):
    # 模型只能选这三个 route；例如：{"route": "refund"}。
    route: Literal["order", "refund", "human"]


# __file__ 是本 demo.py；parent 是本课文件夹。
# REPORT_PATH 最终值类似：...\16_记录路由评测报告\输出\route_evaluation_report.json
LESSON_DIR = Path(__file__).resolve().parent
REPORT_PATH = LESSON_DIR / "输出" / "route_evaluation_report.json"

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
router_model = model.bind(response_format={"type": "json_object"})


def classify_route(question: str) -> str:
    # 传入值示例：question = "我不想要了，钱什么时候退回来？"
    # 返回值示例："refund"。
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
        # 先把模型文字 '{"route": "refund"}' 变成字典，
        # 再用 RouteResult 检查 route 是不是三个允许值之一。
        result = RouteResult.model_validate(json.loads(response.content))
        return result.route
    except (json.JSONDecodeError, ValidationError):
        # 模型没有按约定返回时，也留下一个明确的实际结果给报告。
        return "invalid"


# 每题多放一个 case_type，之后看到失败题时，知道它属于哪一类。
# 第一题的完整值示例：
# {"question": "订单 A1001 到哪里了？", "expected_route": "order", "case_type": "订单查询"}
test_cases = [
    {"question": "订单 A1001 到哪里了？", "expected_route": "order", "case_type": "订单查询"},
    {"question": "我不想要了，钱什么时候退回来？", "expected_route": "refund", "case_type": "退款意图"},
    {"question": "退款单 R2001 还要多久到账？", "expected_route": "refund", "case_type": "退款进度"},
    {"question": "明天上海会下雨吗？", "expected_route": "human", "case_type": "范围外问题"},
]

evaluation_results = []

for index, test_case in enumerate(test_cases, start=1):
    # test_case 是一题，例如第一轮：
    # {"question": "订单 A1001 到哪里了？", "expected_route": "order", "case_type": "订单查询"}
    actual_route = classify_route(test_case["question"])
    passed = actual_route == test_case["expected_route"]

    # 这一题跑完后，evaluation 的值示例：
    # {"index": 1, "question": "订单 A1001 到哪里了？", "expected_route": "order",
    #  "actual_route": "order", "passed": True, "case_type": "订单查询"}
    evaluation = {
        "index": index,
        "question": test_case["question"],
        "expected_route": test_case["expected_route"],
        "actual_route": actual_route,
        "passed": passed,
        "case_type": test_case["case_type"],
    }
    evaluation_results.append(evaluation)

    result_text = "通过" if passed else "失败"
    print(f"第 {index} 题：{result_text}，实际选择 {actual_route}")

# 先把整次评测的所有题写进文件。之后即使关了终端，结果也还在。
# JSON 文件中会是一组 evaluation，例如：[{"index": 1, ...}, {"index": 2, ...}]。
with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(evaluation_results, report_file, ensure_ascii=False, indent=2)

# 再把失败题单独挑出来。成功题不需要优先花时间分析。
failed_results = []
for evaluation in evaluation_results:
    if not evaluation["passed"]:
        failed_results.append(evaluation)

print(f"\n完整报告已写入：{REPORT_PATH}")
if not failed_results:
    print("本次没有失败题。")
else:
    print("本次需要分析的失败题：")
    for failure in failed_results:
        print(f"- 第 {failure['index']} 题（{failure['case_type']}）")
        print(f"  问题：{failure['question']}")
        print(f"  预期：{failure['expected_route']}；实际：{failure['actual_route']}")
