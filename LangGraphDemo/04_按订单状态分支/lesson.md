# LangGraph 第 4 课：按订单状态分支

这节课学什么：图可以根据共享状态里的值，走不同的节点路线。

本课解决什么问题：不是所有订单都能取消。`待制作` 订单走“取消”路线，`制作中` 订单走“拒绝”路线。

## 直接运行

```powershell
py .\LangGraphDemo\04_按订单状态分支\demo.py
```

观察两次结果：

```text
A1001（待制作）-> cancel_order -> 已取消
A1002（制作中）-> reject_cancellation -> 不能取消
```

## 本课只记一句话

```text
节点负责更新 state。
条件边读取 state，决定下一步去哪个节点。
```
