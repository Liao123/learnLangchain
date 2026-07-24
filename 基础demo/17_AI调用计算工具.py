# os：Python 自带的操作系统模块。
# 用来读取环境变量中的 API Key。
import os

# ChatOpenAI：LangChain 中连接聊天模型的类。
from langchain_openai import ChatOpenAI

# tool：把一个普通 Python 函数变成“可供 AI 调用的工具”。
from langchain.tools import tool

# SystemMessage：给 AI 的规则。
# HumanMessage：用户的自然语言问题。
# ToolMessage：把 Python 工具执行结果交还给 AI。
from langchain.messages import SystemMessage, HumanMessage, ToolMessage


# @tool：一个装饰器。
# 它会读取下面函数的名称、参数和说明，
# 并把这些信息告诉 AI：这里有一个可以计算总价的工具。
@tool
def calculate_total_price(unit_price: float, quantity: int) -> str:
    """根据商品单价和数量，计算总价。单价单位是元。"""

    # float：允许单价是小数，例如 12.5。
    # int：数量必须是整数，例如 3。
    total = unit_price * quantity

    # return：把计算结果交还给调用这个工具的地方。
    return f"{total:.2f} 元"


# 创建模型对象。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# bind_tools()：把可用工具清单告诉 AI。
#
# [calculate_total_price] 是一个列表，里面目前只有一个工具。
# 之后 AI 可以根据用户的问题，决定是否请求调用它。
tool_model = model.bind_tools([
    calculate_total_price,
])


# 这条规则告诉 AI：遇到总价计算时，不要自己心算，
# 而要请求 Python 调用 calculate_total_price 工具。
system_message = SystemMessage(
    content="""
你是一名购物助手。
当用户询问商品总价时，必须使用 calculate_total_price 工具。
收到工具结果后，用简短中文回答用户。
"""
)


# 用户正常说话，不需要使用任何固定命令。
question = "我买了 3 杯咖啡，每杯 12.5 元，一共多少钱？"


# messages 保存本次工具调用过程中的所有消息。
messages = [
    system_message,
    HumanMessage(content=question),
]


# 第一次调用模型。
# 此时 AI 不应该直接回答总价，
# 而应该返回“请调用哪个工具、传入哪些参数”。
first_response = tool_model.invoke(messages)


# tool_calls：AI 请求调用的工具列表。
if not first_response.tool_calls:
    print("AI 没有请求调用工具，请重新运行后再观察。")

else:
    # 这次问题只需要一次计算，所以取列表中的第一条工具请求。
    tool_call = first_response.tool_calls[0]

    print("用户问题：", question)
    print("\nAI 选择的工具：", tool_call["name"])
    print("AI 提取的参数：", tool_call["args"])

    # invoke()：真正执行 Python 工具。
    # tool_call["args"] 的内容例如：
    # {"unit_price": 12.5, "quantity": 3}
    tool_result = calculate_total_price.invoke(tool_call["args"])

    print("Python 工具计算结果：", tool_result)

    # 把 AI 的工具请求加入消息历史。
    messages.append(first_response)

    # ToolMessage：把 Python 的计算结果交还给 AI。
    # tool_call_id 用来说明：这个结果对应哪一次工具请求。
    messages.append(
        ToolMessage(
            content=tool_result,
            tool_call_id=tool_call["id"],
        )
    )

    # 第二次调用模型。
    # 现在 AI 已经拿到可靠的计算结果，可以组织自然语言回答。
    final_response = tool_model.invoke(messages)

    print("\nAI 给用户的最终回答：")
    print(final_response.content)
