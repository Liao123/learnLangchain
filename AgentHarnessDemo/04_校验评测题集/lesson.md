# Agent Harness 第 4 课：校验评测题集

## 这课学什么

在调用模型前，先检查人写的评测题 JSON 是否符合固定格式。

## 解决什么问题

如果人工把退款题的标准答案误写成 `payment`，直接评测得到的分数是假的，还会浪费模型调用费用。

## 你现在要做的

先运行正常题集：

```powershell
py .\AgentHarnessDemo\04_校验评测题集\demo.py
```

你会看到：

```text
题集校验通过：客服路由基础题集 v1
题目数量：2
```

再运行故意写错的题集：

```powershell
py .\AgentHarnessDemo\04_校验评测题集\demo.py invalid
```

你会看到 `expected.route` 的值不合法。注意：这次不会调用 DeepSeek。

## 你要记住

`RoutingDataset.model_validate(raw_dataset)` 的作用是：检查 JSON 是否符合你定义的题集格式。

合格，才能进入批量评测；不合格，立即停止。

一句话：先校验题目，再测 Agent，避免拿错误标准答案评判 AI。
