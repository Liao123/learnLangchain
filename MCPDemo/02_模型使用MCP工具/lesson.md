# 第 2 课：模型使用 MCP 工具

## 这节课学什么

上一课是 Python 自己指定调用 `get_order_status`。

这一课变成：模型先拿到 MCP 服务提供的两个工具，然后根据问题自己决定调用订单工具还是退款工具。

## 解决什么问题

客服 Agent 不能只会聊天，它需要查真实业务数据。

而订单、退款等能力通常由不同系统提供。MCP 让这些系统把能力做成统一的“工具”，Agent 不需要把业务代码写进自己文件里。

## 先运行

在项目根目录运行：

```powershell
py .\MCPDemo\02_模型使用MCP工具\demo.py
```

第一次输入：

```text
订单 A1001 到哪里了？
```

你会看到大致过程：

```text
MCP 服务提供的工具：['get_order_status', 'get_refund_status']
第 1 轮：模型请求调用 get_order_status，参数是 {'order_id': 'A1001'}
工具返回：{"found": true, "order_id": "A1001", "status": "配送中", ...}
第 2 轮：模型直接给出最终回答。
最终回答：订单 A1001 正在配送中，预计今天送达。
```

再重新运行一次，输入：

```text
退款单 R2001 什么时候到账？
```

这次应当看到模型请求的是 `get_refund_status`。

## 一句话流程

`server.py` 公开工具 -> `demo.py` 拿到工具 -> 模型选工具 -> Python 调 MCP 工具 -> 工具结果回给模型 -> 模型回答用户。

## 最关键的三行

```python
tools = await client.get_tools()
model_with_tools = model.bind_tools(tools)
response = await model_with_tools.ainvoke(messages)
```

第一行拿到 MCP 服务的工具；第二行让模型知道有哪些工具；第三行才让模型看用户问题并决定要不要请求工具。

## 和之前 `@tool` 的区别

之前的 `@tool`：工具函数写在当前 Agent 的 Python 文件里。

这次的 `@mcp.tool()`：工具函数在独立的 `server.py` 进程里。Agent 只能通过 MCP 协议请求它，像请求一个外部业务服务。

## 看结果文件

运行后打开：`输出/agent_mcp_result.json`。

里面能看到用户问题、模型实际请求的工具名和参数、工具结果、最终回答。
