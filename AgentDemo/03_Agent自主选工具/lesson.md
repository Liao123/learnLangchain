# 第 62 课：Agent 自主选工具

这节课学什么：一个 Agent 有多个工具时，AI 根据用户的问题和工具说明，决定调用哪一个。

本课解决什么问题：不需要先写 `if "积分" in question`、`if "营业" in question` 来分流用户问题。

场景：同一个客服 Agent 同时能查订单、查会员积分、查门店营业时间。

## 直接运行

1. 在 PowerShell 设置好 `DEEPSEEK_API_KEY`。
2. 运行：

```powershell
py .\AgentDemo\03_Agent自主选工具\demo.py
```

3. 看输出第一行：本题会请求 `get_member_points`，因为用户问的是会员积分。

## 自己换一题

把 `question` 改成下面任意一句后重新运行：

```python
question = "订单 A1001 现在什么状态？"
question = "门店今晚几点打烊？"
```

分别观察 Agent 是否改为请求 `get_order_status` 或 `get_store_hours`。

## 如果出现连接错误

看到 `SSL`、`APIConnectionError` 一类错误时，表示 Python 连 DeepSeek 的网络连接中断了，不是工具选择代码出错。程序会自动重试 3 次；仍失败就直接重新运行一次。
