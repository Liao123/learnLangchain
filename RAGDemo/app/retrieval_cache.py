"""把检索缓存的 key、过期和容量规则集中到一个可复用对象中。"""

from collections import OrderedDict


class RetrievalCache:
    """保存检索 result 的内存缓存。"""

    def __init__(self, max_size: int, ttl_seconds: int):
        # 例如 max_size=2、ttl_seconds=300，表示最多两条、每条最多有效五分钟。
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.entries = OrderedDict()

    def make_key(self, user_role: str, knowledge_base_version: str, question: str) -> str:
        """把会影响资料权限的身份、版本和问题合成一个缓存 key。"""
        # 例如返回："normal:v1:周末几点营业？"。
        return f"{user_role}:{knowledge_base_version}:{question}"

    def get(self, cache_key: str, current_time: int):
        """缓存存在且未过期时返回 result；否则返回 None。"""
        entry = self.entries.get(cache_key)
        if entry is None:
            return None

        cache_age = current_time - entry["saved_at"]
        if cache_age > self.ttl_seconds:
            # 过期数据删除后，之后同一个 key 也必须重新检索。
            del self.entries[cache_key]
            return None

        # 命中后移到最后，表示它刚刚被使用，LRU 容量限制时更不容易被删。
        self.entries.move_to_end(cache_key)
        return entry["result"]

    def set(self, cache_key: str, result: dict, current_time: int) -> str | None:
        """保存 result；容量超限时删除最久未使用的 key。"""
        self.entries[cache_key] = {
            "result": result,
            "saved_at": current_time,
        }
        self.entries.move_to_end(cache_key)

        if len(self.entries) > self.max_size:
            removed_key, _ = self.entries.popitem(last=False)
            return removed_key

        return None

    def keys(self) -> list[str]:
        """返回当前缓存 key 的顺序，供终端展示和测试使用。"""
        return list(self.entries.keys())
