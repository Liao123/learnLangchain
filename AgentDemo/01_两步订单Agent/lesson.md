# 第 60 课：两步订单 Agent

## 这节只记一句

Agent 不是只调用一次工具；它会看工具结果，再决定下一步要不要继续调用工具。

```text
用户问 A1001 的状态和取餐号
-> Agent 先查订单状态
-> 看到“制作中”
-> Agent 再查取餐号
-> 最后回答用户
```

## 直接做

### 1. 设置 Key 后运行

```powershell
$env:DEEPSEEK_API_KEY="你的Key"
py .\AgentDemo\01_两步订单Agent\demo.py
```

### 2. 看终端里的轮次

应该依次看到：

```text
第 1 轮：Agent 请求 get_order_status
第 2 轮：Agent 请求 get_pickup_number
Agent 最终答复：...
```

这两轮不是人提前写死的调用顺序；人只规定可用工具和规则，Agent 根据上一轮工具结果决定下一步。



第 1 次：
系统提示词要求“先查订单状态”
→ AI 调用 get_order_status
→ 工具结果追加进 messages：状态是“制作中”

第 2 次：
系统提示词里还有规则：
“收到状态是制作中后，才调用 get_pickup_number”
→ AI 现在终于看到了“制作中”这个工具结果
→ 调用 get_pickup_number
→ 工具结果追加进 messages：取餐号是 18

第 3 次：
AI 已经有状态和取餐号两个需要的资料
系统提示词要求“拿到需要的工具结果后，用简短中文回答”
→ AI 返回文字答案，不再返回 tool_calls
→ `if not response.tool_calls:` 成立，`break` 退出循环