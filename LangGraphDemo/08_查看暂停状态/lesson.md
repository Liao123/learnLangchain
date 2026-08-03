# LangGraph 第 8 课：查看暂停状态

这节课学什么：不直接查 SQLite 表，而是用 `graph.get_state(config)` 查看当前流程状态。

本课解决什么问题：流程暂停后，开发者需要知道它已经收到了什么数据、下一步会运行哪个节点。

## 直接运行

```powershell
py .\LangGraphDemo\08_查看暂停状态\demo.py
```

观察两次状态：

```text
暂停时：state 只有 order_id，下一步是 ask_for_confirmation
恢复后：state 多出 confirmation 和 final_reply，下一步为空
```

## 本课只记一句话

```text
graph.get_state(config).values：当前 state 的值
graph.get_state(config).next：图接下来要运行的节点
```
