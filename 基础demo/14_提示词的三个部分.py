# os：Python 自带的操作系统模块。
# 这里用来读取环境变量中的 API Key。
import os

# ChatOpenAI：LangChain 中连接聊天模型的类。
from langchain_openai import ChatOpenAI

# SystemMessage：给 AI 的规则和身份设定。
# HumanMessage：用户真正提出的问题。
from langchain.messages import SystemMessage, HumanMessage


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# 三个双引号 """ 可以写多行文字。
# 这段 SystemMessage 包含一个好提示词常用的三个部分：
#
# 1. 身份：AI 要扮演谁。
# 2. 对象：AI 要对谁说话。
# 3. 输出要求：答案应该长什么样。
system_message = SystemMessage(
    content="""
你是一名耐心的 Python 老师。

你的回答对象是完全不懂编程的成年人。

请按以下格式回答：
1. 先用一句话给出结论。
2. 再用一个生活中的比喻解释。
3. 最后给一个不超过三行的 Python 例子。
4. 不要使用没有解释的专业术语。
"""
)


# 这是真正由用户提出的问题。
question = "什么是 Python 变量？"


# model.invoke()：把规则和问题发送给模型，取得回答。
# 消息顺序是：先发送 SystemMessage 规则，再发送 HumanMessage 问题。
response = model.invoke([
    system_message,
    HumanMessage(content=question),
])


print("问题：", question)
print("\nAI 的回答：")

# response.content：取得 AIMessage 中真正的回答文字。
print(response.content)
