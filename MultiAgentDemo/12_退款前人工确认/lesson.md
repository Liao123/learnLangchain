# 多 Agent 第 12 课：退款前人工确认

## 这节课学什么

退款子图中也可以 `interrupt()` 暂停。人工确认后，子图再用 `Command.PARENT` 回到父图统一回复。

## 解决什么问题

退款是有风险的真实操作。模型或专员可以准备退款，但不能自动执行；必须暂停等待人工确认。

```text
父图 router
  -> 退款子图 refund_agent
  -> interrupt 暂停，写入 SQLite
  -> 人工输入“确认”
  -> 退款子图继续
  -> Command.PARENT 回父图 final_reply
  -> END
```

## 第一步：启动并暂停

```powershell
py .\MultiAgentDemo\12_退款前人工确认\demo.py start
```

观察：退款子图已经暂停，`输出\checkpoints.sqlite` 保存了当前状态。

## 第二步：恢复并确认

```powershell
py .\MultiAgentDemo\12_退款前人工确认\demo.py resume 确认
```

观察：

```text
客服回复：订单 A1001 已提交 28.0 元退款。
```

也可以输入别的内容：

```powershell
py .\MultiAgentDemo\12_退款前人工确认\demo.py resume 取消
```

这时退款不会提交。

## 本课只记一句话

```text
高风险专员可以在子图里暂停等人工；恢复后仍能带着子图结果回父图继续流程。
```
