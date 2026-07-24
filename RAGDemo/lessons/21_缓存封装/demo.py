"""第 49 课：使用封装好的缓存对象，不再重复手写缓存规则。"""

import sys
from pathlib import Path


RAG_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAG_ROOT / "app"))

# RetrievalCache 内部已经封装了前面学过的权限 key、TTL 和 LRU 容量限制。
from 检索核心.retrieval_cache import RetrievalCache


# 创建缓存对象：最多保留 2 条，每条最多有效 300 秒。
cache = RetrievalCache(max_size=2, ttl_seconds=300)

# 这三个值会共同决定缓存 key。
user_role = "normal"
knowledge_base_version = "v1"
weekend_question = "周末几点营业？"

# make_key() 的实际值是："normal:v1:周末几点营业？"。
weekend_key = cache.make_key(user_role, knowledge_base_version, weekend_question)


# ==================== 存入两条缓存 ====================

cache.set(
    weekend_key,
    {"context": "周末营业到晚上九点。"},
    current_time=1000,
)

member_key = cache.make_key(user_role, knowledge_base_version, "普通会员有什么积分？")
cache.set(
    member_key,
    {"context": "普通会员每消费一元获得一倍积分。"},
    current_time=1010,
)

# 现在实际顺序是：
# ["normal:v1:周末几点营业？", "normal:v1:普通会员有什么积分？"]。
print("存入两条后：", cache.keys())


# ==================== 读取周末问题，确认缓存命中 ====================

# 1020 - 1000 = 20 秒，没有超过 300 秒，所以返回真正的 result 字典。
weekend_result = cache.get(weekend_key, current_time=1020)
print("\n第 1020 秒读取周末问题：", weekend_result)

# 周末问题刚被读取，变成最近使用；顺序实际变成：
# ["normal:v1:普通会员有什么积分？", "normal:v1:周末几点营业？"]。
print("读取周末问题后：", cache.keys())


# ==================== 加入第三条，触发容量删除 ====================

refund_key = cache.make_key(user_role, knowledge_base_version, "咖啡豆能退款吗？")
removed_key = cache.set(
    refund_key,
    {"context": "未拆封咖啡豆七天内可以退款。"},
    current_time=1030,
)

# 当前容量从 2 变成 3，最久未使用的是 member_key，所以 removed_key 实际是 member_key。
print("\n加入退款问题后删除的 key：", removed_key)
print("容量删除后的顺序：", cache.keys())


# ==================== 时间太久后，缓存过期 ====================

# 1400 - 1000 = 400 秒，超过 300 秒，get() 返回 None，并删除 weekend_key。
expired_result = cache.get(weekend_key, current_time=1400)
print("\n第 1400 秒读取周末问题：", expired_result)
print("过期检查后的顺序：", cache.keys())


# 本课重点：demo 不再手写缓存内部规则，只调用 make_key、set、get、keys。
