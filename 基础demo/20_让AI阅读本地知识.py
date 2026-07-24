# os：Python 自带模块，用来读取环境变量中的 API Key。
import os

# ChatOpenAI：LangChain 中连接聊天模型的类。
from langchain_openai import ChatOpenAI

# SystemMessage：给 AI 的规则和资料。
# HumanMessage：用户用自然语言提出的问题。
from langchain.messages import SystemMessage, HumanMessage


# 这是本地 Markdown 知识文件的名称。
# 文件和本程序放在同一个文件夹里，所以只写文件名即可。
knowledge_file = "咖啡店知识库.md"

# open()：打开文件。
# "r" 表示读取（read），不会修改文件。
# encoding="utf-8"：让 Python 正确读取中文。
# with：文件读取结束后，Python 会自动关闭文件。
with open(knowledge_file, "r", encoding="utf-8") as file:
    # read()：一次读取 Markdown 文件中的全部文字。
    knowledge = file.read()


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# 把本地资料放进系统消息中。
# <知识库> 和 </知识库> 是人为加的边界，方便 AI 区分“规则”和“资料内容”。
system_message = SystemMessage(
    content=f"""
你是星光咖啡店客服。
只能依据下面的知识库回答问题，不要补充知识库中没有的信息。
如果知识库没有答案，请直接说：知识库中暂时没有这项信息。

<知识库>
{knowledge}
</知识库>
"""
)


# 可以把这句改成任何与知识库有关的问题，再重新运行程序。
question = "我买的咖啡豆还没拆封，五天前买的，可以退款吗？"


# 把“规则和知识库”以及“用户问题”一起交给 AI。
response = model.invoke([
    system_message,
    HumanMessage(content=question),
])

print("\n系统消息：", system_message)
print("已读取本地知识文件：", knowledge_file)
print("\n用户问题：", question)
print("\nAI 回答：")
print(response.content)


# 重要说明：这个 Demo 会把整份知识库都发送给 AI，适合资料很短的情况。
# 真正的 RAG 会先从大量资料中找出最相关的几段，再只把那些段落发给 AI。
