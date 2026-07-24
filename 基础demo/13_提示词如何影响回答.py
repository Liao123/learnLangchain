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

    # os.environ["DEEPSEEK_API_KEY"]：
    # 从 PowerShell 设置的环境变量中读取 Key。
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# 这是两次都要问 AI 的同一个问题。
# 这样我们能清楚看出：变化来自 SystemMessage，而不是问题本身。
question = "什么是 Python 变量？"


# 第一次调用：让 AI 面向小学生回答。
child_system_message = SystemMessage(
    content="你是一名小学信息技术老师。请用两句简单中文解释，不要使用专业术语。"
)

# model.invoke()：把消息发送给模型，并取得 AI 的回答。
# 列表中的顺序很重要：先给规则，再给问题。
child_response = model.invoke([
    child_system_message,
    HumanMessage(content=question),
])

print("给小学生的回答：")

# response.content：取得 AIMessage 中真正的回答文字。
print(child_response.content)


# 第二次调用：问题完全相同，但换成面向初学者程序员的规则。
developer_system_message = SystemMessage(
    content="你是一名资深 Python 工程师。请解释概念，并给出一个简短 Python 代码例子。"
)

developer_response = model.invoke([
    developer_system_message,
    HumanMessage(content=question),
])

print("\n给 Python 初学者的回答：")
print(developer_response.content)
