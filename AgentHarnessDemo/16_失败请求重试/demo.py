"""Agent Harness 第 16 课：对临时连接错误有限次数重试，并留下尝试记录。"""

import json
from pathlib import Path


LESSON_DIR = Path(__file__).resolve().parent
REPORT_PATH = LESSON_DIR / "输出" / "retry_report.json"

# 最多尝试 3 次：第一次调用 + 最多 2 次重试。
MAX_ATTEMPTS = 3

# 这个变量只用于模拟。第 1、2 次失败，第 3 次成功。
simulated_call_count = 0


def simulate_model_call(question: str) -> str:
    """模拟不稳定的模型服务。生产中可替换为 model.invoke(...)。"""
    global simulated_call_count
    simulated_call_count += 1

    # 第一次的值是 1，第二次是 2，都抛出临时连接错误。
    if simulated_call_count < 3:
        raise ConnectionError("模拟网络暂时中断")

    # 第三次的值是 3，正常返回结果。
    return f"已成功处理问题：{question}"


def call_with_retry(question: str) -> dict:
    """只对 ConnectionError 重试；其他错误应直接暴露，不应盲目重复请求。"""
    attempts = []

    # range(1, MAX_ATTEMPTS + 1) 的值依次是 1、2、3。
    for attempt_number in range(1, MAX_ATTEMPTS + 1):
        try:
            answer = simulate_model_call(question)
            attempts.append(
                {
                    "attempt_number": attempt_number,
                    "status": "success",
                    "error": None,
                }
            )
            return {
                "answer": answer,
                "attempts": attempts,
                "error": None,
            }
        except ConnectionError as error:
            # 只有连接错误进入这里。第一次追加失败记录后，for 自动进入第二次。
            attempts.append(
                {
                    "attempt_number": attempt_number,
                    "status": "connection_error",
                    "error": str(error),
                }
            )

    # 三次全是连接错误时，for 执行完才会走到这里。
    return {
        "answer": "",
        "attempts": attempts,
        "error": f"重试 {MAX_ATTEMPTS} 次后仍无法连接模型服务。",
    }


question = "订单 A1001 到哪里了？"
result = call_with_retry(question)

# result["attempts"] 的值会是：
# [
#   {"attempt_number": 1, "status": "connection_error", ...},
#   {"attempt_number": 2, "status": "connection_error", ...},
#   {"attempt_number": 3, "status": "success", "error": None}
# ]
report = {
    "question": question,
    "max_attempts": MAX_ATTEMPTS,
    "result": result,
    "passed": result["error"] is None,
}

with REPORT_PATH.open("w", encoding="utf-8") as report_file:
    json.dump(report, report_file, ensure_ascii=False, indent=2)

print(f"最终结果：{'通过' if report['passed'] else '失败'}")
for item in result["attempts"]:
    print(f"第 {item['attempt_number']} 次：{item['status']}")
print(f"完整报告已写入：{REPORT_PATH}")
