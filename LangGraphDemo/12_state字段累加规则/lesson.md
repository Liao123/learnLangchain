# LangGraph 第 12 课：state 字段累加规则

## 这节课学什么

学习给 state 某个字段规定“怎么合并”。

## 解决什么问题

两个节点都写 `steps`：

```text
第一个节点：['已校验地址']
第二个节点：['已检查库存']
```

默认情况下，后一个值会覆盖前一个值，只剩 `['已检查库存']`。

本课用 `Annotated[list[str], add]` 规定：`steps` 要用列表相加的方式合并。

## 运行

```powershell
py .\LangGraphDemo\12_state字段累加规则\demo.py
```

## 观察结果

```text
最终 state：{'order_id': 'A1001', 'steps': ['已校验地址', '已检查库存']}
```

## 本课只记一句话

```text
Annotated[list[str], add] 的意思是：这个列表字段每次收到新列表时，不覆盖，而是往后追加。
```
