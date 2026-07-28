# 第 69 课：LangGraph 管理 Agent 循环

这节课学什么：用 LangGraph 把“模型 -> 工具 -> 模型”的手写循环画成状态图。

本课解决什么问题：工具、分支、重试越来越多时，全部写在一个 `for` 里会越来越难看懂、难修改。

场景：客服 Agent 先查订单状态；状态是制作中，再查取餐号；最后回答用户。

## 直接运行

1. 在 PowerShell 设置好 `DEEPSEEK_API_KEY`。
2. 运行：

```powershell
py .\AgentDemo\10_LangGraph管理Agent循环\demo.py
```

3. 看终端的执行过程，正常顺序是：

```text
用户 -> agent 请求查状态 -> tools 返回状态 -> agent 请求取餐号 -> tools 返回取餐号 -> agent 最终答复
```

## 本课只记一句话

```text
agent 节点：调用 AI
tools 节点：执行工具
条件边：AI 要工具就去 tools，不要工具就结束
```
