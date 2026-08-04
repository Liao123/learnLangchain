# Agent Harness 第 6 课：比较两次评测结果

## 这课学什么

把批准过的基准报告和新版本报告放在一起，找出成功率变化和具体回归题。

## 什么叫回归

同一道题以前通过，现在失败，才叫回归。

例如：`route-refund-002` 在 `router-v1` 通过，在 `router-v2` 失败。

## 你现在要做的

先运行正常比较：

```powershell
py .\AgentHarnessDemo\06_比较两次评测结果\demo.py
```

你会看到：

```text
基准版本：router-v1，成功率 100%
新版本：router-v2，成功率 75%
发生回归的任务：
- route-refund-002
```

再运行题集变化示例：

```powershell
py .\AgentHarnessDemo\06_比较两次评测结果\demo.py changed_dataset
```

这次程序会拒绝比较，因为两个报告的题集哈希不同。

## 你要记住

先比较 `dataset_sha256`，相同才比较成绩。

再找“以前 `passed=true`、现在 `passed=false`”的任务。

一句话：回归不是分数低，而是相同题集上，旧版本会做、新版本做错的具体题。
