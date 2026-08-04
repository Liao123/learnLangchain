"""Agent Harness 第 15 课：限制并发数后，并行运行一批模型评测任务。"""

import asyncio
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError


class RouteOutput(BaseModel):
    route: Literal["order", "refund", "human"]


LESSON_DIR = Path(__file__).resolve().parent
TASKS_PATH = LESSON_DIR / "数据" / "routing_tasks.json"
REPORT_PATH = LESSON_DIR / "输出" / "parallel_evaluation_report.json"

# 最多同时发出两次模型请求。四道题会大致分两批完成，而不是四题同时冲向接口。
MAX_CONCURRENT_REQUESTS = 2

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
router_model = model.bind(response_format={"type": "json_object"})


async def evaluate_one_task(task: dict, semaphore: asyncio.Semaphore) -> dict:
    """异步评测一题。遇到 await 时，Python 可以先去执行另一题。"""
    # async with semaphore 表示：先拿到一个并发名额，才能调用模型。
    # 当前有两个名额；第三题会在这里等到前面某题完成后才进入。
    async with semaphore:
        start_time = perf_counter()
        try:
            response = await router_model.ainvoke(
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
                    HumanMessage(content=task["input"]["question"]),
                ]
            )
            actual_route = RouteOutput.model_validate(json.loads(response.content)).route
            error = None
        except (json.JSONDecodeError, ValidationError, TypeError) as caught_error:
            actual_route = "invalid"
            error = f"输出格式异常：{type(caught_error).__name__}"
        except Exception as caught_error:
            actual_route = "invalid"
            error = f"请求异常：{type(caught_error).__name__}: {caught_error}"

        latency_ms = round((perf_counter() - start_time) * 1000)

    expected_route = task["expected"]["route"]
    passed = error is None and actual_route == expected_route
    # 返回值示例：
    # {"task_id": "route-refund-001", "actual_route": "refund", "passed": True, "latency_ms": 850}
    return {
        "task_id": task["task_id"],
        "question": task["input"]["question"],
        "expected_route": expected_route,
        "actual_route": actual_route,
        "passed": passed,
        "latency_ms": latency_ms,
        "error": error,
    }


async def main() -> None:
    with TASKS_PATH.open(encoding="utf-8") as tasks_file:
        dataset = json.load(tasks_file)

    # semaphore 是两张“模型请求通行证”。同一时刻最多两道题持有它。
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    coroutines = []
    for task in dataset["tasks"]:
        # 调用 async 函数不会立刻拿到结果，而是得到一个待执行任务。
        # 第一轮后 coroutines 大致是：[第1题任务, 第2题任务, 第3题任务, 第4题任务]。
        coroutines.append(evaluate_one_task(task, semaphore))

    # *coroutines 把列表拆成多个参数。
    # gather 同时启动所有任务，并等待全部结束；返回结果顺序仍与 tasks 顺序一致。
    records = await asyncio.gather(*coroutines)

    passed_count = 0
    for index, record in enumerate(records, start=1):
        if record["passed"]:
            passed_count += 1
        result_text = "通过" if record["passed"] else "失败"
        print(f"第 {index} 题：{record['task_id']} -> {result_text}，耗时 {record['latency_ms']} ms")

    report = {
        "dataset_name": dataset["dataset_name"],
        "dataset_version": dataset["version"],
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
        "summary": {
            "total_count": len(records),
            "passed_count": passed_count,
        },
        "cases": records,
    }
    with REPORT_PATH.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, ensure_ascii=False, indent=2)

    print(f"\n总结果：{passed_count}/{len(records)}")
    print(f"完整报告已写入：{REPORT_PATH}")


# asyncio.run() 启动异步运行环境，再执行 main() 里的 await 代码。
if __name__ == "__main__":
    asyncio.run(main())
