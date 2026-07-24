"""第 46 课：缓存超过容量后，删除最久未使用的数据。"""

# OrderedDict 是 Python 自带的有顺序字典。
from collections import OrderedDict


# 最多只能保留 2 条缓存。
MAX_CACHE_SIZE = 2

# 刚创建时是空的有顺序字典。
retrieval_cache = OrderedDict()


# ==================== 先放入 q1、q2 ====================

retrieval_cache["q1"] = "周末营业时间的 result"
retrieval_cache["q2"] = "会员积分的 result"

# keys() 按当前顺序返回 key。现在实际是 ["q1", "q2"]。
print("加入 q1、q2 后：", list(retrieval_cache.keys()))


# ==================== 再次使用 q1 ====================

# 假设用户又问了一次 q1。q1 虽然最早存入，但现在刚刚被使用。
# move_to_end("q1") 把 q1 移到最后，实际顺序变成 ["q2", "q1"]。
retrieval_cache.move_to_end("q1")
print("再次使用 q1 后：", list(retrieval_cache.keys()))


# ==================== 加入 q3，容量超过 2 ====================

retrieval_cache["q3"] = "退款规则的 result"

# 现在有 3 条，实际顺序是 ["q2", "q1", "q3"]。
print("加入 q3 后：", list(retrieval_cache.keys()))

# len(...) 现在是 3，3 > 2，所以需要删除一条。
if len(retrieval_cache) > MAX_CACHE_SIZE:
    # popitem(last=False) 删除最前面的项目。
    # 当前最前面是 q2，因此 removed_key = "q2"，removed_result = "会员积分的 result"。
    removed_key, removed_result = retrieval_cache.popitem(last=False)
    print("删除最久未使用的 key：", removed_key)
    print("被删除的 result：", removed_result)

# q1 最近被使用过，q3 刚刚加入，所以最终实际顺序是 ["q1", "q3"]。
print("最终缓存顺序：", list(retrieval_cache.keys()))


# 本课重点：不是删除“最早加入”的数据，而是删除“最久没被使用”的数据。
