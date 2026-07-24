"""第 39 课归档：找回完整章节后，只挑出本轮最相关的句子。"""

# json：读取父子知识库索引 JSON。
import json

# Path：定位 archive 文件夹中的索引文件。
from pathlib import Path

# numpy：把 JSON 中的向量列表还原为 NumPy 数组。
import numpy as np

# SentenceTransformer：加载 BGE，把问题和句子都变成向量。
# util.semantic_search()：按相似度找最相关的子片段或句子。
from sentence_transformers import SentenceTransformer, util


index_file = Path(__file__).with_name("父子知识库索引.json")
query_instruction = "为这个句子生成表示以用于检索相关文章："

# 用户的本轮问题。
question = "咖啡豆已经拆封了，还可以退款吗？"

# 第一次从全知识库找 3 个子片段；第二次只从完整章节内挑 2 句。
parent_top_k = 3
sentence_top_k = 2


# ==================== 程序启动：读取资料和已有向量 ====================

index_data = json.loads(index_file.read_text(encoding="utf-8"))
parents = index_data["parents"]
children = index_data["children"]
child_embeddings = np.array(index_data["child_embeddings"], dtype=np.float32)

# 做一个“parent_id -> 完整父章节”的查询表，之后能通过子片段找到完整章节。
parents_by_id = {}
for parent in parents:
    parents_by_id[parent["parent_id"]] = parent

print("正在加载 BGE 向量模型...")
# 先只读本机已经下载好的 Hugging Face 缓存，避免每次运行都等待网络检查。
# 如果本机从未下载过模型，local_files_only=True 会报 OSError，下面再联网下载一次。
try:
    embedding_model = SentenceTransformer(
        index_data["embedding_model"],
        local_files_only=True,
    )
    model_source = f"{index_data['embedding_model']}（本地缓存）"
except OSError:
    embedding_model = SentenceTransformer(index_data["embedding_model"])
    model_source = index_data["embedding_model"]


# ==================== 第一步：从整个知识库找完整章节 ====================

question_embedding = embedding_model.encode(
    [query_instruction + question],
    normalize_embeddings=True,
)

# 先和全部 child 向量比较。search_results 每项会有 corpus_id（child 的位置）和 score（相似度）。
search_results = util.semantic_search(
    question_embedding,
    child_embeddings,
    top_k=parent_top_k,
)[0]

# 父章节只能放一次。set() 用来记录已经加入的 parent_id。
seen_parent_ids = set()
retrieved_parents = []
for search_result in search_results:
    child = children[search_result["corpus_id"]]
    parent_id = child["parent_id"]

    if parent_id not in seen_parent_ids:
        seen_parent_ids.add(parent_id)
        retrieved_parents.append(parents_by_id[parent_id])

if not retrieved_parents:
    raise RuntimeError("没有找回完整章节，无法进行上下文压缩。")

# 第一章就是本轮最相关的完整父章节。
parent = retrieved_parents[0]
full_parent_content = parent["content"]


# ==================== 第二步：把完整章节拆成句子 ====================

raw_sentence_parts = full_parent_content.replace("\n", "").split("。")
sentences = []
for sentence_part in raw_sentence_parts:
    clean_sentence = sentence_part.strip()
    if clean_sentence:
        sentences.append(clean_sentence + "。")


# ==================== 第三步：只在这章内部挑关键句 ====================

# 每句话各自变成向量。这里 sentence_embeddings 有多少行，sentences 就有多少句。
sentence_embeddings = embedding_model.encode(
    sentences,
    normalize_embeddings=True,
)

# 只把同一个问题与本章句子比较，选出最相关的两句。
sentence_search_results = util.semantic_search(
    question_embedding,
    sentence_embeddings,
    top_k=min(sentence_top_k, len(sentences)),
)[0]


# ==================== 第四步：恢复原文顺序，组成压缩资料 ====================

selected_sentence_indices = set()
for sentence_match in sentence_search_results:
    selected_sentence_indices.add(sentence_match["corpus_id"])

# BGE 的顺序是“分数高在前”；这里改回“原文先后顺序”，让 AI 更容易阅读。
compressed_sentences = []
for sentence_index in range(len(sentences)):
    if sentence_index in selected_sentence_indices:
        compressed_sentences.append(sentences[sentence_index])

compressed_context = f"【{parent['title']}】\n" + "\n".join(compressed_sentences)


# ==================== 第五步：展示即将提交给 AI 的消息 ====================

system_message_content = f"""
你是星光咖啡店客服。
只能根据 <压缩资料> 中的资料回答，不能补充资料中没有的信息。

<压缩资料>
{compressed_context}
</压缩资料>
""".strip()

print("\n用户问题：", question)
print("BGE 模型来源：", model_source)
print(f"完整章节标题：{parent['title']}")
print(f"完整章节字符数：{len(full_parent_content)}")
print("\n完整父章节：")
print(full_parent_content)

print("\n句子级相似度（BGE 选中的句子）：")
for rank, sentence_match in enumerate(sentence_search_results, start=1):
    sentence_index = sentence_match["corpus_id"]
    print(f"{rank}. 第 {sentence_index + 1} 句，相似度：{sentence_match['score']:.4f}")
    print("   ", sentences[sentence_index])

print(f"\n压缩资料字符数：{len(compressed_context)}")
print("压缩后的资料：")
print(compressed_context)

print("\n即将提交给 AI 的消息顺序：")
print("\n【SystemMessage】")
print(system_message_content)
print("\n【HumanMessage】")
print(question)


# 本课重点：完整章节是原始资料；压缩资料只是本轮临时挑出的重点句。
# 压缩不能替代相似度阈值，也要测试它有没有误删例外条件。
