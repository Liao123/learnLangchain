# 多 Agent 第 8 课：限制多 Agent 循环

## 这节课学什么

用 `config={"recursion_limit": 4}` 防止图无限循环。

## 解决什么问题

多 Agent 经常有这种路线：

```text
总调度 -> 专员 -> 总调度
```

如果总调度漏写结束条件，专员就会被不断重新委派，持续消耗模型调用次数和费用。

本课故意写了一个没有 `END` 的错误流程：

```text
supervisor -> specialist -> supervisor -> specialist -> ...
```

## 运行

```powershell
py .\MultiAgentDemo\08_限制多Agent循环\demo.py
```

## 观察结果

```text
第 1 次：总调度交给专员。
专员处理完后，又回到总调度。
第 2 次：总调度交给专员。
专员处理完后，又回到总调度。

已停止：多 Agent 循环达到 recursion_limit=4，但仍没有走到 END。
```

## 本课只记一句话

```text
recursion_limit 不是正确结束条件的替代品；它是结束条件失效时的最后一道刹车。
```
