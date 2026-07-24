# powershell提前设置环境变量值为密钥 $env:DEEPSEEK_API_KEY = "你的真实 Key"
from langchain.messages import SystemMessage, HumanMessage
import os
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

# messages = [
#     ("system", "你是一名耐心的 Python 老师，请用简单中文回答问题。")
# ]
messages = [
    SystemMessage(
        content="你是一名耐心的 Python 老师，请用简单中文回答问题。"
    )
]

while True:
    question = input("你：").strip()
    # breakpoint()
    #命令行查看 p [(m[0], m[1]) if isinstance(m, tuple) else (m.type, m.content) for m in messages]
    if question.lower() in {"退出", "exit", "quit"}:
        print("对话结束。")
        break

    if not question:
        continue

    # messages.append(HumanMessage(content=question))
    # response = model.invoke(messages)
    # messages.append(response)
    # print("AI：", response.content)
    # messages.append(HumanMessage(content=question))

    messages.append(HumanMessage(content=question))

    try:
        response = model.invoke(messages)
    except Exception as error:
        # 删除刚加入但尚未得到回答的问题
        messages.pop()

        print("调用模型失败：", error)
        continue

    messages.append(response)

    print("AI：", response.content)
