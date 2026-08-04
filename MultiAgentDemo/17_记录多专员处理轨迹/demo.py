"""多 Agent 第 17 课：保存一次请求经过哪些专员的处理轨迹。"""

import json
import os
from operator import add
from pathlib import Path
from typing import Annotated, Literal

from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, ValidationError
from typing_extensions import TypedDict


class RouteResult(BaseModel):
    # 模型输出示例：{"route": "refund"}
    route: Literal["order", "refund", "human"]


class SupportState(TypedDict, total=False):
    question: str
    route: str
    answer: str
    # add 的意思是“新轨迹接在旧轨迹后面”，而不是把旧轨迹覆盖掉。
    # 最后 trace 的值示例：[总调度那一条, 退款专员那一条]。
    trace: Annotated[list[dict[str, str]], add]


# 输出文件的最终位置类似：...\17_记录多专员处理轨迹\输出\trace.json
LESSON_DIR = Path(__file__).resolve().parent
TRACE_PATH = LESSON_DIR / "输出" / "trace.json"

api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise RuntimeError("请先设置 DEEPSEEK_API_KEY，再运行本课。")

model = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-v4-pro",
    api_key=api_key,
)
router_model = model.bind(response_format={"type": "json_object"})


def choose_route(question: str) -> str:
    # question 的值示例："我想退钱"
    # 正常返回值示例："refund"。
    response = router_model.invoke(
        [
            SystemMessage(
                content="""
你是客服总调度。
订单进度、配送、修改订单 -> order
退款、退货、退款到账 -> refund
无法判断或不属于客服范围 -> human
只能返回 JSON，例如：{"route": "order"}
"""
            ),
            HumanMessage(content=question),
        ]
    )

    try:
        return RouteResult.model_validate(json.loads(response.content)).route
    except (json.JSONDecodeError, ValidationError):
        # 模型格式异常时交给人工节点，不能猜测用户要什么。
        return "human"


def supervisor(state: SupportState) -> Command:
    route = choose_route(state["question"])
    next_node = {
        "order": "order_agent",
        "refund": "refund_agent",
        "human": "human_service",
    }[route]

    # 例如用户问“我想退钱”时，这一条记录的值会是：
    # {"node": "总调度", "input": "我想退钱", "decision": "交给退款专员"}
    trace_item = {
        "node": "总调度",
        "input": state["question"],
        "decision": f"选择 {route}，进入 {next_node}",
    }

    # Command 同时做两件事：更新 state，并跳到当前选择的专员节点。
    return Command(update={"route": route, "trace": [trace_item]}, goto=next_node)


def order_agent(state: SupportState) -> dict:
    answer = "订单专员：订单 A1001 正在配送中，预计今天送达。"
    return {
        "answer": answer,
        "trace": [
            {
                "node": "订单专员",
                "input": state["question"],
                "decision": "查询订单状态并生成答复",
            }
        ],
    }


def refund_agent(state: SupportState) -> dict:
    answer = "退款专员：退款申请提交后，通常会在 1 到 3 个工作日原路退回。"
    return {
        "answer": answer,
        "trace": [
            {
                "node": "退款专员",
                "input": state["question"],
                "decision": "查询退款规则并生成答复",
            }
        ],
    }


def human_service(state: SupportState) -> dict:
    answer = "人工客服：这个问题需要人工进一步处理。"
    return {
        "answer": answer,
        "trace": [
            {
                "node": "人工客服",
                "input": state["question"],
                "decision": "接收无法自动处理的问题",
            }
        ],
    }


workflow = StateGraph(SupportState)
workflow.add_node("supervisor", supervisor)
workflow.add_node("order_agent", order_agent)
workflow.add_node("refund_agent", refund_agent)
workflow.add_node("human_service", human_service)
workflow.add_edge(START, "supervisor")
workflow.add_edge("order_agent", END)
workflow.add_edge("refund_agent", END)
workflow.add_edge("human_service", END)
support_graph = workflow.compile()


question = input("请输入订单或退款问题：").strip()
if not question:
    raise ValueError("问题不能为空。")

# 首次传入的 state 只有 question，例如：{"question": "我想退钱"}。
# 图运行后 result 还会多出 route、answer 和两条 trace。
result = support_graph.invoke({"question": question})
print(f"123{result}")
trace_report = {
    "question": result["question"],
    "route": result["route"],
    "final_answer": result["answer"],
    "trace": result["trace"],
}

with TRACE_PATH.open("w", encoding="utf-8") as trace_file:
    json.dump(trace_report, trace_file, ensure_ascii=False, indent=2)

print(f"\n最终回答：{result['answer']}")
print("\n本次处理轨迹：")
for item in result["trace"]:
    print(f"- {item['node']}：{item['decision']}")
print(f"\n完整轨迹已写入：{TRACE_PATH}")
