# json：Python 自带的 JSON 处理模块。
# 用来把 AI 返回的 JSON 文字转换成 Python 数据。
import json

# os：用来读取环境变量中的 API Key。
import os

from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# bind()：创建一个固定使用 JSON 输出模式的模型对象。
json_model = model.bind(
    response_format={"type": "json_object"}
)


# 这次提示词除了规则，还给 AI 一条完整示例。
#
# 示例输入：人类说的一句话。
# 示例 JSON 输出：我们希望 AI 返回的数据结构。
#
# AI 会模仿这个例子的结构，处理下面真正的问题。
system_message = SystemMessage(
    content="""
你是一名信息整理助手。
请从用户句子中提取人物、时间、地点和事情。
必须只返回一个合法的 JSON 对象，不能添加解释文字。

示例输入：
李老师将在下周一上午十点到北京参加人工智能会议。

示例 JSON 输出：
{
  "人物": "李老师",
  "时间": "下周一上午十点",
  "地点": "北京",
  "事情": "参加人工智能会议"
}
"""
)


# 这是 AI 从未见过的新句子。
# 它需要参考上面的示例，自行整理出 JSON。
question = "陈阿姨计划在本周六下午两点去杭州学习摄影。"


# invoke()：把提示词和新问题发送给模型。
response = json_model.invoke([
    system_message,
    HumanMessage(content=question),
])


print("用户输入：", question)
print("\nAI 返回的 JSON：")
print(response.content)


# json.loads()：把 AI 返回的 JSON 文字转换成 Python 字典。
data = json.loads(response.content)

print("\nPython 读取后的结果：")
print("人物：", data["人物"])
print("时间：", data["时间"])
print("地点：", data["地点"])
print("事情：", data["事情"])
