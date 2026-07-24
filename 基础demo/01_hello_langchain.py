from langchain_openai import ChatOpenAI
import os
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
    # use_responses_api=True,
)


question = input("你想问什么：")
# response = model.invoke(question)
response = model.invoke([
    ("system", "你是一名耐心的 Python 老师，请用简单中文回答问题。"),
    ("human", question)
])

print("AI：", response.content)