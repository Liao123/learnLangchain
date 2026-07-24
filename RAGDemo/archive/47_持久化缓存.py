"""第 47 课归档：把内存缓存写入 JSON，程序重启后再读回来。"""

import json
from pathlib import Path


# JSON 文件和这个 archive 脚本放在同一文件夹。
cache_file = Path(__file__).with_name("持久化缓存示例.json")

retrieval_cache = {
    "v1:周末几点营业？": {
        "context": "【营业时间与到店服务】\n周末营业到晚上九点。"
    }
}

print("写入文件前的内存缓存：", retrieval_cache)

# 字典 -> JSON 文字 -> 文件。
json_text = json.dumps(retrieval_cache, ensure_ascii=False, indent=2)
cache_file.write_text(json_text, encoding="utf-8")

print("\n已写入缓存文件：", cache_file)
print("文件里的 JSON 文字：")
print(json_text)

# 模拟程序重启后，内存变量变空。
retrieval_cache = {}
print("\n模拟重启后的内存缓存：", retrieval_cache)

# 文件 -> JSON 文字 -> Python 字典。
saved_json_text = cache_file.read_text(encoding="utf-8")
retrieval_cache = json.loads(saved_json_text)

print("\n从文件恢复后的内存缓存：", retrieval_cache)

cache_key = "v1:周末几点营业？"
print("\n恢复后按 key 取到的 context：")
print(retrieval_cache[cache_key]["context"])


# 本课重点：写入磁盘的 JSON 不会随着 Python 变量清空而消失。
