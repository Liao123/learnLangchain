# json：Python 自带模块，用来把 JSON 文字转换为 Python 字典。
import json

# os：Python 自带模块，用来读取环境变量中的 API Key。
import os

# ChatOpenAI：LangChain 中连接聊天模型的类。
from langchain_openai import ChatOpenAI

# tool：把普通 Python 函数包装成 AI 可以请求调用的工具。
from langchain.tools import tool

# 三种消息：规则、用户问题、工具执行结果。
from langchain.messages import SystemMessage, HumanMessage, ToolMessage


# @tool：告诉 LangChain 和 AI，下面的函数是一个可调用工具。
@tool
def calculate_total_price(unit_price: float, quantity: int) -> str:
    """根据商品单价和数量，计算商品总价。单价单位是元。"""

    total = unit_price * quantity
    return f"{total:.2f} 元"


# 创建基础模型。下面会从它派生出两种不同配置。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# tool_model：第一步使用。
# bind_tools() 把工具说明交给 AI，让它能提出“调用计算工具”的请求。
tool_model = model.bind_tools([calculate_total_price])


# json_model：最后一步使用。
# bind() 只是在基础模型上增加“必须返回 JSON 对象”的要求，不会调用 AI。
json_model = model.bind(
    response_format={"type": "json_object"}
)


# 同一条系统规则同时说明两件事：
# 1. 什么时候必须调用工具；2. 最终结果应该是什么 JSON 格式。
system_message = SystemMessage(
    content="""
你是购物助手。
当用户询问商品总价时，必须调用 calculate_total_price 工具，不能自己心算。

当收到工具结果后，最终只返回一个 JSON 对象，不能使用 Markdown。
JSON 必须包含以下字段：
{
  "商品": "商品名称",
  "数量": 数字,
  "总价": 数字,
  "货币": "元"
}
总价必须以工具返回的结果为准。
"""
)


question = "我买了 3 杯咖啡，每杯 12.5 元，一共多少钱？"

# messages 是两种模式共同使用的上下文。
messages = [
    system_message,
    HumanMessage(content=question),
]


# 第一次调用：tool_model 理解用户问题，并请求调用计算工具。
first_response = tool_model.invoke(messages)


if not first_response.tool_calls:
    print("AI 没有请求调用工具，请重新运行后再观察。")

else:
    # [0] 表示取第一条工具请求。本例只需要一次计算。
    tool_call = first_response.tool_calls[0]

    print("用户问题：", question)
    print("AI 选择的工具：", tool_call["name"])
    print("AI 提取的参数：", tool_call["args"])

    # invoke()：Python 真正执行计算函数。
    tool_result = calculate_total_price.invoke(tool_call["args"])
    print("Python 工具计算结果：", tool_result)

    # 将 AI 的工具请求和 Python 的工具回执加入同一份历史。
    messages.append(first_response)
    messages.append(
        ToolMessage(
            content=tool_result,
            tool_call_id=tool_call["id"],
        )
    )

    # 第二次调用：换成 json_model，但仍传入同一份 messages。
    # 因此它看得到用户问题、AI 的工具请求和 Python 的真实计算结果。
    # 这次它不负责选择工具，而是把结果整理成 JSON。
    final_response = json_model.invoke(messages)

    print("\njson_model 返回的 JSON：")
    print(final_response.content)

    # json.loads()：把 JSON 文字转换为 Python 字典，供后续程序读取。
    data = json.loads(final_response.content)
    print("\n程序读取到的总价：", data["总价"], data["货币"])
