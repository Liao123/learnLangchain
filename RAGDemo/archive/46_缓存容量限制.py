"""第 46 课归档：缓存超过容量后，删除最久未使用的数据。"""

from collections import OrderedDict


MAX_CACHE_SIZE = 2
retrieval_cache = OrderedDict()

# 加入后，顺序是 ["q1", "q2"]。
retrieval_cache["q1"] = "周末营业时间的 result"
retrieval_cache["q2"] = "会员积分的 result"
print("加入 q1、q2 后：", list(retrieval_cache.keys()))

# q1 再次被使用，顺序变为 ["q2", "q1"]。
retrieval_cache.move_to_end("q1")
print("再次使用 q1 后：", list(retrieval_cache.keys()))

# 加入 q3 后，顺序暂时是 ["q2", "q1", "q3"]。
retrieval_cache["q3"] = "退款规则的 result"
print("加入 q3 后：", list(retrieval_cache.keys()))

if len(retrieval_cache) > MAX_CACHE_SIZE:
    # 最前面的 q2 最久未使用，因此被删除。
    removed_key, removed_result = retrieval_cache.popitem(last=False)
    print("删除最久未使用的 key：", removed_key)
    print("被删除的 result：", removed_result)

print("最终缓存顺序：", list(retrieval_cache.keys()))


# LRU：缓存满时，删除最久没有被使用的数据。
