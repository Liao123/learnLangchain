"""多 Agent 第 15 课：用一组真实问题评测模型总调度的路由准确率。"""

import json
import os
from typing import Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class RouteResult(BaseModel):
    route: Literal["order", "refund", "human"]


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
        result = RouteResult.model_validate(json.loads(response.content))
        return result.route
    except (json.JSONDecodeError, ValidationError):
        return "invalid"


# 这就是最小评测集：每条都有用户问题和人工预期 route。
test_cases = [
    {"question": "订单 A1001 到哪里了？", "expected_route": "order"},
    {"question": "我不想要了，钱什么时候退回来？", "expected_route": "refund"},
    {"question": "退款单 R2001 还要多久到账？", "expected_route": "refund"},
    {"question": "明天上海会下雨吗？", "expected_route": "human"},
]

passed_count = 0

for index, test_case in enumerate(test_cases, start=1):
    actual_route = classify_route(test_case["question"])
    passed = actual_route == test_case["expected_route"]
    if passed:
        passed_count += 1

    result_text = "通过" if passed else "失败"
    print(f"第 {index} 条：{result_text}")
    print("  问题：", test_case["question"])
    print("  期望 route：", test_case["expected_route"])
    print("  实际 route：", actual_route)

success_rate = passed_count / len(test_cases)
print(f"\n总结果：{passed_count}/{len(test_cases)}，成功率 {success_rate:.0%}")
