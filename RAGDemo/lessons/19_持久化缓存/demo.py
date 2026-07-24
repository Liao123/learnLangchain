"""第 47 课：把内存缓存写入 JSON，程序重启后再读回来。"""

# json：Python 自带模块，负责 Python 字典和 JSON 文字互相转换。
import json

# Path：定位缓存文件的位置。
from pathlib import Path


# with_name() 表示“保持 demo.py 所在文件夹不变，只把文件名换成 demo_retrieval_cache.json”。
# 例如实际位置是：RAGDemo/lessons/19_持久化缓存/demo_retrieval_cache.json。
cache_file = Path(__file__).with_name("demo_retrieval_cache.json")

# 这是程序运行期间的内存缓存。
# 键是“知识库版本:问题”，值是可 JSON 保存的 result 内容。
retrieval_cache = {
    "v1:周末几点营业？": {
        "context": "【营业时间与到店服务】\n周末营业到晚上九点。"
    }
}

print("写入文件前的内存缓存：", retrieval_cache)


# ==================== 第一步：字典写入 JSON 文件 ====================

# json.dumps(...) 把 Python 字典变成 JSON 字符串。
# ensure_ascii=False 让文件里直接保留中文，而不是变成 \u4e2d 这种编码。
# indent=2 让 JSON 换行缩进，打开文件时更好读。
json_text = json.dumps(retrieval_cache, ensure_ascii=False, indent=2)

# write_text() 把 JSON 字符串写进磁盘文件，encoding="utf-8" 保证中文正确保存。
cache_file.write_text(json_text, encoding="utf-8")

print("\n已写入缓存文件：", cache_file)
print("文件里的 JSON 文字：")
print(json_text)


# ==================== 第二步：模拟程序重启，内存清空 ====================

# 真正关闭 Python 后，原来的变量也会消失。
# 这里手动重新赋值为空字典，模拟“新程序刚刚启动”。
retrieval_cache = {}
print("\n模拟重启后的内存缓存：", retrieval_cache)


# ==================== 第三步：从 JSON 文件恢复缓存 ====================

# read_text() 从文件读取 JSON 字符串。
saved_json_text = cache_file.read_text(encoding="utf-8")

# json.loads() 把 JSON 字符串还原成 Python 字典。
retrieval_cache = json.loads(saved_json_text)

print("\n从文件恢复后的内存缓存：", retrieval_cache)

# 这行证明恢复后仍然能按照 key 取到原来的资料。
cache_key = "v1:周末几点营业？"
print("\n恢复后按 key 取到的 context：")
print(retrieval_cache[cache_key]["context"])


# 本课重点：缓存写进 JSON 后，即使 Python 内存清空，也能从文件恢复。
