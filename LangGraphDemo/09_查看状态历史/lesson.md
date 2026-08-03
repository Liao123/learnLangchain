# LangGraph 第 9 课：查看状态历史

## 这节课学什么

学习 `graph.get_state_history(config)`：把同一个 `thread_id` 保存过的每次 state 快照取出来。

## 解决什么问题

流程最后只剩“已完成”，但开发者想知道它之前经历了什么，就查看历史快照。

常见场景：排查订单流程走错、查看某一步改了哪个字段、审计流程经过了哪些状态。

## 运行

```powershell
py .\LangGraphDemo\09_查看状态历史\demo.py
```

## 观察结果

程序会依次显示类似内容：

```text
最后状态： {'order_id': 'A1001', 'status': '已完成', 'reply': '订单 A1001 已完成。'}

第 1 个快照：values = {}，next = ('__start__',)
第 2 个快照：values = {'order_id': 'A1001'}，next = ('create_order',)
第 3 个快照：values = {'order_id': 'A1001', 'status': '待支付'}，next = ('pay_order',)
第 4 个快照：values = {'order_id': 'A1001', 'status': '已支付'}，next = ('finish_order',)
第 5 个快照：values = {'order_id': 'A1001', 'status': '已完成', 'reply': '订单 A1001 已完成。'}，next = ()
```

实际快照数量可能比示例多，因为 LangGraph 还会保存开始节点和结束节点的内部记录；重点看 `values` 里的状态变化。

## 本课只记一句话

```text
get_state(config) 看当前这一刻；get_state_history(config) 看一路走过的所有快照。
```
