"""第 40 课：先判断查哪个主题，再在允许范围内检索。"""

# sys：Python 用它临时增加“去哪里找其他 Python 文件”的位置。
import sys

# Path：用来处理文件夹路径。
from pathlib import Path


# __file__ 是当前 demo.py 的路径；parents[2] 往上走两层，得到 RAGDemo 文件夹。
RAG_ROOT = Path(__file__).resolve().parents[2]

# rag_core.py 在 RAGDemo/app/ 中。放进搜索路径后才能 import 前面课程学过的检索工具。
sys.path.insert(0, str(RAG_ROOT / "app"))

# 这三个函数都是已学过的：读取索引、加载 BGE、在给定资料范围中检索完整父章节。
# 本课新出现的“路由判断、缩小子片段范围”会直接写在这个 demo.py 里。
from 检索核心.rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 默认问题里有“周末”“营业”两个词，应该路由到“到店服务”。
question = "周末几点营业？"

# 低于 0.50 的资料不可信。路由成功也不等于资料一定相关，仍要保留相似度阈值。
MIN_RELEVANCE_SCORE = 0.50

# 每个路由都像一份“知识库目录卡”。
# keywords：看到这些词时，认为问题可能属于这个主题。
# parent_ids：这个主题允许检索哪些完整父章节。
# 这里的 parent_id 来自现有父子知识库索引，不是新建的第二份 JSON 文件。
knowledge_base_routes = {
    "会员与订单": {
        "keywords": ["会员", "积分", "优惠", "退款", "订单", "咖啡豆", "饮品"],
        "parent_ids": ["parent_1", "parent_2", "parent_3"],
    },
    "到店服务": {
        "keywords": ["营业", "周末", "周六", "周日", "打烊", "预订", "到店", "门店"],
        "parent_ids": ["parent_4"],
    },
}

# 读取全部 4 个父章节、9 个子片段和 9 行子片段向量。
index_data = load_parent_child_index()


# ==================== 第一步：先用关键词决定路由 ====================

# matched_routes 会保存命中的每一份知识库。
# 默认问题运行后，它大致是：
# [{"route_name": "到店服务", "matched_keywords": ["营业", "周末"], "parent_ids": ["parent_4"]}]
matched_routes = []

# items() 每次取出“路由名字 + 路由配置”。
# 第一次 route_name 是“会员与订单”，第二次是“到店服务”。
for route_name, route in knowledge_base_routes.items():
    # 记录这个路由到底是被问题里的哪些词命中的，方便终端解释。
    matched_keywords = []

    # 逐个检查这个路由的关键词，例如检查“营业”是否出现在“周末几点营业？”里。
    for keyword in route["keywords"]:
        if keyword in question:
            matched_keywords.append(keyword)

    # 至少命中一个词，才把这个路由加入结果。
    if matched_keywords:
        matched_routes.append({
            "route_name": route_name,
            "matched_keywords": matched_keywords,
            "parent_ids": route["parent_ids"],
        })

# 没有路由就不调用 BGE。这样“维修电脑”不会被咖啡店资料硬答。
if not matched_routes:
    print("用户问题：", question)
    print("路由结果：没有命中任何知识库主题。")
    print("本轮不做 BGE 检索，应该拒答或转人工。")
    raise SystemExit


# ==================== 第二步：根据路由缩小子片段范围 ====================

# allowed_parent_ids 是“不重复的允许父章节名单”。
# 默认题只命中“到店服务”时，最后实际值是：{"parent_4"}。
allowed_parent_ids = set()

for matched_route in matched_routes:
    # update(...) 会把一个列表中的多个值一次加入 set。
    # 默认题把 ["parent_4"] 加进去；多路由时会把多份路由的父章节合并起来。
    allowed_parent_ids.update(matched_route["parent_ids"])

# 找出这些父章节下面的子片段位置。
# 默认题时，child_8 和 child_9 在全库 children 列表中的位置是 7、8。
allowed_child_indices = []
for child_index in range(len(index_data["children"])):
    child = index_data["children"][child_index]

    if child["parent_id"] in allowed_parent_ids:
        allowed_child_indices.append(child_index)

# routed_children 是筛选后的文字资料。
# 默认题时实际是 [child_8, child_9]，不再包含退款、会员等另外 7 个子片段。
routed_children = []
for child_index in allowed_child_indices:
    routed_children.append(index_data["children"][child_index])

# copy() 创建 index_data 的新外层字典，避免改坏原始 9 段资料。
# 之后只把“子片段”和“子片段向量”换成路由允许的那一部分。
# 默认题创建后，routed_index_data["children"] 只有 child_8、child_9；
# 但 routed_index_data["parents_by_id"] 仍保留全部章节查询表，方便通过 child 的 parent_id 找完整原文。
routed_index_data = index_data.copy()
routed_index_data["children"] = routed_children

# child_embeddings 原来有 9 行向量；用 [7, 8] 取出第 8、9 行后，只剩 child_8、child_9 的向量。
# 所以 routed_index_data["child_embeddings"].shape 大致从 (9, 512) 变成 (2, 512)。
routed_index_data["child_embeddings"] = index_data["child_embeddings"][allowed_child_indices]


# ==================== 第三步：只在路由后的范围里做 BGE 检索 ====================

print("正在加载 BGE 向量模型...")
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])

# 注意传入的是 routed_index_data，不是原始 index_data。
# 所以 retrieve_parent_context() 看到的只有路由允许的子片段和向量。
# 默认题成功时，result["matched_children"] 大致是 [{"child": child_8, "score": 0.7...}, ...]；
# result["parents"] 大致是 [{"parent_id": "parent_4", "title": "营业时间与到店服务", ...}]；
# result["context"] 则是 parent_4 的完整章节文字，后面可直接交给 AI。
result = retrieve_parent_context(
    question,
    routed_index_data,
    embedding_model,
    top_k=3,
    min_relevance_score=MIN_RELEVANCE_SCORE,
)


# ==================== 第四步：把本轮真实过程打印出来 ====================

print("\n用户问题：", question)
print("BGE 模型来源：", model_source)

print("\n路由命中：")
for matched_route in matched_routes:
    print(
        f"- {matched_route['route_name']}，"
        f"命中关键词：{matched_route['matched_keywords']}，"
        f"允许父章节：{matched_route['parent_ids']}"
    )

print("\n本轮允许的父章节 ID：", allowed_parent_ids)
print("本轮允许的子片段：", [child["child_id"] for child in routed_children])
print(f"全库子片段数量：{len(index_data['children'])}")
print(f"路由后子片段数量：{len(routed_children)}")

if result["best_score"] is None:
    print("\n路由范围里没有任何子片段，应该检查路由配置。")
else:
    print(f"\n路由范围内最高相似度：{result['best_score']:.4f}")

if not result["parents"]:
    print("没有资料通过相似度阈值，本次应该拒答。")
else:
    print("\n最终找回的完整父章节：")
    for parent in result["parents"]:
        print("-", parent["title"])

    # result["context"] 是后续放进 SystemMessage 的完整章节文字。
    print("\n后续会交给 AI 的资料：")
    print(result["context"])


# 本课重点：
# 1. 路由先决定范围，BGE 再在范围内检索。
# 2. 路由没有命中时，本例直接停止，不把全部知识库拿去硬搜。
# 3. 路由成功后，仍要用相似度阈值判断资料是否真的相关。
