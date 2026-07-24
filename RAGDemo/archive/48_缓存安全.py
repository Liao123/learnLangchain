"""第 48 课归档：把用户权限放进缓存 key，避免不同用户共用资料。"""

question = "我有什么会员优惠？"
knowledge_base_version = "v1"
gold_member_role = "gold"
normal_member_role = "normal"

# 错误做法：key 只有问题。普通会员会误读金卡缓存。
unsafe_cache_key = question
unsafe_cache = {
    unsafe_cache_key: "金卡会员享受现制饮品九折优惠。"
}

print("错误 key：", unsafe_cache_key)
print("普通会员问同一问题时，错误缓存会给：", unsafe_cache[unsafe_cache_key])
print("这不安全：普通会员不应该直接复用金卡资料。")

# 正确做法：身份、版本、问题一起组成 key。
gold_cache_key = f"{gold_member_role}:{knowledge_base_version}:{question}"
normal_cache_key = f"{normal_member_role}:{knowledge_base_version}:{question}"

safe_cache = {
    gold_cache_key: "金卡会员享受现制饮品九折优惠。"
}

print("\n金卡缓存 key：", gold_cache_key)
print("普通会员缓存 key：", normal_cache_key)

if normal_cache_key in safe_cache:
    print("缓存命中：", safe_cache[normal_cache_key])
else:
    print("普通会员缓存未命中：应按普通会员权限重新检索。")


# 本课重点：会影响权限的身份信息必须进入缓存 key。
