from langchain.messages import SystemMessage, HumanMessage, AIMessage

messages = [
    SystemMessage(content="你是一名耐心的 Python 老师"),
    HumanMessage(content="什么是变量？"),
    AIMessage(content="变量是用来保存数据的名字。"),
]

for message in messages:
    print(type(message).__name__, message.type, message.content)