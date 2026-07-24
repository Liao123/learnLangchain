"""按元数据过滤后再检索的应用示例。"""

from rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 订单系统已经知道用户买的是现制饮品；这不是模型猜的，是业务系统已有的信息。
metadata_filters = {"商品类型": "现制饮品"}
question = "可以退款吗？"

index_data = load_parent_child_index()
print("正在加载 BGE 向量模型...")
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])

# 只在“现制饮品”的资料里比较相似度，咖啡豆退款规则不会参与本次搜索。
result = retrieve_parent_context(
    question,
    index_data,
    embedding_model,
    min_relevance_score=0.50,
    metadata_filters=metadata_filters,
)

print("BGE 模型来源：", model_source)
print("用户问题：", question)
print("已知条件：", metadata_filters)
print("实际找回的章节：", [parent["title"] for parent in result["parents"]])
print("\n完整资料：")
print(result["context"])