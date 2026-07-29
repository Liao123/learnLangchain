# LangGraph 第 5 课：实时查看图执行

这节课学什么：用 `graph.stream()` 在每个节点完成时，立刻看到图的执行过程。

本课解决什么问题：`graph.invoke()` 只在整张图结束后给最终 state；排查分支走错时，看不到中间经过哪些节点。

## 直接运行

```powershell
py .\LangGraphDemo\05_实时查看图执行\demo.py
```

观察输出：

```text
A1001：check_order -> cancel_order
A1002：check_order -> reject_cancellation
```

## 本课只记一句话

```text
invoke：等图全部结束，拿最终 state
stream：每个节点完成就立刻拿到一次更新
```
