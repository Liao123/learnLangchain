"""第 45 课：缓存保存太久后，判断它已经过期。"""

# 缓存最多可用 300 秒，也就是 5 分钟。
CACHE_TTL_SECONDS = 300

# 这是一条已经存好的缓存。除了 result，还记录它是什么时候保存的。
# saved_at 的实际值是 1000，表示“第 1000 秒时保存”。
cached_entry = {
    "result": {
        "context": "【营业时间与到店服务】\n周末营业到晚上九点。"
    },
    "saved_at": 1000,
}


# ==================== 第一次检查：缓存还有效 ====================

# 这里模拟当前处于第 1100 秒。
current_time = 1100

# 实际计算：1100 - 1000 = 100。
cache_age = current_time - cached_entry["saved_at"]

print("第一次检查：")
print("缓存保存时间：", cached_entry["saved_at"])
print("当前时间：", current_time)
print("缓存年龄：", cache_age)
print("TTL：", CACHE_TTL_SECONDS)

# 100 <= 300 是 True，所以可以继续使用缓存里的 result。
if cache_age <= CACHE_TTL_SECONDS:
    print("结论：缓存有效，可以直接使用 result。")
else:
    print("结论：缓存过期，应该重新检索。")


# ==================== 第二次检查：缓存已经过期 ====================

# 问题和缓存没变，只把当前时间推进到第 1400 秒。
current_time = 1400

# 实际计算：1400 - 1000 = 400。
cache_age = current_time - cached_entry["saved_at"]

print("\n第二次检查：")
print("缓存保存时间：", cached_entry["saved_at"])
print("当前时间：", current_time)
print("缓存年龄：", cache_age)
print("TTL：", CACHE_TTL_SECONDS)

# 400 <= 300 是 False，所以不能再使用旧 result。
if cache_age <= CACHE_TTL_SECONDS:
    print("结论：缓存有效，可以直接使用 result。")
else:
    print("结论：缓存过期，应该重新检索。")


# 真实程序会用 time.time() 代替这里手写的 1100、1400。
# 本课用固定时间，只是为了让“100 秒有效、400 秒过期”一眼可见。
