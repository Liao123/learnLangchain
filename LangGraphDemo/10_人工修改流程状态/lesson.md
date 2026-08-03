# LangGraph 第 10 课：人工修改流程状态

## 这节课学什么

学习 `graph.update_state(config, {"字段": "新值"})`：流程暂停后，人工直接修改已保存的 state。

## 解决什么问题

用户填写了错误地址，客服核对后发现问题。不能带着旧地址继续发货，要先修正 state，再恢复流程。

## 运行

```powershell
py .\LangGraphDemo\10_人工修改流程状态\demo.py
```

## 观察结果

```text
暂停时的 state：{'order_id': 'A1001', 'address': '北京市朝阳区 1 号'}
人工改地址后的 state：{'order_id': 'A1001', 'address': '上海市浦东新区 2 号'}
恢复后的发货单：发货单：订单 A1001，寄往 上海市浦东新区 2 号。
```

## 本课只记一句话

```text
update_state 只改当前 state 指定的字段；恢复后的节点会读取修改后的新值。
```
