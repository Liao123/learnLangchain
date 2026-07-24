"""第 51 课：用索引文件内容自动生成缓存版本。"""

# hashlib：Python 自带库，用来计算文件内容的 SHA-256 指纹。
import hashlib

# Path：定位父子知识库索引 JSON 文件。
from pathlib import Path


# __file__ 是当前 demo.py；parents[2] 往上两层就是 RAGDemo 文件夹。
RAG_ROOT = Path(__file__).resolve().parents[2]
index_file = RAG_ROOT / "data" / "indexes" / "父子知识库索引.json"


# ==================== 第一步：当前索引自动生成版本 ====================

# read_bytes() 读取文件的原始字节。它不是文字列表，而是一整份二进制内容。
index_bytes = index_file.read_bytes()

# sha256(...).hexdigest() 把字节变成一长串十六进制 hash 字符串。
# 完整 hash 有 64 个字符，例如 "8ab3..."；这里只取前 12 个，方便放进缓存 key。
full_index_hash = hashlib.sha256(index_bytes).hexdigest()
index_version = f"index-{full_index_hash[:12]}"

# 当前实际值会因索引文件内容不同而不同，例如："index-8ab3cdef1234"。
print("索引文件：", index_file.name)
print("索引字节数：", len(index_bytes))
print("完整 SHA-256：", full_index_hash)
print("自动缓存版本：", index_version)


# ==================== 第二步：用版本组成缓存 key ====================

user_role = "public_customer"
question = "周末几点营业？"

# 实际结构是："public_customer:index-前12位hash:周末几点营业？"。
cache_key = f"{user_role}:{index_version}:{question}"
print("\n当前缓存 key：", cache_key)


# ==================== 第三步：模拟索引更新 ====================

# 这里不修改真实索引文件，只在内存中假设新索引多了一行数据。
# 原索引字节 + b"\nnew-index-data" 一定和原索引不同，因此 hash 也不同。
updated_index_bytes = index_bytes + b"\nnew-index-data"
updated_hash = hashlib.sha256(updated_index_bytes).hexdigest()
updated_version = f"index-{updated_hash[:12]}"
updated_cache_key = f"{user_role}:{updated_version}:{question}"

print("\n模拟索引更新后的版本：", updated_version)
print("模拟更新后的缓存 key：", updated_cache_key)
print("两个版本是否相同：", index_version == updated_version)
print("两个缓存 key 是否相同：", cache_key == updated_cache_key)


# 本课重点：索引内容变化 -> hash 变化 -> version 变化 -> cache key 变化。
