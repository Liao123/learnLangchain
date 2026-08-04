"""Agent Harness 第 5 课：为一次评测记录模型、提示词和题集信息。"""

import hashlib
import json
from datetime import datetime
from pathlib import Path


LESSON_DIR = Path(__file__).resolve().parent
DATASET_PATH = LESSON_DIR / "数据" / "routing_tasks.json"
MANIFEST_PATH = LESSON_DIR / "输出" / "run_manifest.json"

# 实际批量评测时，这些值应和 run_agent() 中真正使用的配置保持一致。
MODEL_NAME = "deepseek-v4-pro"
PROMPT_VERSION = "router-v1"


# read_text() 读到的是整个 JSON 文件的字符串。
# dataset_text 的开头大致是：'{\n  "dataset_name": "客服路由基础题集", ...'
dataset_text = DATASET_PATH.read_text(encoding="utf-8")

# json.loads() 再把字符串变成 Python 字典，方便读取 name / version / tasks。
dataset = json.loads(dataset_text)

# encode("utf-8") 把字符串变成字节，sha256 才能计算哈希。
# dataset_hash 的值是一长串固定字符，例如：'a34f...9c2e'。
# 只要题集文件任意一个字符变了，计算出的 hash 就会不同。
dataset_hash = hashlib.sha256(dataset_text.encode("utf-8")).hexdigest()

# manifest 是“本次运行的身份证”。它不放评测结果，只说明结果的来源。
# 值示例：
# {"model_name": "deepseek-v4-pro", "prompt_version": "router-v1",
#  "dataset_version": "v1", "dataset_sha256": "a34f..."}
manifest = {
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "model_name": MODEL_NAME,
    "prompt_version": PROMPT_VERSION,
    "dataset_name": dataset["dataset_name"],
    "dataset_version": dataset["version"],
    "dataset_sha256": dataset_hash,
    "task_count": len(dataset["tasks"]),
}

with MANIFEST_PATH.open("w", encoding="utf-8") as manifest_file:
    json.dump(manifest, manifest_file, ensure_ascii=False, indent=2)

print("本次评测运行信息：")
print(f"- 模型：{manifest['model_name']}")
print(f"- 提示词版本：{manifest['prompt_version']}")
print(f"- 题集：{manifest['dataset_name']} {manifest['dataset_version']}")
print(f"- 题集指纹前 12 位：{dataset_hash[:12]}")
print(f"完整运行信息已写入：{MANIFEST_PATH}")
