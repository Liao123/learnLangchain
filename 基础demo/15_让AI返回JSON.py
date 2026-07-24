# json：Python 自带的 JSON 处理模块。
# json.loads() 可以把 AI 返回的 JSON 文字转换成 Python 数据。
import json

# os：Python 自带的操作系统模块。
# 这里用来读取环境变量中的 API Key。
import os

# ChatOpenAI：LangChain 中连接聊天模型的类。
from langchain_openai import ChatOpenAI

# SystemMessage：给 AI 的规则。
# HumanMessage：用户输入的自然语言。
from langchain.messages import SystemMessage, HumanMessage


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# bind()：基于原来的模型创建一个“带固定设置”的模型。
#
# response_format={"type": "json_object"}：
# 要求 DeepSeek 使用 JSON 模式返回结果。
# JSON 是一种固定格式的数据，例如：
# {"姓名": "小王", "地点": "上海"}
json_model = model.bind(
    response_format={"type": "json_object"}
)


# DeepSeek 的 JSON 模式要求提示词中明确出现 JSON，
# 并且要说明希望得到的字段。
system_message = SystemMessage(
    content="""
你是一名信息整理助手。

请从用户提供的句子中提取人物、时间、地点和事情。
必须只返回一个合法的 JSON 对象，不能添加解释文字。

JSON 格式如下：
{
  "人物": "",
  "时间": "",
  "地点": "",
  "事情": "",
  "天气"：""
}
"""
)


# 这是一句普通自然语言，不需要按固定命令输入。
question = "小王准备在周五下午三点去上海参加 Python 培训。"


# invoke()：把规则和自然语言问题发送给模型。  这三行的作用是：给同一个模型预先打开“只返回 JSON”的模式。
# model      = 普通模式的 AI
# json_model = 开启 JSON 输出模式的同一个 AI
response = json_model.invoke([
    system_message,
    HumanMessage(content=question),
])


# 先显示 AI 原始返回的 JSON 文字。
print("AI 返回的 JSON：")
print(response.content)


# json.loads()：把 JSON 文字转换成 Python 字典。
# 转换后，Python 就可以按照字段名称直接拿到数据。
data = json.loads(response.content)


# data["字段名"]：从字典中读取指定字段的值。
print("\nPython 读取后的结果：")
print("人物：", data["人物"])
print("时间：", data["时间"])
print("地点：", data["地点"])
print("事情：", data["事情"])
