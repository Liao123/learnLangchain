"""第 52 课：完整应用怎样自动生成缓存版本。"""

import sys
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

# get_index_content_version() 内部就是第 51 课写过的“读索引字节 -> SHA-256 -> 前 12 位”。
from 检索核心.rag_core import get_index_content_version
from 检索核心.retrieval_cache import RetrievalCache


# 这两个配置和完整应用中的值相同。
TOP_K = 3
MIN_RELEVANCE_SCORE = 0.70
USER_ROLE = "public_customer"
question = "周末几点营业？"

# 当前索引内容自动生成版本，例如 "index-001e7af6fbec"。
index_content_version = get_index_content_version()

# 实际值大致是："index-001e7af6fbec-top3-threshold0.70"。
retrieval_cache_version = (
    f"{index_content_version}-top{TOP_K}-threshold{MIN_RELEVANCE_SCORE:.2f}"
)

# make_key() 再把身份、自动版本和问题拼起来。
cache = RetrievalCache(max_size=50, ttl_seconds=300)
cache_key = cache.make_key(USER_ROLE, retrieval_cache_version, question)

print("自动索引版本：", index_content_version)
print("自动缓存版本：", retrieval_cache_version)
print("最终缓存 key：", cache_key)


# 本课重点：rag_cli.py 现在调用同一个 get_index_content_version()，不再手写 v1、v2。
