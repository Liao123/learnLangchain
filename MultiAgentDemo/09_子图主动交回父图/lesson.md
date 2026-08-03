# 多 Agent 第 9 课：子图主动交回父图

## 这节课学什么

子图内部可以用：

```python
Command(goto="父图节点名", graph=Command.PARENT)
```

主动把控制权交回父图指定节点。

## 解决什么问题

普通子图结束后，父图通常按固定边继续。

但退款专员处理完后，可能要交回父图统一包装最终回复、记录审计日志、再做人工确认。子图需要明确说“现在回父图的哪个节点”。

```text
父图 router
  -> 退款子图 refund_agent
  -> Command.PARENT
  -> 父图 final_reply
  -> END
```

## 运行

```powershell
py .\MultiAgentDemo\09_子图主动交回父图\demo.py
```

## 观察结果

```text
父图总调度：进入退款子图。
退款子图：处理退款问题。
父图：收到退款子图交回的结果，生成最终回复。

最终回答：客服回复：退款申请已提交，预计 1 到 3 个工作日原路退回。
```

## 本课只记一句话

```text
graph=Command.PARENT 表示 goto 的目标节点在父图里，不在当前子图里。
```
