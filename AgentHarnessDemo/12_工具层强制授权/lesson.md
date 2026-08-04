# Agent Harness 第 12 课：工具层强制授权

## 这课学什么

在退款工具内部再次检查服务器确认状态。模型即使错误请求了工具，也无法真的提交未确认退款。

## 和第 11 课的区别

第 11 课测试：模型会不会听系统提示词，不发出越权工具请求。

这一课假设最坏情况：模型已经发出了错误工具请求。重点是工具还会不会拒绝。

## 你现在要做的

在项目根目录运行：

```powershell
py .\AgentHarnessDemo\12_工具层强制授权\demo.py
```

打开 `输出\tool_authorization_report.json`。

## 你要重点看第二题

第二题故意强制执行了：

```python
submit_refund.invoke({"order_id": "A1001"})
```

但服务器状态是：

```python
server_confirmations["A1001"] = False
```

工具内部会走到：

```python
if not server_confirmations.get(order_id, False):
    return {"ok": False, "reason": "服务器未确认退款，拒绝执行。"}
```

所以退款状态仍是 `not_requested`。

## 你要记住

提示词是第一层提醒。

工具内部的服务器校验才是最后一层强制保护。

一句话：模型可以提出操作请求，但服务器才有权决定操作是否执行。
