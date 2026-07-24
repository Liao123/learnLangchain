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
# 这个函数专门创建一段新对话开始时需要的消息列表。
def create_initial_messages():

    # return：把新建的列表交还给调用函数的地方。
    # SystemMessage 是 AI 的固定规则，每次新对话都会重新创建。
    return [
        SystemMessage(
            content="你是一名耐心的 Python 老师，请用简单中文回答问题。"
        )
    ]


# def：定义“读取历史消息”的函数。
def load_messages():
    messages = create_initial_messages()

    # os.path.exists()：检查历史文件是否存在。
    if not os.path.exists(HISTORY_FILE):
        print("暂时没有历史记录，将开始一段新对话。")
        return messages

    # with open()：以只读模式打开 JSON 文件。
    # "r" 表示读取，encoding="utf-8" 用于避免中文乱码。
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

    # len()：计算列表中有多少条历史消息。
    print("已加载历史消息数量：", len(saved_history))
    return messages


# def：定义“保存历史消息”的函数。
# messages 是参数，调用函数时会把完整消息列表传进来。
def save_messages(messages):
    history_to_save = []

    # 逐条处理 LangChain 消息对象。
    for message in messages:

        # SystemMessage 是固定规则，不保存到历史文件。
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


# def：定义“显示历史消息”的函数。
# 这个函数只打印消息，不会调用模型，也不会修改历史文件。
def show_history(messages):

    # history_count 用来记录已经显示了多少条真实对话。
    history_count = 0

    # 逐条检查完整消息列表。
    for message in messages:

        # 不显示 SystemMessage，因为它是程序内部规则，不是对话内容。
        if message.type == "system":
            continue

        # += 1：在原来的数字上加 1。
        # 每显示一条对话，序号增加一次。
        history_count += 1

        print("第", history_count, "条记录")

        # 根据消息角色，显示不同的说话人名称。
        if message.type == "human":
            print("你：", message.content)

        elif message.type == "ai":
            print("AI：", message.content)

        print("--------------------")

    # 如果一条真实对话也没有，给出提示。
    if history_count == 0:
        print("当前没有可查看的对话历史。")


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",

    # os.environ[]：读取环境变量中的 API Key。
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# 调用 load_messages()，取得完整历史消息。
messages = load_messages()


# while True：持续进行对话。
while True:
    question = input("你：").strip()

    # lower()：把英文转换为小写，方便识别命令。
    command = question.lower()

    # 输入“退出”、exit 或 quit 时，结束程序。
    if command in {"退出", "exit", "quit"}:
        print("对话结束。")
        break

    # 输入“查看历史”或 history 时，只显示本地历史。
    if command in {"查看历史", "history"}:
        show_history(messages)

        # continue：直接回到 while True 的开头，等待下一次输入。
        continue

    # 输入“清空历史”或 clear 时，开始一段新对话。
    if command in {"清空历史", "clear"}:
        messages = create_initial_messages()

        # 保存后，chat_history.json 会变成空列表 []。
        save_messages(messages)

        print("历史记录已清空。现在可以开始一段新对话。")
        continue

    # 没有输入内容时，直接等待下一次输入。
    if not question:
        continue

    # 把用户问题加入消息列表。
    messages.append(
        HumanMessage(content=question)
    )

    try:
        # model.invoke()：把完整历史发送给模型，取得 AI 回答。
        # 返回值 response 是 AIMessage 对象。
        response = model.invoke(messages)

    except Exception as error:
        # pop()：删除刚加入、但没有成功回答的用户问题。
        messages.pop()

        print("调用模型失败：", error)
        continue

    # 把 AI 回答加入消息列表。
    messages.append(response)

    # response.content：取得 AI 回答的正文。
    print("AI：", response.content)

    # 调用保存函数，把当前完整历史写入 JSON 文件。
    save_messages(messages)

    print("本轮对话已保存。")
