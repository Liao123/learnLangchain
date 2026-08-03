# 多 Agent 第 7 课：校验交接单

## 这节课学什么

模型的 JSON 不能直接当业务数据使用。先用 `Handoff.model_validate(...)` 检查，合格后才交给专员。

## 解决什么问题

提示词虽然要求模型返回：

```json
{"route": "order", "record_id": "A1001", "task": "查询订单状态"}
```

但模型仍可能输出错误 route、漏掉 task、漏掉单号，或者根本不是合法 JSON。

本课要求：

```text
route 只能是 order / refund / human
task 必须是文字
order、refund 路线必须带 record_id
```

任意一项不合格，都转人工客服，不让坏数据进入业务专员。

## 运行

```powershell
py .\MultiAgentDemo\07_校验交接单\demo.py
```

输入：

```text
订单 A1001 到哪里了？
```

观察类似输出：

```text
通过 Python 校验的交接单：{'route': 'order', 'record_id': 'A1001', 'task': '查询订单状态'}
最终回答：订单专员：订单 A1001 当前配送中。
```

## 本课只记一句话

```text
提示词负责要求格式；Pydantic 校验负责在 Python 里真正拦住不合格的模型输出。
```
