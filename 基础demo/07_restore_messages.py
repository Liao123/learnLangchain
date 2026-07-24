# json：Python 自带的 JSON 处理模块。
import json

# 导入 LangChain 的三种消息类型。
from langchain.messages import SystemMessage, HumanMessage, AIMessage


# 读取之前保存的 JSON 文件。
with open("chat_history.json", "r", encoding="utf-8") as file:

    # json.load()：
    # 读取 JSON 文件并转换成 Python 数据。
    saved_history = json.load(file)


# 创建模型真正需要的 messages 列表。
#
# SystemMessage 不需要保存到 JSON，
# 每次启动程序时重新创建即可。
messages = [
    SystemMessage(
        content="你是一名耐心的 Python 老师，请用简单中文回答问题。"
    )
]


# for：依次处理 JSON 中的每条历史消息。
for record in saved_history:

    # 从当前字典中取出角色和内容。
    role = record["role"]
    content = record["content"]

    # 如果角色是 human，
    # 就创建一个 HumanMessage 对象。
    if role == "human":

        # append()：
        # 把新消息添加到 messages 列表末尾。
        messages.append(
            HumanMessage(content=content)
        )

    # elif 表示“否则，如果……”。
    # 如果角色是 ai，就创建 AIMessage 对象。
    elif role == "ai":
        messages.append(
            AIMessage(content=content)
        )


# 查看转换后的所有消息。
for message in messages:

    # type()：取得对象的类型。
    # __name__：取得类型名称。
    print("消息类型：", type(message).__name__)

    # message.type：消息角色。
    print("消息角色：", message.type)

    # message.content：消息正文。
    print("消息内容：", message.content)

    print("--------------------")