"""第 51 课归档：用索引文件内容自动生成缓存版本。"""

import hashlib
from pathlib import Path


index_file = Path(__file__).with_name("父子知识库索引.json")

# 当前索引文件 -> 原始字节 -> SHA-256 -> 前 12 位版本号。
index_bytes = index_file.read_bytes()
full_index_hash = hashlib.sha256(index_bytes).hexdigest()
index_version = f"index-{full_index_hash[:12]}"

print("索引文件：", index_file.name)
print("索引字节数：", len(index_bytes))
print("完整 SHA-256：", full_index_hash)
print("自动缓存版本：", index_version)

user_role = "public_customer"
question = "周末几点营业？"
cache_key = f"{user_role}:{index_version}:{question}"
print("\n当前缓存 key：", cache_key)

# 不修改真实文件，只在内存中模拟新索引的字节内容。
updated_index_bytes = index_bytes + b"\nnew-index-data"
updated_hash = hashlib.sha256(updated_index_bytes).hexdigest()
updated_version = f"index-{updated_hash[:12]}"
updated_cache_key = f"{user_role}:{updated_version}:{question}"

print("\n模拟索引更新后的版本：", updated_version)
print("模拟更新后的缓存 key：", updated_cache_key)
print("两个版本是否相同：", index_version == updated_version)
print("两个缓存 key 是否相同：", cache_key == updated_cache_key)


# 索引字节变了，hash、版本、缓存 key 都会变，旧缓存不会命中。
