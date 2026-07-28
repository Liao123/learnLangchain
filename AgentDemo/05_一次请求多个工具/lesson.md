# 第 64 课：一次请求多个工具

这节课学什么：AI 一次模型回复里，可能同时请求多个互不依赖的工具。

本课解决什么问题：用户同时问订单状态和会员积分时，不能只把其中一个工具结果交回给 AI。

场景：用户问“订单 A1001 的状态，以及会员 M1001 的积分”。

## 直接运行

1. 在 PowerShell 设置好 `DEEPSEEK_API_KEY`。
2. 运行：

```powershell
py .\AgentDemo\05_一次请求多个工具\demo.py
```

3. 正常情况下，第 1 轮会看到两个工具请求：

```text
get_order_status
get_member_points
```

第 2 轮才会得到最终答复。

## 本课只记一句话

`response.tool_calls` 是一个列表。AI 要了几个工具，Python 就要执行几个，并为每一个工具结果追加对应的 `ToolMessage`。
