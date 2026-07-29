# LangGraph 第 2 课：会话记忆

这节课学什么：用 LangGraph 的 `MemorySaver` 保存同一会话的 `messages`。

本课解决什么问题：第二轮用户只说“那取餐号呢”，如果没有前一轮历史，AI 不知道“那”指哪张订单。

场景：用户先问订单 `A1001` 的状态，随后追问取餐号。

## 直接运行

1. 在 PowerShell 设置好 `DEEPSEEK_API_KEY`。
2. 运行：

```powershell
py .\LangGraphDemo\02_会话记忆\demo.py
```

3. 看两轮输出：第二轮问题里没有 `A1001`，但 Agent 仍会查到取餐号 `18`。

## 本课只记一句话

```text
同一个 thread_id = 同一个会话历史
换一个 thread_id = 新会话，没有旧历史
```

本课的 `MemorySaver` 只保存在当前 Python 进程内；程序关闭后记忆就没了。
