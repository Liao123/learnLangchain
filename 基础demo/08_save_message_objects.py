# 导入 Python 自带的 JSON 模块。
import json

# 导入 LangChain 的消息类型。
from langchain.messages import SystemMessage, HumanMessage, AIMessage


# 模拟程序运行中的 messages 列表。
messages = [
    SystemMessage(
        content="你是一名耐心的 Python 老师。"
    ),
    HumanMessage(
        content="什么是变量？"
    ),
    AIMessage(
        content="变量是用来保存数据的名字。"
    )
]


# 创建一个空列表。
# 这个列表只保存可以写入 JSON 的普通字典。
history_to_save = []


# 依次处理每个 LangChain 消息对象。
for message in messages:

    # SystemMessage 是程序规则，
    # 每次启动时重新创建，不需要保存。
    if message.type == "system":
        continue

    # append()：把一个新字典添加到列表末尾。
    #
    # message.type：取得消息角色，例如 human 或 ai。
    # message.content：取得消息正文。
    history_to_save.append(
        {
            "role": message.type,
            "content": message.content
        }
    )


# 以写入模式打开 JSON 文件。
with open(
    "chat_history_from_messages.json",
    "w",
    encoding="utf-8"
) as file:

    # json.dump()：
    # 把 Python 列表写入 JSON 文件。
    json.dump(
        history_to_save,
        file,
        ensure_ascii=False,
        indent=2
    )


print("LangChain 消息已经保存到 JSON 文件")