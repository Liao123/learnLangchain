# os：Python 自带模块，用来读取环境变量中的 API Key。
import os

# ChatOpenAI：LangChain 中连接聊天模型的类。
from langchain_openai import ChatOpenAI

# tool：把普通 Python 函数包装成 AI 可以请求调用的工具。
from langchain.tools import tool

# 三种消息：规则、用户问题、工具执行结果。
from langchain.messages import SystemMessage, HumanMessage, ToolMessage


# @tool：让 AI 知道下面是一个可调用工具。
@tool
def calculate_total_price(unit_price: float, quantity: int) -> str:
    """根据商品单价和数量，计算商品总价。单价单位是元。"""

    total = unit_price * quantity
    return f"{total:.2f} 元"


# 这是第二个工具。真实项目里，这类信息通常来自数据库或公司系统；
# 本课先用固定内容，专门观察 AI 如何在多个工具中做选择。
@tool
def get_return_policy() -> str:
    """查询本店咖啡商品的退货政策。"""

    return "未拆封的咖啡豆可在购买后 7 天内凭订单退款；现制饮品不支持退款。"


# 创建基础模型对象。它本身还不知道有哪些工具可以使用。
model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)


# bind_tools()：把两个工具的名称、参数和说明发给 AI。
# 这一步不会运行任何工具，只是让 AI 知道“有哪些工具可选”。
tools = [calculate_total_price, get_return_policy]
tool_model = model.bind_tools(tools)


# 这张“工具名称 → 工具对象”的表，是本课的重点。
# AI 返回工具名称后，Python 用这张表找到真正要运行的工具。
# .name 是 LangChain 工具的名称，例如 "calculate_total_price"。
tools_by_name = {
    tool.name: tool
    for tool in tools
}


system_message = SystemMessage(
    content="""
你是咖啡店客服。
当用户询问商品总价时，必须调用 calculate_total_price 工具。
当用户询问退货政策时，必须调用 get_return_policy 工具。
收到工具结果后，用简短、自然的中文回答用户。
"""
)


# 先测试“计算价格”。
# 运行成功后，可以改成：question = "买的咖啡可以退吗？"
# 再运行一次，观察 AI 是否会选择 get_return_policy。
# question = "我买了 3 杯咖啡，每杯 12.5 元，一共多少钱？"
question = "买的咖啡可以退吗？"

messages = [
    system_message,
    HumanMessage(content=question),
]


# 第一次调用 AI：AI 只负责理解问题，并提出工具调用请求。
# 它不会在这里自动运行 Python 函数。
first_response = tool_model.invoke(messages)


if not first_response.tool_calls:
    print("AI 没有请求调用工具，请重新运行后再观察。")

else:
    # [0] 表示取第一条工具请求。
    # 本课的每个问题只需要一个工具，所以先处理第一条即可。
    tool_call = first_response.tool_calls[0]

    print("用户问题：", question)
    print("\nAI 选择的工具：", tool_call["name"])
    print("AI 提取的参数：", tool_call["args"])

    # dict.get(名称)：从“工具名称 → 工具对象”的表中取出工具。
    # 如果名称不存在，.get() 会返回 None，而不会让程序直接崩溃。
    selected_tool = tools_by_name.get(tool_call["name"])

    if selected_tool is None:
        print("AI 请求了未登记的工具，程序不会执行它。")

    else:
        # invoke()：真正执行 Python 工具。
        # 参数由 AI 从用户自然语言中提取，例如：
        # {"unit_price": 12.5, "quantity": 3}
        # 对于没有参数的 get_return_policy，AI 会传入空字典 {}。
        tool_result = selected_tool.invoke(tool_call["args"])

        print("Python 工具执行结果：", tool_result)

        # 把 AI 的工具请求放回消息中，保留完整上下文。
        messages.append(first_response)

        # ToolMessage：把 Python 工具的真实结果交还给 AI。
        # tool_call_id 表示这份结果对应 AI 刚才的哪一次请求。
        messages.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call["id"],
            )
        )

        # 第二次调用 AI：它已经拿到工具回执，负责组织自然语言回答。
        final_response = tool_model.invoke(messages)

        print("\nAI 给用户的最终回答：")
        print(final_response.content)



# 第一次 tool_model：
# 用户问题 → 判断要调用什么工具

# Python：
# 执行工具 → 得到 ToolMessage

# 第二次 tool_model：
# 看到 ToolMessage 中的结果 → 用白话文回复用户