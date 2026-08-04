# Agent Harness 第 1 课：任务与评测分离

## 这课学什么

认识 Harness 最小结构：任务、Agent 运行、评测，三者分开。

## 解决什么问题

“模型答错了”这句话太笼统。你需要留下：它做的是哪道题、实际怎么做、按什么标准判错。

## 什么场景会用

改提示词、换模型、换工具或改 LangGraph 流程后，都要用同一批任务重新测试。

## 你现在要做的

1. 在项目根目录运行：

   ```powershell
   py .\AgentHarnessDemo\01_任务与评测分离\demo.py
   ```

2. 打开本课的 `输出\run_record.json`。

## 你要看什么

```json
{
  "task": {
    "input": {"question": "我想退钱"},
    "expected": {"route": "refund"}
  },
  "agent_output": {"route": "refund"},
  "evaluation": {"passed": true}
}
```

`task` 是人出的题和标准答案。

`agent_output` 是 Agent 实际做出的选择。

`evaluation` 是独立比较后的结果。

这课故意没有再写 LangGraph：Harness 包在 Agent 外面，里面可以是普通函数，也可以换成完整 LangGraph 图。

一句话：Harness 不是另一个 AI，而是把“出题、运行、判分、留记录”固定下来的工程外壳。
