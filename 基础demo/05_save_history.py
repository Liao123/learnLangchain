# 导入 Python 自带的 json 模块。
# json 模块负责把 Python 数据转换成 JSON 格式，
# 不需要使用 pip 安装。
import json


# 先模拟两条对话记录。
# 列表使用 []，里面可以保存多条数据。
# 每个 {} 表示一条消息。
chat_history = [
    {
        "role": "human",
        "content": "你好"
    },
    {
        "role": "ai",
        "content": "你好，请问有什么可以帮助你？"
    }
]


# open()：打开或创建文件。
#
# 第一个参数：
# "chat_history.json" 是文件名。
#
# 第二个参数：
# "w" 表示写入模式。
# 文件不存在时会创建，存在时会覆盖原内容。
#
# encoding="utf-8"：
# 使用 UTF-8 编码，避免中文乱码。
#
# with：
# 代码执行完后自动关闭文件。
with open("chat_history.json", "w", encoding="utf-8") as file:

    # json.dump()：把 Python 数据写入 JSON 文件。
    #
    # chat_history：要保存的数据。
    # file：要写入的文件。
    # ensure_ascii=False：直接保存中文，不转换成 \uXXXX。
    # indent=2：使用两个空格排版，让文件容易阅读。
    json.dump(
        chat_history,
        file,
        ensure_ascii=False,
        indent=2
    )


# print()：在终端输出提示文字。
print("对话记录已经保存到 chat_history.json")