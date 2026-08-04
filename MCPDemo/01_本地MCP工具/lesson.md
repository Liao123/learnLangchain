# MCP 第 1 课：本地 MCP 工具

## 这课学什么

让一个独立的 MCP 服务端公开订单查询工具，再让客户端通过 MCP 协议读取并调用它。

## 解决什么问题

以前的 `@tool` 函数只能直接写在当前 Agent 项目里。MCP 让工具放在独立服务中，任何支持 MCP 的客户端都能按同一协议连接它。

## 这课有两个程序

`server.py`：订单服务端。它公开 `get_order_status(order_id)`。

`demo.py`：客户端。它自动启动服务端、获取工具、调用工具。

## 你现在要做的

只运行客户端：

```powershell
py .\MCPDemo\01_本地MCP工具\demo.py
```

你不需要单独运行 `server.py`。

## 你要观察什么

终端大致会显示：

```text
客户端拿到的工具：['get_order_status']
调用 get_order_status 后的结果：...
```

再打开 `输出\mcp_result.json`，看客户端实际拿到的工具名、调用参数和结果。

## 一句话理解

`server.py` 像一个单独开店的工具提供方。

`demo.py` 像来接工具的客户端。

MCP 规定了它们如何通信，所以后面可以把这个工具交给 LangChain Agent、Claude Desktop 或其他 MCP 客户端使用。

本课不调用 DeepSeek，也不需要 API Key。
