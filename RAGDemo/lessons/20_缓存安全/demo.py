"""第 48 课：把用户权限放进缓存 key，避免不同用户共用资料。"""

# 两个用户问的是完全相同的问题。
question = "我有什么会员优惠？"

# 知识库版本和第 44 课一样，也放进 key。
knowledge_base_version = "v1"

# 金卡会员的身份标识。
gold_member_role = "gold"

# 普通会员的身份标识。
normal_member_role = "normal"


# ==================== 先看错误做法：key 只有问题 ====================

# 这个错误 key 的实际值只有："我有什么会员优惠？"。
# 它没有记录提问者是金卡还是普通会员。
unsafe_cache_key = question

# 假设金卡会员先问，缓存保存的是金卡九折资料。
unsafe_cache = {
    unsafe_cache_key: "金卡会员享受现制饮品九折优惠。"
}

print("错误 key：", unsafe_cache_key)
print("普通会员问同一问题时，错误缓存会给：", unsafe_cache[unsafe_cache_key])
print("这不安全：普通会员不应该直接复用金卡资料。")


# ==================== 正确做法：权限也放进 key ====================

# f 字符串把“会员身份、版本、问题”拼在一起。
# 金卡 key 的实际值："gold:v1:我有什么会员优惠？"。
gold_cache_key = f"{gold_member_role}:{knowledge_base_version}:{question}"

# 普通会员 key 的实际值："normal:v1:我有什么会员优惠？"。
normal_cache_key = f"{normal_member_role}:{knowledge_base_version}:{question}"

safe_cache = {
    gold_cache_key: "金卡会员享受现制饮品九折优惠。"
}

print("\n金卡缓存 key：", gold_cache_key)
print("普通会员缓存 key：", normal_cache_key)

# normal key 和 gold key 不相同，所以普通会员不会命中金卡缓存。
if normal_cache_key in safe_cache:
    print("缓存命中：", safe_cache[normal_cache_key])
else:
    print("普通会员缓存未命中：应按普通会员权限重新检索。")


# 本课重点：缓存 key 不只包含问题，还要包含会影响资料权限的身份信息。
