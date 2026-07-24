# powershell提前设置环境变量值为密钥 $env:DEEPSEEK_API_KEY = "你的真实 Key"

import os
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

messages = [
    ("system", "你是一名耐心的 Python 老师，请用简单中文回答问题。")
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

    messages.append(("human", question))

    response = model.invoke(messages)

    messages.append(response)

    print("AI：", response.content)