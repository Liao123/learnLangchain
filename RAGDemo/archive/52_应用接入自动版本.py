"""第 52 课归档：完整应用怎样自动生成缓存版本。"""

import hashlib
from pathlib import Path


index_file = Path(__file__).with_name("父子知识库索引.json")
top_k = 3
min_relevance_score = 0.70
user_role = "public_customer"
question = "周末几点营业？"

# 索引 JSON 内容 -> SHA-256 -> 前 12 位自动版本。
index_hash = hashlib.sha256(index_file.read_bytes()).hexdigest()
index_content_version = f"index-{index_hash[:12]}"

# top_k、阈值也会影响检索 result，所以一起放进缓存版本。
retrieval_cache_version = (
    f"{index_content_version}-top{top_k}-threshold{min_relevance_score:.2f}"
)

cache_key = f"{user_role}:{retrieval_cache_version}:{question}"

print("自动索引版本：", index_content_version)
print("自动缓存版本：", retrieval_cache_version)
print("最终缓存 key：", cache_key)


# 重建索引后，index_hash 会变化，最终 cache_key 也会变化。
