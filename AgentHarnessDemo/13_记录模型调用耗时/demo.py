"""Agent Harness 第 13 课：记录一次模型调用耗时，并按时限评测。"""

import json
import os
from pathlib import Path
from time import perf_counter

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


LESSON_DIR = Path(__file__).resolve().parent
REPORT_PATH = LESSON_DIR / "输出" / "latency_report.json"

# 这是业务自己定的服务时限：一次路由判断最多允许 15 秒。
MAX_ALLOWED_LATENCY_MS = 15000

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)


def call_router(question: str) -> dict:
    """只测 model.invoke() 的网络请求和模型生成时间。"""
    # perf_counter() 是专门测耗时的高精度计时器。
    # 例如 start_time 的内部值可能是 12345.678，不需要直接关心它的数值。
    start_time = perf_counter()
    try:
        response = model.invoke(
            [
                SystemMessage(content="你是客服总调度，请简短回答用户问题。"),
                HumanMessage(content=question),
            ]
        )
        # 结束时间减开始时间，单位是秒；乘 1000 后变成毫秒。
        # 例如 0.82 秒 * 1000 = 820.0 ms。
        latency_ms = round((perf_counter() - start_time) * 1000)
        return {
            "answer": str(response.content),
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as error:
        # 请求失败也记录花了多久，之后可区分“慢”还是“直接报错”。
        latency_ms = round((perf_counter() - start_time) * 1000)
        return {
            "answer": "",
            "latency_ms": latency_ms,
            "error": f"{type(error).__name__}: {error}",
        }


question = "订单 A1001 到哪里了？"
call_result = call_router(question)

# 例如 call_result["latency_ms"] = 820 时：820 <= 15000，latency_passed=True。
latency_passed = call_result["latency_ms"] <= MAX_ALLOWED_LATENCY_MS
passed = call_result["error"] is None and latency_passed

report = {
    "question": question,
    "model_name": "deepseek-v4-pro",
    "max_allowed_latency_ms": MAX_ALLOWED_LATENCY_MS,
    "call_result": call_result,
    "evaluation": {
        "latency_passed": latency_passed,
        "passed": passed,
    },
}

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(report, report_file, ensure_ascii=False, indent=2)

result_text = "通过" if passed else "失败"
print(f"模型调用耗时：{call_result['latency_ms']} ms")
print(f"时限：{MAX_ALLOWED_LATENCY_MS} ms")
print(f"性能评测：{result_text}")
if call_result["error"]:
    print(f"请求错误：{call_result['error']}")
print(f"完整报告已写入：{REPORT_PATH}")
