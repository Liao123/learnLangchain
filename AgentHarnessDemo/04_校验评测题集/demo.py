"""Agent Harness 第 4 课：在运行 Agent 前，先校验评测题集。"""

import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError


class TaskInput(BaseModel):
    # input 的数据格式只能是：{"question": "我想退钱"}
    question: str


class ExpectedResult(BaseModel):
    # 人工标准答案只能是三种路线之一。
    # 写成 {"route": "payment"} 就是不合格题目。
    route: Literal["order", "refund", "human"]


class RoutingTask(BaseModel):
    # 一道题的完整格式。
    task_id: str
    case_type: str
    input: TaskInput
    expected: ExpectedResult


class RoutingDataset(BaseModel):
    # 整个题集的完整格式。
    dataset_name: str
    version: str
    tasks: list[RoutingTask]


LESSON_DIR = Path(__file__).resolve().parent
VALID_DATASET_PATH = LESSON_DIR / "数据" / "routing_tasks.json"
ERROR_EXAMPLE_PATH = LESSON_DIR / "数据" / "routing_tasks_error_example.json"


def main() -> None:
    # 默认 mode="valid"，读正常题集。
    # 运行 py demo.py invalid 时，mode="invalid"，读故意写错的示例文件。
    mode = sys.argv[1] if len(sys.argv) >= 2 else "valid"

    if mode == "valid":
        dataset_path = VALID_DATASET_PATH
    elif mode == "invalid":
        dataset_path = ERROR_EXAMPLE_PATH
    else:
        print("用法：py demo.py")
        print("或：py demo.py invalid")
        return

    # raw_dataset 的值还是普通 Python 字典，来自 JSON 文件。
    # 例如：{"dataset_name": "客服路由基础题集", "version": "v1", "tasks": [{...}]}
    with dataset_path.open(encoding="utf-8") as dataset_file:
        raw_dataset = json.load(dataset_file)

    try:
        # model_validate 会逐层检查：题集 -> 每道题 -> input / expected。
        # 正常时，dataset 是 RoutingDataset 对象，不再是普通字典。
        dataset = RoutingDataset.model_validate(raw_dataset)
    except ValidationError as error:
        # 不合格就立刻停止。此时还没有调用任何模型，也没有花 API 费用。
        print(f"题集不合格：{dataset_path.name}")
        for item in error.errors():
            print(f"- 出错位置 {item['loc']}：{item['msg']}")
        return

    # 例如：dataset.dataset_name = "客服路由基础题集"
    # dataset.tasks[0].expected.route = "order"
    print(f"题集校验通过：{dataset.dataset_name} {dataset.version}")
    print(f"题目数量：{len(dataset.tasks)}")
    print(f"第一题期望路线：{dataset.tasks[0].expected.route}")
    print("现在才可以把这套题交给 Agent Harness 批量运行。")


if __name__ == "__main__":
    main()
