# Path：定位与当前 Python 文件同目录的 Markdown 示例文件。
from pathlib import Path

# RecursiveCharacterTextSplitter：LangChain 提供的长文档切块工具。
# 它会优先在较自然的位置（段落、换行、句号等）切分；
# 如果仍然太长，才继续向更小的分隔符尝试。
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 找到与本程序同一个文件夹中的长文档示例。
source_file = Path(__file__).with_name("长文档示例.md")

# read_text()：读取 Markdown 文件的全部文字。
# encoding="utf-8"：保证中文正常读取。
source_text = source_file.read_text(encoding="utf-8")


# 创建切块器。
# chunk_size=120：每个片段目标长度最多约 120 个字符。
# 本课故意设得较小，方便在终端清楚观察切块效果；真实项目通常会更大。
# chunk_overlap=30：相邻片段目标重叠约 30 个字符，减少上下文被切断的风险。
# length_function=len：用 Python 的 len() 计算每段文字的字符数量。
# is_separator_regex=False：下面的分隔符按普通文字理解，不当作正则表达式。
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=120,
    chunk_overlap=30,
    length_function=len,
    is_separator_regex=False,
    # separators：从上到下是切分优先级。
    # 优先保留段落和换行；不够时再按中文句号、逗号等位置尝试切分。
    separators=[
        "\n\n",
        "\n",
        "。",
        "！",
        "？",
        "；",
        "，",
        " ",
        "",
    ],
)


# split_text()：把一整段长文字切成多个字符串片段。
chunks = text_splitter.split_text(source_text)


print("原始文件：", source_file.name)
print("原文字符数：", len(source_text))
print("切分后的片段数：", len(chunks))


# enumerate(chunks, start=1)：依次取出每个片段，并从 1 开始编号。
for chunk_number, chunk in enumerate(chunks, start=1):
    print("\n" + "=" * 50)
    print(f"片段 {chunk_number}（{len(chunk)} 个字符）：")
    print(chunk)


# 观察重点：
# 1. 切块器会优先尝试在段落、换行和中文标点处切分。
# 2. chunk_overlap 是“目标重叠量”，为了保持自然句子边界，实际重叠字符数可能略有不同。
# 3. 下一课会把这种切块方式接入“构建知识库索引”的流程。
