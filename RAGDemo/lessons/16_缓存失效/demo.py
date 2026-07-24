"""第 44 课：知识库版本变化后，让旧缓存不再命中。"""

# 问题还是同一个字符串。
question = "周末几点营业？"

# 这是本地内存缓存。键是“版本:问题”，值是当时检索得到的 result。
retrieval_cache = {}


# ==================== 第一次：知识库是 v1 ====================

knowledge_base_version = "v1"

# f"{版本}:{问题}" 会把两个变量拼成一个字符串。
# 当前实际值："v1:周末几点营业？"。
cache_key = f"{knowledge_base_version}:{question}"

# 这是 v1 时假设已经检索到的结果。
# 重点不是 result 内容，而是它被存在哪个 key 下面。
v1_result = {
    "context": "【营业时间与到店服务】\n周六和周日营业时间是早上九点至晚上九点。"
}

retrieval_cache[cache_key] = v1_result

print("第一次资料版本：", knowledge_base_version)
print("第一次缓存 key：", cache_key)
print("当前缓存：", retrieval_cache)


# ==================== 第二次：知识库更新成 v2 ====================

# 假设资料更新后，周末营业时间改成晚上十点。
knowledge_base_version = "v2"

# 问题没变，但版本变了，所以 cache_key 的实际值变成："v2:周末几点营业？"。
cache_key = f"{knowledge_base_version}:{question}"

print("\n资料更新后版本：", knowledge_base_version)
print("新的缓存 key：", cache_key)

# 字典里只有 "v1:周末几点营业？"，没有新的 "v2:周末几点营业？"。
# 所以这里会是 False，程序知道不能使用旧结果。
if cache_key in retrieval_cache:
    print("缓存命中：可以复用旧 result。")
else:
    print("缓存未命中：不能使用 v1 的旧 result，应该重新检索。")

    # 这里模拟“重新检索后”得到的新资料。真实 RAG 中，这一步会调用 retrieve_parent_context()。
    v2_result = {
        "context": "【营业时间与到店服务】\n周六和周日营业时间是早上九点至晚上十点。"
    }
    retrieval_cache[cache_key] = v2_result

print("\n最后缓存的键：", list(retrieval_cache.keys()))
print("v1 资料：", retrieval_cache["v1:周末几点营业？"]["context"])
print("v2 资料：", retrieval_cache["v2:周末几点营业？"]["context"])


# 本课重点：不必马上删掉 v1；只要新版本使用 v2 key，旧数据就不会被新请求误用。
