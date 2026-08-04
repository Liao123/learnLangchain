# Agent Harness 第 9 课：验证工具操作结果

## 这课学什么

测试 Agent 是否真的正确调用工具，以及工具调用后业务数据是否真的变成预期状态。

## 解决什么问题

Agent 说“退款已提交”不代表退款真的提交了。回答文字正确、工具没调用，仍然是业务失败。

## 你现在要做的

在项目根目录运行：

```powershell
py .\AgentHarnessDemo\09_验证工具操作结果\demo.py
```

打开 `输出\tool_evaluation_report.json`。

## 你要观察什么

第一题确认退款后，报告应同时有：

```json
{
  "actual_refund_status": "submitted",
  "actual_tool_name": "submit_refund",
  "passed": true
}
```

第二题没有确认时，应同时有：

```json
{
  "actual_refund_status": "not_requested",
  "actual_tool_name": null,
  "passed": true
}
```

## 你要记住

开放回答用模型评审。

订单状态、是否调用工具、金额等确定事实，用代码直接检查。

本课用的是内存里的假订单系统，测试不会产生真实退款。

一句话：测试会操作业务系统的 Agent，必须检查副作用，不能只看它说了什么。
