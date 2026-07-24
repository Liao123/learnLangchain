# json：Python 自带的 JSON 处理模块。
# 负责读取和保存对话历史。
import json

# os：Python 自带的操作系统模块。
# 这里用来读取环境变量和检查文件是否存在。
import os

# 导入 LangChain 的三种消息对象。
from langchain.messages import SystemMessage, HumanMessage, AIMessage

# 导入模型连接器。
from langchain_openai import ChatOpenAI


# 使用大写变量名表示固定配置。
# 这是要保存和读取的历史记录文件。
HISTORY_FILE = "chat_history.json"


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",

    # os.environ["名称"]：
    # 从系统环境变量中读取 API Key。
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# 创建消息列表。
# SystemMessage 每次启动程序时重新创建。
messages = [
    SystemMessage(
        content="你是一名耐心的 Python 老师，请用简单中文回答问题。"
    )
]


# os.path.exists()：
# 检查指定文件是否存在。
#
# 存在时返回 True，不存在时返回 False。
if os.path.exists(HISTORY_FILE):

    # 以只读模式打开历史记录文件。
    with open(HISTORY_FILE, "r", encoding="utf-8") as file:

        # json.load()：
        # 读取 JSON 文件并转换成 Python 列表。
        saved_history = json.load(file)

    # 把 JSON 字典转换成 LangChain 消息对象。
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

    # len()：计算列表中有多少条数据。
    print("已加载历史消息数量：", len(saved_history))

else:
    print("暂时没有历史记录，将开始一段新对话。")


# while True：持续进行对话。
while True:

    # input()：等待用户输入。
    #
    # strip()：
    # 删除输入内容开头和结尾的空格。
    question = input("你：").strip()

    # lower()：
    # 把英文转换成小写，方便判断 exit 和 quit。
    if question.lower() in {"退出", "exit", "quit"}:
        print("对话结束。")
        break

    # 如果用户没有输入内容，直接进入下一轮。
    if not question:
        continue

    # 把用户问题添加到消息列表。
    messages.append(
        HumanMessage(content=question)
    )

    try:
        # model.invoke()：
        # 把完整消息历史发送给模型，并取得回答。
        #
        # 返回值 response 是一个 AIMessage 对象。
        response = model.invoke(messages)

    except Exception as error:
        # pop()：
        # 删除列表中的最后一条消息。
        #
        # 当前最后一条就是没有得到回答的用户问题。
        messages.pop()

        print("调用模型失败：", error)
        continue

    # 把模型回答加入消息列表。
    messages.append(response)

    # response.content：
    # 取得 AIMessage 中的回答正文。
    print("AI：", response.content)

    # 创建准备写入 JSON 的普通列表。
    history_to_save = []

    # 把 LangChain 消息对象转换成普通字典。
    for message in messages:

        # SystemMessage 是固定规则，不保存。
        if message.type == "system":
            continue

        history_to_save.append(
            {
                "role": message.type,
                "content": message.content
            }
        )

    # 每次模型成功回答后，都重新保存完整历史。
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:

        # json.dump()：
        # 把 Python 列表写入 JSON 文件。
        json.dump(
            history_to_save,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("本轮对话已保存。")