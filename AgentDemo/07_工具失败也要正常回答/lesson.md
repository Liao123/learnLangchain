# 第 66 课：工具失败也要正常回答

这节课学什么：订单不存在这类“业务失败”，要作为工具结果交给 AI，而不是让 Python 抛异常终止程序。

本课解决什么问题：用户问不存在的订单时，Agent 既不能崩溃，也不能编造订单状态。

场景：用户查询订单 `A9999`，但订单库里只有 `A1001`。

## 直接运行

1. 在 PowerShell 设置好 `DEEPSEEK_API_KEY`。
2. 运行：

```powershell
py .\AgentDemo\07_工具失败也要正常回答\demo.py
```

3. 看输出：工具会返回 `success: false` 和 `ORDER_NOT_FOUND`；下一轮 AI 会据此告诉用户订单不存在。

## 本课只记一句话

预料中的业务失败，返回结构化结果：

```json
{"success": false, "data": null, "error": {"code": "ORDER_NOT_FOUND"}}
```

只有网络断开、代码写错这类真正的异常，才需要 `try / except`。
