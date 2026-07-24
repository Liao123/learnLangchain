# 导入 Python 自带的 json 模块。
import json


# open()：打开文件。
#
# "chat_history.json"：需要读取的文件名。
# "r"：read 的缩写，表示只读模式。
# encoding="utf-8"：按照 UTF-8 编码读取，避免中文乱码。
#
# with：代码执行完成后自动关闭文件。
with open("chat_history.json", "r", encoding="utf-8") as file:

    # json.load()：读取 JSON 文件，
    # 并把文件内容转换成 Python 数据。
    #
    # 返回的数据会保存到 chat_history 变量中。
    chat_history = json.load(file)


# type()：查看变量的数据类型。
# __name__：只取得类型名称。
print("读取后的数据类型：", type(chat_history).__name__)


# for：依次取出列表中的每条消息。
# message：当前取出的消息。
# chat_history：刚才从 JSON 文件读取的列表。
for message in chat_history:

    # message["role"]：取得消息的角色。
    # message["content"]：取得消息的内容。
    print("角色：", message["role"])
    print("内容：", message["content"])
    print("--------------------")