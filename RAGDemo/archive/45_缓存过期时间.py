"""第 45 课归档：缓存保存太久后，判断它已经过期。"""

CACHE_TTL_SECONDS = 300  # 300 秒 = 5 分钟。

# 缓存里同时保存检索结果和保存时刻。
cached_entry = {
    "result": {
        "context": "【营业时间与到店服务】\n周末营业到晚上九点。"
    },
    "saved_at": 1000,
}

# 第一次：1100 - 1000 = 100，100 没超过 300，所以有效。
current_time = 1100
cache_age = current_time - cached_entry["saved_at"]

print("第一次检查：")
print("缓存保存时间：", cached_entry["saved_at"])
print("当前时间：", current_time)
print("缓存年龄：", cache_age)
print("TTL：", CACHE_TTL_SECONDS)

if cache_age <= CACHE_TTL_SECONDS:
    print("结论：缓存有效，可以直接使用 result。")
else:
    print("结论：缓存过期，应该重新检索。")

# 第二次：1400 - 1000 = 400，400 超过 300，所以过期。
current_time = 1400
cache_age = current_time - cached_entry["saved_at"]

print("\n第二次检查：")
print("缓存保存时间：", cached_entry["saved_at"])
print("当前时间：", current_time)
print("缓存年龄：", cache_age)
print("TTL：", CACHE_TTL_SECONDS)

if cache_age <= CACHE_TTL_SECONDS:
    print("结论：缓存有效，可以直接使用 result。")
else:
    print("结论：缓存过期，应该重新检索。")


# 本课重点：缓存年龄没有超过 TTL 才能使用；超过 TTL 就重新检索。
