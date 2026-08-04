"""Agent Harness 第 14 课：读取模型 Token 用量，并按预算判定。"""

import json
import os
from pathlib import Path

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


LESSON_DIR = Path(__file__).resolve().parent
REPORT_PATH = LESSON_DIR / "输出" / "token_usage_report.json"

# 业务自己设定：一次简单路由请求最多允许使用 500 个 Token。
MAX_TOTAL_TOKENS = 500

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)


def read_token_usage(response) -> dict:
    """从 AIMessage 读取 LangChain 统一整理后的 Token 用量。"""
    # 正常时 raw_usage 的值类似：
    # {"input_tokens": 30, "output_tokens": 20, "total_tokens": 50}
    # 某些模型服务不返回用量时，它的值可能是 None，所以用 {} 代替。
    raw_usage = response.usage_metadata or {}

    # dict.get("input_tokens") 的意思：有这个键就取值，没有就返回 None。
    return {
        "input_tokens": raw_usage.get("input_tokens"),
        "output_tokens": raw_usage.get("output_tokens"),
        "total_tokens": raw_usage.get("total_tokens"),
    }


question = "订单 A1001 到哪里了？"
try:
    response = model.invoke(
        [
            SystemMessage(content="你是客服总调度，请用一句中文回答用户。"),
            HumanMessage(content=question),
        ]
    )
    token_usage = read_token_usage(response)
    error = None
    answer = str(response.content)
except Exception as caught_error:
    # 网络或服务失败时，没有有效 Token 用量，不能当成 0 Token。
    token_usage = {
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
    }
    error = f"{type(caught_error).__name__}: {caught_error}"
    answer = ""

total_tokens = token_usage["total_tokens"]
if error is not None:
    budget_status = "request_failed"
    passed = False
elif total_tokens is None:
    # 这表示服务商没有返回 Token 数据，不能判断是否超预算。
    budget_status = "usage_unavailable"
    passed = False
elif total_tokens <= MAX_TOTAL_TOKENS:
    budget_status = "within_budget"
    passed = True
else:
    budget_status = "over_budget"
    passed = False

report = {
    "question": question,
    "model_name": "deepseek-v4-pro",
    "max_total_tokens": MAX_TOTAL_TOKENS,
    "answer": answer,
    "token_usage": token_usage,
    "evaluation": {
        "budget_status": budget_status,
        "passed": passed,
    },
    "error": error,
}

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(report, report_file, ensure_ascii=False, indent=2)

print(f"输入 Token：{token_usage['input_tokens']}")
print(f"输出 Token：{token_usage['output_tokens']}")
print(f"总 Token：{token_usage['total_tokens']}")
print(f"Token 预算状态：{budget_status}")
print(f"完整报告已写入：{REPORT_PATH}")
