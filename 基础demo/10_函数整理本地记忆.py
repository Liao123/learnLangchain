# json：Python 自带的 JSON 处理模块。
# 用来读取和保存对话历史。
import json

# os：Python 自带的操作系统模块。
# 用来读取环境变量和检查文件是否存在。
import os

# 导入 LangChain 的消息对象。
from langchain.messages import SystemMessage, HumanMessage, AIMessage

# 导入模型连接器。
from langchain_openai import ChatOpenAI


# 对话历史保存的文件名。
HISTORY_FILE = "chat_history.json"


# def：定义一个函数。
#
# load_messages 是函数名。
# 函数中的代码暂时不会运行；
# 只有写了 load_messages() 后，它才会运行。
def load_messages():

    # 每次启动时，先创建固定的系统消息。
    messages = [
        SystemMessage(
            content="你是一名耐心的 Python 老师，请用简单中文回答问题。"
        )
    ]

    # os.path.exists()：检查历史文件是否存在。
    if not os.path.exists(HISTORY_FILE):
        print("暂时没有历史记录，将开始一段新对话。")

        # return：把结果交还给调用函数的地方。
        # 这里返回只有 SystemMessage 的 messages 列表。
        return messages

    # with open()：以只读模式打开 JSON 文件。
    # "r" 表示读取。
    with open(HISTORY_FILE, "r", encoding="utf-8") as file:

        # json.load()：把 JSON 文件转换成 Python 列表。
        saved_history = json.load(file)

    # 把 JSON 中的普通字典转换成 LangChain 消息对象。
    for record in saved_history:
        role = record["role"]
        content = record["content"]

        if role == "human":
            messages.append(
                HumanMessage(content=content)
            )

        elif role == "ai":
            messages.append(
                AIMessage(content=content)
            )

    # len()：计算历史消息数量。
    print("已加载历史消息数量：", len(saved_history))

    # 把完整 messages 列表返回。
    return messages


# def：定义第二个函数。
#
# messages 写在括号中，叫“参数”。
# 调用此函数时，要把需要保存的消息列表传进来。
def save_messages(messages):

    # 创建一个空列表，准备保存 JSON 格式的数据。
    history_to_save = []

    # 逐条处理 LangChain 消息对象。
    for message in messages:

        # SystemMessage 是每次启动时重新创建的规则，不保存。
        if message.type == "system":
            continue

        # append()：把普通字典添加到列表末尾。
        history_to_save.append(
            {
                "role": message.type,
                "content": message.content
            }
        )

    # "w" 表示写入模式。
    # 每次保存都会用最新历史覆盖旧文件。
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:

        # json.dump()：把 Python 列表保存到 JSON 文件。
        json.dump(
            history_to_save,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("本轮对话已保存。")


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",

    # os.environ[]：读取环境变量中的 API Key。
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# 调用 load_messages() 函数，取得完整历史消息。
messages = load_messages()


# while True：持续进行对话。
while True:
    question = input("你：").strip()

    # lower()：将英文转为小写。
    if question.lower() in {"退出", "exit", "quit"}:
        print("对话结束。")
        break

    if not question:
        continue

    # 把用户问题加入消息列表。
    messages.append(
        HumanMessage(content=question)
    )

    try:
        # invoke()：将完整历史发送给模型，取得 AI 回答。
        response = model.invoke(messages)

    except Exception as error:
        # pop()：删除刚加入、但没有成功回答的用户问题。
        messages.pop()

        print("调用模型失败：", error)
        continue

    # 把 AI 回答加入消息列表。
    messages.append(response)

    print("AI：", response.content)

    # 调用保存函数，把当前完整历史写入 JSON 文件。
    save_messages(messages)