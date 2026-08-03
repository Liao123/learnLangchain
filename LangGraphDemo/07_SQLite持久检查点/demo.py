import sys
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


#total=False 表示值为动态增加   TypedDict 意思 这是一个 类的type 数据格式声明类
class CancelState(TypedDict, total=False):
    order_id: str
    confirmation: str
    final_reply: str


orders = {
    "A1001": {"状态": "待制作"},
}

LESSON_DIR = Path(__file__).resolve().parent #...\07_SQLite持久检查点 当前文件demo的绝对路径的父目录
DATABASE_PATH = LESSON_DIR / "输出" / "checkpoints.sqlite" #...\07_SQLite持久检查点\输出\checkpoints.sqlite
THREAD_ID = "cancel-A1001"


def ask_for_confirmation(state: CancelState) -> dict:
    confirmation = interrupt( #让 LangGraph 让工作流暂停不往下走 退出函数，并把控制权交还给外部程序  此时confirmation 的值是暂定的 要后续 恢复的值 Command(resume=confirmation)  confirmation 才是传给下一个的值
        {
            "类型": "取消订单确认",
            "订单号": state["order_id"],
            "问题": f"确定取消订单 {state['order_id']} 吗？",
        }
    )
    return {"confirmation": confirmation} #在这个终端 Demo 里，暂停后代码执行了 return，所以当前 Python 程序就退出了。


def cancel_order(state: CancelState) -> dict:
    if state["confirmation"] != "确认":
        return {"final_reply": "未收到“确认”，订单没有取消。"}

    orders[state["order_id"]]["状态"] = "已取消"
    return {"final_reply": f"订单 {state['order_id']} 已取消。"}


def build_graph(checkpointer: SqliteSaver):
    #传进去的 是 全节点共享的 变量 add_node 
    #每个节点拿到：当前完整 shared state 入参
    #每个节点返回：自己这一步新增或修改的字段 出参数
    #LangGraph：把返回值合并进 shared state 合并入参出参
    #下一个节点：拿到合并后的完整 state 合并后的参数
    workflow = StateGraph(CancelState) 

    workflow.add_node("ask_for_confirmation", ask_for_confirmation)
    workflow.add_node("cancel_order", cancel_order)
    workflow.add_edge(START, "ask_for_confirmation")
    workflow.add_edge("ask_for_confirmation", "cancel_order")
    workflow.add_edge("cancel_order", END)
    return workflow.compile(checkpointer=checkpointer)
    #发消息自动存档sqllite 和 interrupt 可以理解为存档触发信号
    #interrupt：
    #保存“我暂停在哪里，等什么输入”

    #节点 return：
    #保存“这个节点刚刚更新了哪些 state 字段”


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) >= 2 else ""  #获取启动命令  如果参数大于2 就取坐标1 否则默认 ""
    confirmation = sys.argv[2] if len(sys.argv) >= 3 else "" # 获取启动命令 参数大于3 就取坐标2 否则默认 ""
    #如果2个字符串都不能匹配到 就打印
    if mode not in {"start", "resume"}:
        print("用法：py demo.py start")
        print("或：py demo.py resume 确认")
        return
    # 绝对路径 输出文件夹 创建文件  exist_ok=True #如果“输出”文件夹已经存在，也算正常，不报错。
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    config = {"configurable": {"thread_id": THREAD_ID}} #LangGraph 默认存档属性名
    #str 把路径变量转成字符串   from_conn_string 数据库链接参数 数据库连接字符串
    with SqliteSaver.from_conn_string(str(DATABASE_PATH)) as checkpointer:  # with：打开资源，结束时自动关闭 with 理解成前端的 try/finally。 as checkpointer：给打开后的资源取变量名
        checkpointer.setup() # etup() 初始化数据库 会自动创建例如表格、索引等数据库结构，如果已经存在则不会重复创建。
        cancel_graph = build_graph(checkpointer) #使用自定义方法build_graph 创建一张“取消订单流程图”，并让它使用当前打开的 SQLite 存档库。

        if mode == "start":
            result = cancel_graph.invoke({"order_id": "A1001"}, config=config)
            if "__interrupt__" in result:
                print("流程已暂停，确认点已写入 SQLite。")
                print("现在可以运行：py demo.py resume 确认")
            return

        if not DATABASE_PATH.exists():
            print("还没有 SQLite 记录，请先运行：py demo.py start")
            return

        final_state = cancel_graph.invoke(Command(resume=confirmation), config=config)
        print(final_state["final_reply"])
        print("本进程中的订单状态：", orders["A1001"]["状态"])

#如果是本地运行
if __name__ == "__main__":
    main() #入口
