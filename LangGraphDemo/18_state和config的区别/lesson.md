# LangGraph 第 18 课：state 和 config 的区别

## 这节课学什么

区分两类数据：

```text
state：流程正在处理、节点会读写的数据。
config：这一次运行时传入的外部配置。
```

## 解决什么问题

订单号、金额是订单流程数据，适合放在 state。

当前用户是谁、属于哪个租户、当前 thread_id 等运行条件，通常从 config 传入，不需要自动成为流程 state 的字段。

## 运行

```powershell
py .\LangGraphDemo\18_state和config的区别\demo.py
```

## 观察结果

```text
节点收到的 state：{'order_id': 'A1001', 'amount': 28.0}
节点从 config 读到：小王 金卡

最终 state：{
  'order_id': 'A1001',
  'amount': 28.0,
  'reply': '小王，你的 金卡会员订单金额是 28.0 元。'
}
```

注意：最终 state 没有自动出现 `customer_name` 和 `membership`。

## 本课只记一句话

```text
state 是流程内的业务数据；config 是这次调用给流程的外部参数。
```
