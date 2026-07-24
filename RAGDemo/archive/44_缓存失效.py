"""第 44 课归档：知识库版本变化后，让旧缓存不再命中。"""

question = "周末几点营业？"
retrieval_cache = {}

# 第一次，资料版本是 v1，key 的实际值是“v1:周末几点营业？”。
knowledge_base_version = "v1"
cache_key = f"{knowledge_base_version}:{question}"
v1_result = {
    "context": "【营业时间与到店服务】\n周六和周日营业时间是早上九点至晚上九点。"
}
retrieval_cache[cache_key] = v1_result

print("第一次资料版本：", knowledge_base_version)
print("第一次缓存 key：", cache_key)
print("当前缓存：", retrieval_cache)

# 第二次，资料更新成 v2。同样的问题会组成一个完全不同的 key。
knowledge_base_version = "v2"
cache_key = f"{knowledge_base_version}:{question}"

print("\n资料更新后版本：", knowledge_base_version)
print("新的缓存 key：", cache_key)

if cache_key in retrieval_cache:
    print("缓存命中：可以复用旧 result。")
else:
    print("缓存未命中：不能使用 v1 的旧 result，应该重新检索。")

    # 模拟重新检索后的新资料。
    v2_result = {
        "context": "【营业时间与到店服务】\n周六和周日营业时间是早上九点至晚上十点。"
    }
    retrieval_cache[cache_key] = v2_result

print("\n最后缓存的键：", list(retrieval_cache.keys()))
print("v1 资料：", retrieval_cache["v1:周末几点营业？"]["context"])
print("v2 资料：", retrieval_cache["v2:周末几点营业？"]["context"])


# 本课重点：缓存 key 包含知识库版本，资料更新后新 key 不会命中旧缓存。
