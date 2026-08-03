# LangGraph 第 15 课：节点自己决定下一步

## 这节课学什么

学习 `Command(update=..., goto=...)`：一个节点同时更新 state，并直接指定下一个节点。

## 解决什么问题

库存检查后，流程要根据结果分支：

```text
库存充足 -> create_order
库存不足 -> reject_order
```

以前可以在图外写 `add_conditional_edges`。这节课把“更新检查结果”和“选择下一步”放进 `check_stock` 节点的一次返回中。

## 运行

```powershell
py .\LangGraphDemo\15_节点自己决定下一步\demo.py
```

## 观察结果

```text
A1001：库存充足，去 create_order。
最终回答：订单 A1001 已创建。

A1002：库存不足，去 reject_order。
最终回答：订单 A1002 库存不足，无法创建。
```

## 本课只记一句话

```text
Command(update=数据, goto="节点名") 的意思是：更新 state 后，直接去指定节点。
```
Command(goto)：从固定节点中动态选路线。
Send：根据数据动态创建固定节点的多次任务。
add_conditional_edges：
把“判断下一步”的代码写在节点外面的路由函数里