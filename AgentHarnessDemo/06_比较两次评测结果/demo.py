"""Agent Harness 第 6 课：比较基准评测和新版本评测，找出回归。"""

import json
import sys
from pathlib import Path


LESSON_DIR = Path(__file__).resolve().parent
BASELINE_PATH = LESSON_DIR / "数据" / "baseline_report.json"
CANDIDATE_PATH = LESSON_DIR / "数据" / "candidate_report.json"
CHANGED_DATASET_CANDIDATE_PATH = LESSON_DIR / "数据" / "candidate_report_dataset_changed.json"
COMPARISON_PATH = LESSON_DIR / "输出" / "comparison.json"


def load_report(report_path: Path) -> dict:
    """读取一份历史评测报告，得到普通 Python 字典。"""
    with report_path.open(encoding="utf-8") as report_file:
        return json.load(report_file)


def main() -> None:
    # 默认比较同一份题集上的两次运行。
    # 运行 py demo.py changed_dataset 时，改用“题集已变化”的示例。
    mode = sys.argv[1] if len(sys.argv) >= 2 else "normal"
    if mode == "normal":
        candidate_path = CANDIDATE_PATH
    elif mode == "changed_dataset":
        candidate_path = CHANGED_DATASET_CANDIDATE_PATH
    else:
        print("用法：py demo.py")
        print("或：py demo.py changed_dataset")
        return

    baseline = load_report(BASELINE_PATH)
    candidate = load_report(candidate_path)

    # 先确认两次报告是不是在同一份题集上跑出来的。
    # 如果 hash 不同，80% 和 90% 也不能直接说谁更好。
    baseline_hash = baseline["run"]["dataset_sha256"]
    candidate_hash = candidate["run"]["dataset_sha256"]
    if baseline_hash != candidate_hash:
        comparison = {
            "comparable": False,
            "reason": "两次运行使用的题集内容不同，不能直接比较成功率。",
            "baseline_dataset_sha256": baseline_hash,
            "candidate_dataset_sha256": candidate_hash,
        }
        with COMPARISON_PATH.open("w", encoding="utf-8") as comparison_file:
            json.dump(comparison, comparison_file, ensure_ascii=False, indent=2)

        print("不能比较：两次运行的题集指纹不同。")
        print(f"比较结果已写入：{COMPARISON_PATH}")
        return

    # 把基准报告整理成：任务 id -> 是否通过。
    # 例如：baseline_passed_by_task["route-refund-002"] 的值是 True。
    baseline_passed_by_task = {}
    for case in baseline["cases"]:
        baseline_passed_by_task[case["task_id"]] = case["evaluation"]["passed"]

    regressions = []
    for case in candidate["cases"]:
        task_id = case["task_id"]
        candidate_passed = case["evaluation"]["passed"]
        baseline_passed = baseline_passed_by_task.get(task_id)

        # 只有“以前通过、现在失败”才叫回归。
        if baseline_passed is True and candidate_passed is False:
            regressions.append(task_id)

    baseline_rate = baseline["summary"]["success_rate"]
    candidate_rate = candidate["summary"]["success_rate"]
    rate_change = candidate_rate - baseline_rate

    comparison = {
        "comparable": True,
        "baseline_prompt_version": baseline["run"]["prompt_version"],
        "candidate_prompt_version": candidate["run"]["prompt_version"],
        "baseline_success_rate": baseline_rate,
        "candidate_success_rate": candidate_rate,
        "rate_change": rate_change,
        "regressions": regressions,
    }
    with COMPARISON_PATH.open("w", encoding="utf-8") as comparison_file:
        json.dump(comparison, comparison_file, ensure_ascii=False, indent=2)

    print(f"基准版本：{comparison['baseline_prompt_version']}，成功率 {baseline_rate:.0%}")
    print(f"新版本：{comparison['candidate_prompt_version']}，成功率 {candidate_rate:.0%}")
    print(f"成功率变化：{rate_change:+.0%}")
    if regressions:
        print("发生回归的任务：")
        for task_id in regressions:
            print(f"- {task_id}")
    else:
        print("没有发现从通过变为失败的任务。")
    print(f"比较结果已写入：{COMPARISON_PATH}")


if __name__ == "__main__":
    main()
