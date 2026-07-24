"""第 36 课：先按元数据过滤，再做语义检索。"""

# sys：Python 用它临时增加“去哪里找其他 Python 文件”的位置。
import sys

# Path：用来处理文件夹路径，比手动拼接字符串更不容易写错。
from pathlib import Path


# __file__ 就是当前 demo.py 的路径。
# parents[2] 表示从 demo.py 往上走两层，得到 RAGDemo 文件夹。
RAG_ROOT = Path(__file__).resolve().parents[2]

# rag_core.py 放在 RAGDemo/app/ 中。
# insert(0, ...) 把 app 放到 Python 最先查找的位置，下面才能 import 它。
sys.path.insert(0, str(RAG_ROOT / "app"))

# load_parent_child_index()：读取索引、父章节和元数据。
# load_embedding_model()：加载把文字变成向量的 BGE 模型。
# retrieve_parent_context()：先筛资料，再找最相关的完整章节。
from rag_core import load_embedding_model, load_parent_child_index, retrieve_parent_context


# 低于这个分数的片段不可靠，不会被当作本轮资料。
MIN_RELEVANCE_SCORE = 0.50

# 这份信息来自订单系统：用户买的是现制饮品。
# 字典用“字段名: 值”的方式保存条件，这里就是“商品类型: 现制饮品”。
# 这个变量当前的实际数据是：{"商品类型": "现制饮品"}。
metadata_filters = {"商品类型": "现制饮品"}

# 用户没有说自己买了什么，只问“可以退款吗”。
# 单看这句话，程序无法知道应该看咖啡豆规则还是现制饮品规则。
question = "可以退款吗？"

# 读取父子索引，并把元数据加到每个父章节上。
# index_data 是一个大字典，里面有父章节、子片段、向量和查询表。
# 例如 index_data["parents"][1]["metadata"] 的数据是：{"商品类型": "现制饮品", "业务主题": "订单修改与退款"}。
index_data = load_parent_child_index()
print("正在加载 BGE 向量模型...")

# index_data["embedding_model"] 取出构建索引时使用的模型名称。
# 逗号左边的两个变量会接住函数返回的两个值：模型对象和模型来源。
# model_source 运行后通常会是本地模型路径，或 "BAAI/bge-small-zh-v1.5" 这个模型名称。
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])

# 程序先用 metadata_filters 挑出“现制饮品”资料，再比较这些资料和问题的相似度。
# result 是一次检索后的结果包，里面有最高分、命中的子片段、完整章节和 context。
# 这题成功时，result["parents"] 大致会是：[{"title": "现制饮品与订单修改", ...}]。
# result["context"] 则会是这一整章的文字，后面可以直接交给 AI 回答。
result = retrieve_parent_context(
    # question：用户问题，BGE 会把它变成查询向量。
    question,
    # index_data：刚刚读到的知识库资料和向量。
    index_data,
    # embedding_model：负责把 question 变成向量的 BGE 模型。
    embedding_model,
    # min_relevance_score：低于门槛的片段不能进入本轮资料。
    min_relevance_score=MIN_RELEVANCE_SCORE,
    # metadata_filters：先要求“商品类型必须是现制饮品”，再做相似度比较。
    metadata_filters=metadata_filters,
)

# 下面只是把本轮过程打印出来，方便核对程序到底做了什么。
print("BGE 模型来源：", model_source)
print("\n用户问题：", question)
print("订单已知条件：", metadata_filters)

# None 表示连“符合元数据条件的候选资料”都没有，所以没有最高相似度可显示。
if result["best_score"] is None:
    print("没有任何资料符合这个元数据条件。")
else:
    # :.4f 表示把小数显示为四位，便于比较不同问题的分数。
    print(f"最高子片段相似度：{result['best_score']:.4f}")

# result["parents"] 是本轮最终找回的完整章节列表。
# not 表示“列表是空的”；空列表说明没有资料通过相似度门槛。
# 成功时它像 [父章节1]；失败时它就是 []，也就是一个空列表。
if not result["parents"]:
    print("没有通过阈值的资料，本次应该拒答。")
else:
    print("\n实际找回的章节：")

    # for 会把列表里的章节一个一个取出来，暂时放进 parent 变量。
    for parent in result["parents"]:
        # parent["title"] 取出这章的标题，例如“现制饮品与订单修改”。
        print("-", parent["title"])

    print("\n找回的完整资料：")
    # context 是把本轮找回的完整章节拼成的一段文字。
    print(result["context"])
