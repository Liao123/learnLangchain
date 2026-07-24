"""第 39 课：找回完整章节后，只挑出本轮最相关的句子。"""

# sys：Python 用它临时增加“去哪里找其他 Python 文件”的位置。
import sys

# Path：用来处理文件夹路径。
from pathlib import Path

# util.semantic_search()：BGE 已经把句子变成向量后，用它按相似度找最相关的句子。
from sentence_transformers import util


# __file__ 是当前 demo.py 的路径；parents[2] 往上走两层，得到 RAGDemo 文件夹。
RAG_ROOT = Path(__file__).resolve().parents[2]

# rag_core.py 在 RAGDemo/app/ 中。放进搜索路径后，下面才能 import 已经学过的检索工具。
sys.path.insert(0, str(RAG_ROOT / "app"))

# 这四项都是前面课程学过的内容。
# 本课新出现的“拆句、句子筛选、组装压缩资料”会直接写在这个 demo.py 里。
from rag_core import (
    QUERY_INSTRUCTION,
    load_embedding_model,
    load_parent_child_index,
    retrieve_parent_context,
)


# 用户明确问“拆封后能不能退款”。
question = "咖啡豆已经拆封了，还可以退款吗？"

# 第一次检索从整个知识库中找 3 个子片段，用它们找回对应的完整父章节。
parent_top_k = 3

# 第二次检索只在完整父章节内部挑 2 句。
# 这里不是越小越好：若只保留 1 句，可能会删掉例外条件。
sentence_top_k = 2

# 读取全部父章节、子片段和它们已经算好的向量。
index_data = load_parent_child_index()

print("正在加载 BGE 向量模型...")
# embedding_model 是 BGE 模型；model_source 是模型来自本地路径还是模型仓库名称。
embedding_model, model_source = load_embedding_model(index_data["embedding_model"])


# ==================== 第一步：从整个知识库找完整章节 ====================

# result 是父子检索的结果包。
# result["parents"] 是完整父章节列表；默认题成功时第一个是“退款办理规则”。
result = retrieve_parent_context(
    question,
    index_data,
    embedding_model,
    top_k=parent_top_k,
)

# 没有父章节时，后面没有资料可压缩。本例不设阈值，目的是专门观察压缩过程。
if not result["parents"]:
    raise RuntimeError("没有找回完整章节，无法进行上下文压缩。")

# [0] 表示取列表中的第一章，也就是本轮相似度最高的父章节。
parent = result["parents"][0]
full_parent_content = parent["content"]


# ==================== 第二步：把完整章节拆成句子 ====================

# replace("\n", "") 去掉 Markdown 段落换行，让一句话不会在中间被断开。
# split("。") 按句号切开，返回一个列表。最后通常会多出一个空字符串，后面会跳过它。
raw_sentence_parts = full_parent_content.replace("\n", "").split("。")

sentences = []
for sentence_part in raw_sentence_parts:
    # strip() 去掉句子开头或结尾的空格。
    clean_sentence = sentence_part.strip()

    # if clean_sentence 的意思是“不是空字符串才继续”。
    # 加回“。”，让后面交给 AI 的文字仍是自然完整的句子。
    if clean_sentence:
        sentences.append(clean_sentence + "。")

# 这题的 sentences 大致是：
# [
#   "顾客购买咖啡豆后，如商品仍保持原包装且没有拆封，可以在购买日期后的七天内申请退款。",
#   "申请时需要提供订单号、付款记录或小票，以便客服核对购买时间和商品信息。",
#   "超过七天的咖啡豆，即使没有拆封，也不再支持无理由退款。",
#   "如果咖啡豆已经拆封、受潮、明显损坏……门店不能办理退款。",
#   "顾客如认为商品本身存在质量问题……",
#   ...
# ]


# ==================== 第三步：只在这章内部挑关键句 ====================

# BGE 把“用户问题”变成一个查询向量。
# 加 QUERY_INSTRUCTION 是为了和前面知识库检索时保持同一种 BGE 查询写法。
question_embedding = embedding_model.encode(
    [QUERY_INSTRUCTION + question],
    normalize_embeddings=True,
)

# BGE 再把这一章的每一句话分别变成向量。
# sentence_embeddings 的行数和 sentences 数量一样：第 0 行对应 sentences[0]，第 1 行对应 sentences[1]。
sentence_embeddings = embedding_model.encode(
    sentences,
    normalize_embeddings=True,
)

# 现在只比较“一个问题向量”和“这一章的句子向量”，不再比较全知识库。
# corpus_id 是句子在 sentences 列表中的位置，例如 3 就表示第 4 句话。
sentence_search_results = util.semantic_search(
    question_embedding,
    sentence_embeddings,
    top_k=min(sentence_top_k, len(sentences)),
)[0]


# ==================== 第四步：恢复原文顺序，组成压缩资料 ====================

# set() 是“不重复名单”。这里记录 BGE 选中了哪几句话的位置。
# 例如默认题大致会是 {0, 3}，表示保留第 1 句和第 4 句。
selected_sentence_indices = set()
for sentence_match in sentence_search_results:
    selected_sentence_indices.add(sentence_match["corpus_id"])

# BGE 返回的是“相关性从高到低”的顺序；但资料交给 AI 时，原文顺序通常更好读。
# 所以从第 0 句一路走到最后一句，只把入选位置的句子加回来。
compressed_sentences = []
for sentence_index in range(len(sentences)):
    if sentence_index in selected_sentence_indices:
        compressed_sentences.append(sentences[sentence_index])

# join("\n") 用换行把两句合成一段；标题也保留，让 AI 知道资料来自哪一章。
compressed_context = f"【{parent['title']}】\n" + "\n".join(compressed_sentences)


# ==================== 第五步：展示真正准备提交给 AI 的内容 ====================

# 这里只用字符串展示消息，不调用 DeepSeek。
# 以后接入 ChatOpenAI 时，这段文字会放进 SystemMessage(content=system_message_content)。
system_message_content = f"""
你是星光咖啡店客服。
只能根据 <压缩资料> 中的资料回答，不能补充资料中没有的信息。

<压缩资料>
{compressed_context}
</压缩资料>
""".strip()

print("\nBGE 模型来源：", model_source)
print("\n用户问题：", question)

# len() 计算字符串中的字符数量。它让你看到压缩前后资料长度的变化。
print(f"完整章节标题：{parent['title']}")
print(f"完整章节字符数：{len(full_parent_content)}")
print("\n完整父章节：")
print(full_parent_content)

print("\n句子级相似度（BGE 选中的句子）：")
for rank, sentence_match in enumerate(sentence_search_results, start=1):
    sentence_index = sentence_match["corpus_id"]
    print(
        f"{rank}. 第 {sentence_index + 1} 句，"
        f"相似度：{sentence_match['score']:.4f}"
    )
    print("   ", sentences[sentence_index])

print(f"\n压缩资料字符数：{len(compressed_context)}")
print("压缩后的资料：")
print(compressed_context)

print("\n即将提交给 AI 的消息顺序：")
print("\n【SystemMessage】")
print(system_message_content)
print("\n【HumanMessage】")
print(question)


# 本课重点：
# 1. 完整父章节仍是知识来源，压缩资料只是本轮临时版本。
# 2. 先用 BGE 在全库找章节，再用 BGE 在章节内部挑句子。
# 3. 压缩后必须用测试题检查例外条件有没有被误删。
