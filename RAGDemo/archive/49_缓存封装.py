"""第 49 课归档：把缓存 key、TTL 和容量规则封装进一个对象。"""

from collections import OrderedDict


class RetrievalCache:
    def __init__(self, max_size, ttl_seconds):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.entries = OrderedDict()

    def make_key(self, user_role, knowledge_base_version, question):
        return f"{user_role}:{knowledge_base_version}:{question}"

    def get(self, cache_key, current_time):
        entry = self.entries.get(cache_key)
        if entry is None:
            return None

        cache_age = current_time - entry["saved_at"]
        if cache_age > self.ttl_seconds:
            del self.entries[cache_key]
            return None

        self.entries.move_to_end(cache_key)
        return entry["result"]

    def set(self, cache_key, result, current_time):
        self.entries[cache_key] = {
            "result": result,
            "saved_at": current_time,
        }
        self.entries.move_to_end(cache_key)

        if len(self.entries) > self.max_size:
            removed_key, _ = self.entries.popitem(last=False)
            return removed_key
        return None

    def keys(self):
        return list(self.entries.keys())


# 这几行是课堂 demo 实际需要写的调用代码。
cache = RetrievalCache(max_size=2, ttl_seconds=300)
user_role = "normal"
knowledge_base_version = "v1"
weekend_key = cache.make_key(user_role, knowledge_base_version, "周末几点营业？")

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
print("存入两条后：", cache.keys())

weekend_result = cache.get(weekend_key, current_time=1020)
print("\n第 1020 秒读取周末问题：", weekend_result)
print("读取周末问题后：", cache.keys())

refund_key = cache.make_key(user_role, knowledge_base_version, "咖啡豆能退款吗？")
removed_key = cache.set(
    refund_key,
    {"context": "未拆封咖啡豆七天内可以退款。"},
    current_time=1030,
)
print("\n加入退款问题后删除的 key：", removed_key)
print("容量删除后的顺序：", cache.keys())

expired_result = cache.get(weekend_key, current_time=1400)
print("\n第 1400 秒读取周末问题：", expired_result)
print("过期检查后的顺序：", cache.keys())


# 这个对象复用了前面每一课学过的缓存规则，demo 只需要调用它的方法。
