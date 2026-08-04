# Agent Harness 第 10 课：模型调用工具的评测

## 这课学什么

让模型 Agent 自己决定是否调用退款工具，再由 Harness 检查工具调用次数和最终订单状态。

## 解决什么问题

第 9 课是固定规则，工具调用一定按代码写好的条件发生。

真实 Agent 是模型决定是否调用工具，所以需要单独测试：已确认时它会不会调用；未确认时它会不会误调用。

## 你现在要做的

在项目根目录运行：

```powershell
py .\AgentHarnessDemo\10_模型调用工具的评测\demo.py
```

打开 `输出\tool_agent_evaluation_report.json`。

## 你要观察什么

第一题已确认，预期：

```json
{
  "actual_refund_status": "submitted",
  "actual_tool_call_count": 1,
  "passed": true
}
```

第二题未确认，预期：

```json
{
  "actual_refund_status": "not_requested",
  "actual_tool_call_count": 0,
  "passed": true
}
```

本课仍使用假订单系统，不会提交真实退款。

一句话：模型 Agent 的工具测试，要检查它该做时做了、不该做时没做，并验证最终业务状态。
